# Step spec file format

Every trigger and action has two files:

- `docs/<actions|triggers>/<Name>.md` – human/agent-readable reference page
- `spec/<actions|triggers>/<Name>.json` – machine-readable spec consumed by `tools/validate_flow.py`

`<Name>` is the AL enum value name (e.g. `HttpRequest`, `ForEachLoop`, `GlobalModify`).

## spec JSON shape

```jsonc
{
  "kind": "action",                 // "action" | "trigger"
  "name": "HttpRequest",            // enum value name
  "id": 5564402,                    // enum ordinal = the number stored in step.action / step.trigger
  "caption": "HTTP Request",        // English caption shown in the step picker
  "category": "Web",                // picker category, if any
  "availability": "ga",             // "ga" | "dark-launched" | "deprecated" | "internal"; explain in notes
  "terminating": false,             // value written to step.terminating
  "group": false,                   // true if the step carries edges[] (branches/loop bodies)
  "edges": {                        // only when group = true
    "fixed": [ { "value": "true", "description": "True" } ],   // edges always present, by value
    "dynamic": false,               // true if edges are generated from configuration (e.g. Case)
    "rules": "free text describing how edges relate to configuration"
  },
  "configuration": [                // keys of step.configuration (trigger: step.configuration as well)
    {
      "key": "url",
      "type": "string",             // string | integer | decimal | boolean | object | array | guid | date | datetime | any
      "required": true,             // required for the step to work (or to pass a check)
      "default": null,              // value used / written when absent
      "enum": null,                 // allowed values if constrained (list), else null
      "maxLength": null,            // if a length limit applies
      "smart": "text",              // none | text | filter | formula | date | code | sorting | field | record – how references inside are interpreted
      "description": "Target URL. Supports {{slug_output}} placeholders."
    }
  ],
  "outputs": [                      // entries written to step.outputs (what downstream steps can reference)
    { "name": "statusCode", "type": "value", "tableNo": null, "when": "always" }
  ],
  "rules": [                        // every check that exists in the code for this step
    {
      "id": "HttpRequest.url-required",
      "severity": "error",          // error (blocks) | warning (publish asks to confirm; headless publish fails) | info
      "stage": "publish",           // editor (checks in the config dialog) | publish | runtime | import
      "check": "configuration.url must be non-empty",
      "message": "Exact English message text from the source, with %1 placeholders",
      "machine": { "type": "required", "key": "url" }   // optional; see below
    }
  ],
  "notes": [ "free-text gotchas" ]
}
```

### `machine` check types understood by the validator

| type | fields | meaning |
|---|---|---|
| `required` | `key` | key present and not empty string / null |
| `type` | `key`, `valueType` | if present, JSON type matches (string, number, integer, boolean, object, array) |
| `enum` | `key`, `values` | if present (and non-empty), value is one of `values` |
| `range` | `key`, `min`, `max` | numeric value within range (either bound optional) |
| `maxLength` | `key`, `max` | string length ≤ max |
| `requiredIf` | `key`, `ifKey`, `equals` | `key` required when `configuration[ifKey] == equals` |
| `regex` | `key`, `pattern` | string matches pattern (Python `re.fullmatch`) |

Keys may be dotted paths into nested objects (`auth.type`). Fields of array rows are written as `array[].field` (e.g. `attachments[].type`); the validator documents but does not check these. Anything that cannot be expressed this way stays as prose in `check` with no `machine` entry.
