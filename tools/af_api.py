#!/usr/bin/env python3
"""Find, export and import AutoFlow flows through the AutoFlow Flow API, signed in as you.

Business Central API pages under /api/mse365/autoflow/v1.0 (see the README for the AutoFlow version):
flows (list), flowVersions (export JSON in "definition") and flowImports (import as a draft).
The API never publishes: review an imported draft in the flow editor and publish it there.

Usage:
    python3 tools/af_api.py login                      # sign in once (device code)
    python3 tools/af_api.py companies                  # list companies, to find AF_COMPANY
    python3 tools/af_api.py list [--filter "<OData>"]  # e.g. --filter "startswith(code,'ACME.')"
    python3 tools/af_api.py export <code-or-no> [--published] [-o flow.json]
    python3 tools/af_api.py import flow.json
    python3 tools/af_api.py logout                     # forget the cached sign-in

Configuration (environment variables):
    AF_ENVIRONMENT   Business Central environment name, e.g. Production or Sandbox (online)
    AF_COMPANY       Company name or id
    AF_TENANT        Optional: tenant id or domain (default: the one you sign in to)
    AF_TOKEN         Optional: an access token to use as is (e.g. from the Azure CLI)
    AF_CLIENT_ID     Optional: public client app id to sign in with (default: Microsoft's
                     first-party Azure PowerShell client, which needs no app registration)
    AF_BASE_URL      On-premises only: the API root, e.g. https://bc.example.com:7048/BC/api
    AF_USERNAME / AF_PASSWORD   On-premises only: basic authentication instead of sign-in

Sign-in is delegated: every call runs with your own Business Central user and AutoFlow
role (mse365 AF ALL is enough). The cached sign-in lives in ~/.cache/autoflow-api/token.json,
readable only by you, until it expires or you run "logout".

Standard library only. Exit code: 0 = ok, 1 = API error, 2 = bad input or configuration.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CLIENT_ID = "1950a258-227b-4e31-a9cf-717495945fc2"  # Microsoft Azure PowerShell (public client)
BC_SCOPE = "https://api.businesscentral.dynamics.com/.default offline_access"
BC_API_HOST = "https://api.businesscentral.dynamics.com/v2.0"
API_PATH = "mse365/autoflow/v1.0"
CACHE_FILE = Path.home() / ".cache" / "autoflow-api" / "token.json"


class ApiError(Exception):
    pass


class ConfigError(Exception):
    pass


# ── sign-in ──────────────────────────────────────────────────────────────────

def authority() -> str:
    return "https://login.microsoftonline.com/" + (os.environ.get("AF_TENANT") or "organizations")


def client_id() -> str:
    return os.environ.get("AF_CLIENT_ID") or DEFAULT_CLIENT_ID


def post_form(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        try:
            return json.load(err)
        except ValueError:
            raise ApiError(f"{url}: HTTP {err.code}") from None


def save_token(token: dict) -> None:
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 3600)) - 60
    token["client_id"] = client_id()
    token["authority"] = authority()
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.touch(mode=0o600, exist_ok=True)
    os.chmod(CACHE_FILE, stat.S_IRUSR | stat.S_IWUSR)
    CACHE_FILE.write_text(json.dumps(token))


def load_token() -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        token = json.loads(CACHE_FILE.read_text())
    except ValueError:
        return None
    if token.get("client_id") != client_id() or token.get("authority") != authority():
        return None
    return token


def login() -> None:
    code = post_form(f"{authority()}/oauth2/v2.0/devicecode", {"client_id": client_id(), "scope": BC_SCOPE})
    if "device_code" not in code:
        raise ApiError(code.get("error_description") or json.dumps(code))
    print(code["message"], file=sys.stderr, flush=True)
    interval = int(code.get("interval", 5))
    deadline = time.time() + int(code.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        token = post_form(f"{authority()}/oauth2/v2.0/token", {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id(),
            "device_code": code["device_code"],
        })
        if "access_token" in token:
            save_token(token)
            print("Signed in.", file=sys.stderr)
            return
        error = token.get("error")
        if error == "slow_down":
            interval += 5
        elif error != "authorization_pending":
            raise ApiError(token.get("error_description") or error or json.dumps(token))
    raise ApiError("The sign-in code expired. Run login again.")


def access_token() -> str:
    if os.environ.get("AF_TOKEN"):
        return os.environ["AF_TOKEN"]
    token = load_token()
    if token is None:
        raise ConfigError("Not signed in. Run: python3 tools/af_api.py login")
    if token.get("expires_at", 0) > time.time():
        return token["access_token"]
    refreshed = post_form(f"{authority()}/oauth2/v2.0/token", {
        "grant_type": "refresh_token",
        "client_id": client_id(),
        "refresh_token": token.get("refresh_token", ""),
        "scope": BC_SCOPE,
    })
    if "access_token" not in refreshed:
        raise ConfigError("The sign-in has expired. Run: python3 tools/af_api.py login")
    save_token(refreshed)
    return refreshed["access_token"]


def auth_header() -> str:
    if os.environ.get("AF_USERNAME"):
        pair = f"{os.environ['AF_USERNAME']}:{os.environ.get('AF_PASSWORD', '')}"
        return "Basic " + base64.b64encode(pair.encode()).decode()
    return "Bearer " + access_token()


# ── API ──────────────────────────────────────────────────────────────────────

def api_root() -> str:
    if os.environ.get("AF_BASE_URL"):
        return os.environ["AF_BASE_URL"].rstrip("/")
    env = os.environ.get("AF_ENVIRONMENT")
    if not env:
        raise ConfigError("Set AF_ENVIRONMENT to your Business Central environment name (e.g. Production).")
    tenant = os.environ.get("AF_TENANT")
    return f"{BC_API_HOST}/{tenant}/{env}/api" if tenant else f"{BC_API_HOST}/{env}/api"


def call(method: str, url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    # Only reads are retried after a dropped connection: an import that reached the server
    # may have created a draft already, and repeating it would create a second one.
    attempts = 3 if method == "GET" else 1
    for attempt in range(1, attempts + 1):
        try:
            return send(req)
        except urllib.error.URLError as err:  # HTTP errors are already ApiError here
            if attempt == attempts:
                raise ApiError(f"Cannot reach {urllib.parse.urlsplit(url).netloc}: {err.reason}") from None
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def send(req: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        raw = err.read().decode(errors="replace")
        try:
            message = json.loads(raw)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = raw or err.reason
        if err.code == 401:
            message += " (signed in to the right tenant? Run login again.)"
        elif err.code == 403:
            message += " (your user needs the AutoFlow permission set mse365 AF ALL in this company.)"
        raise ApiError(f"HTTP {err.code}: {message}") from None


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def company_url() -> str:
    company = os.environ.get("AF_COMPANY")
    if not company:
        raise ConfigError("Set AF_COMPANY to the company name or id (see: af_api.py companies).")
    if len(company) == 36 and company.count("-") == 4:
        company_id = company
    else:
        query = urllib.parse.quote(f"name eq {quote(company)}")
        found = call("GET", f"{api_root()}/{API_PATH}/companies?$filter={query}")["value"]
        if not found:
            raise ConfigError(f"No company named {company!r}. See: af_api.py companies")
        company_id = found[0]["id"]
    return f"{api_root()}/{API_PATH}/companies({company_id})"


FLOW_FIELDS = "id,number,code,description,status,isSubFlow,triggerType,folderPath,publishedVersionId,publishedVersion,draftVersionId,draftVersion,lastModifiedDateTime"


def find_flow(key: str) -> dict:
    # A flow number has at most 20 characters; filtering on a longer one is an error, not a miss.
    fields = ("code", "number") if len(key) <= 20 else ("code",)
    for field in fields:
        query = urllib.parse.quote(f"{field} eq {quote(key.upper())}")
        found = call("GET", f"{company_url()}/flows?$filter={query}&$select={FLOW_FIELDS}")["value"]
        if found:
            return found[0]
    raise ApiError(f"No flow with the code or number {key!r}.")


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_companies(_args) -> None:
    for company in call("GET", f"{api_root()}/{API_PATH}/companies")["value"]:
        print(f"{company['id']}  {company['name']}")


def cmd_list(args) -> None:
    url = f"{company_url()}/flows?$select={FLOW_FIELDS}"
    if args.filter:
        url += "&$filter=" + urllib.parse.quote(args.filter)
    flows = call("GET", url)["value"]
    if args.json:
        print(json.dumps(flows, indent=2))
        return
    for flow in flows:
        versions = f"published {flow['publishedVersion'] or '-'}"
        if flow["draftVersionId"]:
            versions += f", draft {flow['draftVersion']}"
        print(f"{flow['number']:<10} {flow['code'] or '(no code)':<32} {flow['status']:<9} {flow['triggerType']:<22} {versions}  {flow['description']}")


def cmd_export(args) -> None:
    flow = find_flow(args.flow)
    version_id = flow["publishedVersionId"] if args.published else (flow["draftVersionId"] or flow["publishedVersionId"])
    if not version_id:
        raise ApiError(f"Flow {flow['number']} has no {'published ' if args.published else ''}version to export.")
    query = urllib.parse.quote(f"versionId eq {version_id}")
    url = f"{company_url()}/flows({flow['id']})/flowVersions?$filter={query}&$select=version,definition"
    found = call("GET", url)["value"]
    if not found:
        raise ApiError(f"Version {version_id} of flow {flow['number']} was not found.")
    definition = json.dumps(json.loads(found[0]["definition"]), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(definition, encoding="utf-8")
        print(f"Exported {flow['number']} {flow['code']} version {found[0]['version']} to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(definition)


def cmd_import(args) -> None:
    text = Path(args.file).read_text(encoding="utf-8-sig")
    try:
        json.loads(text)
    except ValueError as err:
        raise ConfigError(f"{args.file} is not valid JSON: {err}") from None
    result = call("POST", f"{company_url()}/flowImports", {"definition": text})
    issues = json.loads(result.get("issues") or "[]")
    if args.json:
        result["issues"] = issues
        print(json.dumps(result, indent=2))
        return
    what = "New flow" if result["createdNewFlow"] else "New draft of flow"
    print(f"{what} {result['flowNumber']}, draft version {result['version']} (not published).")
    if issues:
        print("Publishing would stop or warn on:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("No issues found. Review the draft in the flow editor, then publish it there.")


def cmd_login(_args) -> None:
    login()


def cmd_logout(_args) -> None:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    print("Signed out.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoFlow Flow API: find, export and import flows.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("login", help="sign in with a device code").set_defaults(func=cmd_login)
    sub.add_parser("logout", help="forget the cached sign-in").set_defaults(func=cmd_logout)
    sub.add_parser("companies", help="list companies").set_defaults(func=cmd_companies)
    p = sub.add_parser("list", help="list flows")
    p.add_argument("--filter", help="OData filter, e.g. \"status eq 'Published'\"")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)
    p = sub.add_parser("export", help="export a flow's definition")
    p.add_argument("flow", help="flow code or number")
    p.add_argument("--published", action="store_true", help="export the published version even if there is a draft")
    p.add_argument("-o", "--output", help="file to write (default: stdout)")
    p.set_defaults(func=cmd_export)
    p = sub.add_parser("import", help="import a definition as a draft")
    p.add_argument("file")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_import)
    args = parser.parse_args()
    try:
        args.func(args)
    except ConfigError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    except ApiError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
