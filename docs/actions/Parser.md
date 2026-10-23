# Parser

[← All actions](README.md)

Extracts values from JSON, XML or arbitrary text using JsonPath, XPath or regular expressions.

| | |
|---|---|
| Enum name | `Parser` |
| Ordinal | `"action": 5564403` |
| Category | Data |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA |

## What it does

The step resolves the SmartText `input` and parses it once: as JSON for JsonPath, as XML for XPath, or as plain text for RegEx. It then evaluates every line of `lines` against that input, using the same selector language for all lines. Each line produces a value output named after the line. If a selector returns several results, they become indexed outputs (see [Outputs](#outputs)). A selector with no match yields an empty string; it does not raise an error. Input that cannot be parsed fails the step.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `type` | string | no | `"JsonPath"` | `"JsonPath"`, `"XPath"` or `"RegEx"`, exact and case-sensitive. Any other value is treated as JsonPath. |
| `input` | string | yes | `""` | Text to parse, for example `{{PostOrder_responseBody}}`. SmartText. |
| `lines` | object | yes | `{}` | `{ "<outputName>": "<selector>" }`. Output names are truncated to 30 characters and selectors to 2048. The editor treats selectors as SmartText. |
| `namespaces` | object | no | `{}` | XPath only: `{ "<prefix>": "<uri>" }` (prefix at most 20 characters, URI at most 250). If the object is non-empty, **only** these prefixes are registered. If it is empty, namespaces are discovered automatically (see below). |
| `rawXmlLines` | object | no | `{}` | XPath only: `{ "<outputName>": true }` returns the matched elements of that line as outer XML instead of inner text. |
| `previewSample` | string | no | `""` | Sample input for the editor's Run Preview. Not used at run time. |

In the editor, the parser type is chosen as an option, but it is stored as the text key `type`. Lines and namespaces are edited as rows but stored as the objects shown above.

### Parse modes

**JsonPath** (`type` = `"JsonPath"`)
- `input` must be valid JSON. An empty or invalid input raises `Failed to parse input as JSON.`
- Each selector is evaluated with Business Central's `SelectToken`, for example `$.id`, `$.customer.name`, `$.items` or `$.items[0].sku`.
- A string, number or boolean result becomes `<name>`, as text with strings unescaped. A JSON `null` gives `''`. An object becomes `<name>` holding the object as JSON text.
- An array result becomes `<name>[0]`, `<name>[1]`, and so on, one per element. Object elements are serialised as JSON text.
- A path that does not exist gives `<name>` = `''`.
- Avoid paths that match several tokens (wildcards such as `[*]` or recursive descent `..`): the platform's single-token selection is expected to reject them. Select the array itself instead.

**XPath** (`type` = `"XPath"`)
- `input` must be well-formed XML. Otherwise the step fails with `Failed to parse input as XML.`
- Unprefixed element names in a selector are rewritten to `*[local-name()='Name']`. For example, `//Order/Line` matches regardless of the document's namespaces. Prefixed names (`ns:Order`), attributes (`@id`), `*`, `.`, and function steps such as `text()` or `count(...)` are left as written.
- Namespace prefixes come from `namespaces` if it is non-empty. Otherwise they are discovered from the document: each namespace URI keeps the prefix it uses there, a default namespace gets `def`, and a prefix shared by two URIs gets a numeric suffix (`ns2`, …) on the second URI.
- **Every match is indexed, even a single one:** `<name>[0]`, `<name>[1]`, …. An element gives its inner text (concatenated text of all descendants), or its outer XML when the line is in `rawXmlLines`. An attribute gives its value, and a text or CDATA node gives its value.
- No match gives `<name>` = `''`. An invalid XPath raises the platform's error.

**RegEx** (`type` = `"RegEx"`)
- `input` is used as-is. Selectors are .NET regular expressions.
- Each non-empty match becomes an indexed output `<name>[0]`, `<name>[1]`, …. If the pattern has a capture group, the **first group** is used; otherwise the whole match is used.
- Zero-width matches are skipped. If there are no non-empty matches, `<name>` = `''`.
- An invalid pattern raises the platform's error.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| one per key of `lines` | `value` | – | declared in `outputs` as `{ "name": "<key>", "type": "value" }` |

The JSON declares one output per line. At run time, a line writes one of the following:

| result | runtime value(s) |
|---|---|
| single value (JsonPath scalar or object) | `<slug>_<name>` |
| several values (JsonPath array, any XPath match, any RegEx match) | `<slug>_<name>[0]`, `<slug>_<name>[1]`, … |
| no match | `<slug>_<name>` = `''` |

To reference a line:

- `{{<slug>_<name>}}` gives the scalar value, or the **first** element of an indexed result.
- `{{<slug>_<name>[n]}}` gives element *n*.
- A For Each loop or an aggregate formula over `{{<slug>_<name>}}` walks all elements.

Runtime names are cut at 30 characters including the `[n]` suffix. Keep line names short (about 26 characters or fewer) when a selector can return ten or more items.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | warning | `type` is `JsonPath`, `XPath` or `RegEx` (otherwise JsonPath is used) | – |
| editor | error | `lines` is an object of name → selector | – |
| editor | warning | `lines` has at least one entry | – |
| editor | warning | line names are at most 30 characters | – |
| runtime | error | JsonPath input is not valid JSON | Failed to parse input as %1. (`%1` = `JSON`) |
| runtime | error | XPath input is not well-formed XML | Failed to parse input as %1. (`%1` = `XML`) |

The step has no editor validity check and no publish check of its own. Only the generic dangling-reference warning applies.

## Runtime errors

- `Failed to parse input as JSON.` / `Failed to parse input as XML.`
- The platform's errors for an invalid XPath expression, an invalid regular expression, or (expected) a JsonPath that matches more than one token.

## Example

```json
{
  "id": "1F2E3D4C-5B6A-4798-8877-665544332211",
  "type": "action",
  "action": 5564403,
  "description": "Parse JsonPath",
  "slug": "ParseOrder",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/braces.svg",
  "terminating": false,
  "configuration": {
    "type": "JsonPath",
    "input": "{{PostOrder_responseBody}}",
    "lines": {
      "orderId": "$.id",
      "status": "$.status",
      "orderLines": "$.lines",
      "firstSku": "$.lines[0].sku"
    },
    "namespaces": {},
    "rawXmlLines": {},
    "previewSample": ""
  },
  "outputs": [
    { "name": "orderId", "type": "value" },
    { "name": "status", "type": "value" },
    { "name": "orderLines", "type": "value" },
    { "name": "firstSku", "type": "value" }
  ]
}
```

Here `orderLines` selects an array, so the run time writes `ParseOrder_orderLines[0]`, `ParseOrder_orderLines[1]`, …, one JSON object text per order line, which a For Each loop or another Parser step can process. `orderId`, `status` and `firstSku` are scalars. Here is an XPath variant of `lines`, with `"type": "XPath"`:

```json
{ "orderNo": "/Envelope/Body/Order/@no", "lineXml": "//Order/Line" }
```

Add `"rawXmlLines": { "lineXml": true }` to get each `<Line>` element as XML.

## Gotchas

- The `outputs` array lists plain line names. Indexed names (`name[0]`) appear only at run time.
- With XPath, even a single match is `name[0]`. `{{slug_name}}` still works because of the first-element fallback.
- A non-empty `namespaces` object switches off auto-discovery completely. List every prefix your selectors use.
- `previewSample` can contain sensitive sample data and is exported with the flow. Leave it empty in shared definitions.
