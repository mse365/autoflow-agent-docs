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
  "feature": null,                  // dark-launched steps: the portal feature flag that enables them (e.g. "tasks"), else omitted
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
| `requiredUnless` | `key`, `ifKey`, `equals` | `key` required unless `configuration[ifKey] == equals` (an absent `ifKey` counts as not equal) |
| `regex` | `key`, `pattern` | string matches pattern (Python `re.fullmatch`) |
| `triggerNotIn` | `triggers` | the flow's trigger ordinal (`steps[0].trigger`) is not one of `triggers`; reported on the step |
| `feature` | `feature` | documents that the step needs a dark-launched feature; checked through `availability` / `feature`, not per rule |

Keys may be dotted paths into nested objects (`auth.type`). Fields of array rows are written as `array[].field` (e.g. `attachments[].type`); the validator documents but does not check these. Anything that cannot be expressed this way stays as prose in `check` with no `machine` entry.

### Dark-launched steps

A step that ships behind a portal feature flag gets `"availability": "dark-launched"` and `"feature": "<flag>"`. Its page starts with an **Early access** callout. The validator warns on it (`step.dark-launched`) unless `--features <flag>` says the user confirmed the flag is on for their environment. When the step becomes generally available, set `availability` to `"ga"`, drop `feature`, and remove the callout.

