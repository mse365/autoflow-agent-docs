# References, slugs and Smart syntax

This page is the reference for how a value inside a step's `configuration` points at data: placeholder tokens (`{{…}}`), slugs, the inline mini-languages (SmartFormula `[[…]]`, SmartDate `[@…@]`, SmartControls `{#…#}`, SmartFilter conditions), and the flow-level `smartFieldDefs` block that defines how record paths are walked. It also covers the structural step properties every step carries: `id`, `level`, `x`/`y`, `customIconUrl`, `status`, and the root `notes`.

The machine-readable companion is [`spec/smart-syntax.json`](../spec/smart-syntax.json). It holds the regexes, built-in tokens, operators, functions and messages.

> **The short version**
> - A step output is referenced as `{{<slug>_<outputName>}}`. Walk into a record reference with dots: `{{trigger_Rec.No}}`.
> - A leaf segment matches either a SmartField definition name or a BC field name. BC field names are compared case-insensitively and ignore punctuation, so for `"Sell-to Customer No."` you write `selltocustomerno`.
> - A token that doesn't resolve is **left in the text verbatim**. The flow doesn't fail, and nothing is written to the execution log.
> - Format a value inline with `;`: `{{today;9}}` gives `2026-10-23`, and `{{x;<Precision,2:2><Standard Format,9>}}` sets two decimals.
> - Slugs match `[A-Za-z][A-Za-z0-9-]{0,19}` and must not contain `_`. The trigger's slug is always `trigger`.

---

## 1. Placeholder tokens `{{…}}`

### 1.1 Grammar

```
token      := "{{" body "}}"
body       := path [ ";" format ]                 // first ";" splits; format is everything after it
path       := root { "." segment }
root       := name [ "[" index "]" ]               // e.g. find_results[0]
segment    := name [ "[" index "]" ]
index      := digits                               // 0-based
```

- **Scanning.** The scanner finds `{{`, then takes the **first** `}}` after it. The body is everything in between, with nothing trimmed (`{{ x }}` looks up `" x "`). Tokens do not nest.
- **Length.** The body must be shorter than 251 characters. A longer body is not treated as a token and is kept literally.
- **Unclosed `{{`.** A `{{` with no `}}` after it is plain text. For example, a regex such as `\{{2}` is kept as written.
- **Paths.** A dot always separates path segments, so a BC field name that contains a dot (`No.`) can't be written as-is. Use the punctuation-free form instead (see 1.3).
- **Format suffix.** The text after the first `;` is the format. Because format strings never contain `;`, the split is unambiguous.

### 1.2 Roots: what a token can start with

| Root | Kind | Example | Notes |
|---|---|---|---|
| `<slug>_<outputName>` | output of an earlier step (or the trigger) | `{{findCustomer_results}}`, `{{trigger_Rec}}` | The main case. The slug and the output name are joined by a single `_`. |
| `today` | value | `{{today}}` | Today's date in the session's date format. Use `{{today;9}}` for ISO. |
| `workdate` | value | `{{workdate;9}}` | The work date of the session that **started** the execution. In design-time previews it is the current work date. |
| `currentDateTime` | value | `{{currentDateTime;9}}` | Current date-time. |
| `currentUser` | reference → table 2000000120 (User) | `{{currentUser.username}}` | The User record of the user running the step. |
| `currentCompany` | reference → table 79 (Company Information) | `{{currentCompany.name}}` | The first Company Information record. |
| loop index variable | value | `{{i}}` | Only inside a `{#for {{…}}[i]#}` block. It counts from 1. |
| `credential.username`, `credential.password` | special | `{{credential.username}}` | Only in an HTTP Request body when a credential is selected. They are replaced at send time and stay unresolved everywhere else. |

The editor's field picker lists the outputs of every step on the path from the trigger to the current step: earlier siblings, enclosing group steps (for example the loop item of a For Each), and those steps' predecessors. It adds the five built-ins at the end.

At runtime the context holds every output that has **already executed**. A reference to a step on another branch only resolves if that branch actually ran earlier.

**Trigger outputs** are registered under `trigger_<name>`, and the whole key is capped at 30 characters. The output name is therefore truncated to 22 characters (`trigger_` takes 8). **Action outputs** have no practical cap. Output names themselves are at most 30 characters.

Common output names:

| Producer | References |
|---|---|
| Record triggers (insert, modify, delete, document events, page triggers) | `{{trigger_Rec}}` (reference), `{{trigger_Rec.<field>}}` |
| Webhook trigger | `{{trigger_Payload}}`, `{{trigger_Method}}`, `{{trigger_Headers}}`, `{{trigger_Query}}` |
| Find Records | `{{<slug>_results}}` (reference array), `{{<slug>_results[0].no}}`, `{{<slug>_results.no}}` (= first element) |
| For Each | `{{<slug>_currentItem}}`, `{{<slug>_currentItem.<field>}}`, `{{<slug>_iteration}}`, `{{<slug>_total}}`, `{{<slug>_items}}` |

The individual step pages list every step's outputs.

### 1.3 Walking a path through records

When the root is a **reference**, which at runtime holds a record id (table and primary key), each following segment is resolved against the current record's table:

1. **SmartField definition.** If the table has a definition with this exact name in the flow's `smartFieldDefs` (see 1.8):
   - A `value` definition returns that field (FlowFields are calculated).
   - A `reference` definition jumps to the related record and continues the path from there.
   - When the flow has no `smartFieldDefs` at all, definitions registered globally in the company are used instead.
2. **BC field name, leaf segments only.** If no definition exists, the **last** segment may name a real table field. Both sides are normalised: everything except `A–Z a–z 0–9` is removed and the rest is lower-cased. `No.` becomes `no`, `Sell-to Customer No.` becomes `selltocustomerno`, and `Balance (LCY)` becomes `balancelcy`. So `{{trigger_Rec.no}}`, `{{trigger_Rec.No}}` and `{{trigger_Rec.NO}}` all resolve the same field.
3. **No match.** The token is not resolvable and is kept verbatim.

An **intermediate** segment, meaning any segment that is followed by another one, must be a `reference` SmartField definition. A BC field name can't be used to jump into a related table. To reach `Customer` from a `Sales Header` record, define a reference SmartField on table 36 that links `"No."` to `"Sell-to Customer No."`, then write `{{trigger_Rec.Customer.name}}`.

**Arrays.**
- **Reference arrays** (for example Find Records `results`) are stored as `name[0]`, `name[1]`, and so on.
  - `{{x_results[2].no}}` addresses element 2.
  - `{{x_results.no}}` means the first element.
  - A bare `{{x_results}}` is a **selector** and is never turned into text.
- **Value arrays.** A bare `{{x_items}}` substitutes the **first** element, and `{{x_items[3]}}` substitutes element 3.

**Missing records.**
- If a reference points at a record that no longer exists, its fields resolve to their empty or default values, such as `""` or `0`.
- If a relation finds no related record, the result is the same: empty or default values.
- If a relation matches several records, the **first** one in the definition's key and direction is used.

### 1.4 What happens at runtime (step configurations)

Before a step runs, its whole `configuration` object is serialized to JSON text and passed through a single resolver pass. The result is parsed back into JSON and handed to the step. Within each text segment, the resolver works in this order:

1. **SmartControls** `{#if#}` and `{#for#}` are expanded. Their bodies go through the steps below, once per iteration.
2. **SmartDates** `[@ … @]` are evaluated, after resolving any `{{…}}` inside them.
3. **Aggregates** `sum( … )`, `avg( … )`, `min( … )`, `max( … )` and `count( … )` whose first argument is a `{{list}}` are reduced to a number. This happens **anywhere in the text**, not only inside `[[ ]]`.
4. **`{{…}}` substitution** follows the *selective* rules below. Every substituted value is **JSON-escaped**, so quotes, backslashes and newlines in data can't break the configuration.
5. **SmartFormulas** `[[ … ]]` are evaluated, but **only if every `{{…}}` in that segment resolved**. If any token stayed unresolved, the formulas in that segment are left as literal `[[…]]` text.

**Selective substitution rules.** A token is replaced only when it resolves to a **scalar value**. Everything else is left in the text exactly as written:

| Token resolves to… | Result in the configuration |
|---|---|
| a scalar value, a value-array root, or a value leaf | the formatted value |
| a reference (for example `{{trigger_Rec}}`) | kept as `{{trigger_Rec}}`, so selector-type keys can resolve it to a record |
| a reference-array root (for example `{{find_results}}`) | kept verbatim |
| an unknown root, an unknown leaf, or a wrong type | kept verbatim |

As a consequence:

- **Unknown tokens never raise an error.** A mistyped `{{trigger_Rec.Nmae}}` ends up literally in the email subject, field value, or other target. The resolver's diagnostics are not written to the execution log.
- **Empty values** substitute as an empty string. There is no default-value syntax. To check for empty, use a condition: `{#if {{x}} = '' #}…{#endif#}`.
- **A reference token in free text is not rendered.** Writing `{{trigger_Rec}}` in a message body shows the literal token. Reference a field instead.
- **Publish check.** At publish time, every `{{X_…}}` token whose text before the first `_` is not a slug in the flow produces a warning: `Step "%1" references unknown slug "%2".` This is the only reference check that exists. The comparison is case-sensitive, and the check runs over all string values in every step's configuration.

### 1.5 Default rendering and the format suffix

Without a suffix, a value is rendered with BC's `Format()` in the **session's** language and region. In a German session that means `1.234,56` and `23.10.26`. A value defined in `smartFieldDefs` with a `format` uses that format by default.

The inline suffix `{{path;FORMAT}}` takes precedence over the definition's format. `FORMAT` can be one of the following:

| Suffix | Effect | Example |
|---|---|---|
| an integer | BC standard format number. `9` is XML/invariant (ISO dates, `.` decimal). | `{{today;9}}` → `2026-10-23` |
| a BC format string | `Format(value, 0, '<…>')` | `{{trigger_Rec.postingdate;<Day,2>.<Month,2>.<Year4>}}` |
| `base64` / `utf8` / `utf16` | **BLOB, Media or binary outputs only.** Base64 (the default for binary) or bytes decoded as UTF-8 or UTF-16 text. On a text value these suffixes do nothing. | `{{trigger_Rec.picture;base64}}` |
| `xmlEscape` / `utf8-xmlEscape` / `utf16-xmlEscape` | Escapes `& < > " '` for XML. On a binary source it decodes first (UTF-8 by default). The escaping is not idempotent: `&amp;` becomes `&amp;amp;`. | `{{trigger_Rec.name;xmlEscape}}` |

How the suffix is applied:

- **Case.** The suffix keywords are not case-sensitive.
- **Text values with a format string.** For a text value (a step output or built-in), the text is first parsed as Date, then Decimal, then Boolean, then DateTime, and the format is applied to the first type that parses.
- **Invalid formats.** An invalid format falls back to the **unformatted** value, never to an empty string.
- **Binary values.** A token whose **whole** value is exactly one `{{name}}` (no suffix, no other text) is handed to binary-aware steps as raw bytes. This applies to the HTTP Request body and to Insert/Modify Record on a BLOB field.

### 1.6 Selector fields (reference inputs)

Some configuration keys don't take text. They take a **selector**: exactly one braced token naming a record, a collection or an iterator. Examples are the For Each `selector`, the `reference` of Modify, Delete and Rename Record, and SubFlow reference inputs. The rules:

- The value must be `{{…}}` with nothing else around it. Whitespace around it and inside the braces is trimmed. `{{}}` and an unbraced name are rejected.
- Allowed forms:
  - a flat reference: `{{trigger_Rec}}`
  - a reference array, which means its first element where a single record is needed: `{{find_results}}`
  - an indexed element: `{{find_results[1]}}`
  - a **dotted relation** through `reference` SmartField definitions: `{{trigger_Rec.SalesLines}}`. When the step loops, this iterates every related record.
- The step resolves the selector itself. Because references are never substituted (1.4), the token arrives unchanged.

### 1.7 Loop items

There are two ways to iterate:

- **For Each step.** Inside its body, use `{{<forEachSlug>_currentItem}}` (a reference or a value, mirroring the selector's type), `{{<forEachSlug>_currentItem.<field>}}`, `{{<forEachSlug>_iteration}}` and `{{<forEachSlug>_total}}`.
- **`{#for#}` inside a text** (section 4.4). Inside the block, write the **same selector path** you iterate over, extended with fields: `{#for {{trigger_Rec.SalesLines}}#}{{trigger_Rec.SalesLines.description}}{#endfor#}`. The resolver rebinds that prefix to the current row.

### 1.8 `smartFieldDefs`: the flow-level path definitions

SmartField definitions live at the **root** of the flow definition, next to `steps`:

```jsonc
{
  "name": "…",
  "steps": [ … ],
  "smartFieldDefs": {
    "36": {                                   // table no. (as a string key)
      "Customer": {                           // SmartField name, max 30 chars, unique per table
        "type": "reference",
        "table": 18,                          // target table no.
        "key": "No.",                         // optional: comma-joined BC field NAMES of a key on the target table
        "descending": false,                  // optional: read direction (picks the LAST match when true)
        "relation": [                         // how to find the target record(s)
          { "target": 1, "type": "field", "value": 2 },        // target."No." = source field 2 ("Sell-to Customer No.")
          { "target": 23, "type": "const", "value": "BLUE" },  // equality (SetRange) on text/code, else used as a filter
          { "target": 59, "type": "filter", "value": "<>0" }   // BC filter expression
        ]
      },
      "PostingDate": { "type": "value", "field": 20, "format": "<Year4>-<Month,2>-<Day,2>" }
    }
  }
}
```

| Key | Applies to | Meaning |
|---|---|---|
| `type` | both | `"value"` or `"reference"`. Matched case-insensitively. Any other value drops the definition. |
| `field` | value | Field number on the table named by the outer key. |
| `format` | value | Default format, using the same forms as the inline suffix. An empty string is allowed. |
| `table` | reference | Target table number. |
| `key` | reference | Comma-joined field **names** of an active key on the target table, for example `"Document Type,Document No.,Line No."`. If it no longer matches a key, the primary key is used. |
| `descending` | reference | Boolean. When omitted, the direction is ascending. |
| `relation[].target` | reference | Field number on the **target** table. |
| `relation[].type` | reference | `"field"`: `value` is a source-table field number, compared for equality. `"const"`: a literal value. `"filter"`: a BC filter expression. |
| `relation[].value` | reference | See `type`. |

How names and definitions behave:

- **Name derivation in the editor.** When a definition is created from the picker, its name is derived from the field caption, or the table caption for references. The caption is PascalCased, umlauts are transliterated (`ü` becomes `ue`), the result is cut to 30 characters, and on a collision the suffixes `2`, `3`, … are added. `Sell-to Customer No.` becomes `SelltoCustomerNo`.
- **Renaming a definition.** The editor rewrites every placeholder segment that resolves to the renamed definition **at that position in the path**. Literal text and segments that resolve to BC field names are not touched.
- **Missing fields.** A value definition whose field no longer exists resolves to an empty string, with a warning that is not shown to users.

---

## 2. Slugs

Every step has a `slug`. Downstream steps reference its outputs as `{{<slug>_<output>}}`.

### 2.1 Grammar

```
slug := [A-Za-z][A-Za-z0-9-]{0,19}      // 1–20 chars, starts with a letter, letters/digits/hyphen, NO underscore
```

- **No underscore.** The `_` separates the slug from the output name, so a slug can't contain one.
- **Trigger slug.** The trigger step's slug is always `"trigger"`. No action can take it: an auto-generated slug that collides becomes `Trigger2`, and renaming a step to `trigger` is rejected as a duplicate.
- **Uniqueness.** A slug must be unique across the **whole** flow, including steps inside every branch and loop body.

### 2.2 Generation (new step, duplicated step)

The slug is generated from the step `description`:

1. Transliterate `ä→ae ö→oe ü→ue Ä→Ae Ö→Oe Ü→Ue ß→ss é è ê ë→e á à â→a ñ→n ç→c`.
2. Convert to PascalCase: every character outside `A–Z a–z 0–9` is a word boundary and is dropped, and the first letter of each word is upper-cased. The rest of the word keeps its case.
3. Strip leading characters until the first letter, then cut to 20 characters.
4. If nothing is left (for example a description in a non-Latin script), use `Step`.
5. If the slug already exists (compared **case-insensitively**), append `2`, `3`, … and shorten the base so the total stays at 20 characters or fewer.

Examples: `"Send e-mail to customer"` → `SendEMailToCustomer`. `"Prüfe Lieferung"` → `PruefeLieferung`. `"2nd approval"` → `ndApproval`: the PascalCase step produces `2ndApproval`, and only the leading digit is removed afterwards. `"Find Records"` a second time → `FindRecords2`.

When a sub-tree is duplicated, every step in the copy gets a new `id` and a newly generated slug. References **inside** the copy are rewritten to the new slugs, and references to steps outside the copy stay as they were.

> Older flows may contain lower-case or hyphenated slugs such as `find-records`. Those remain valid and work as long as they match the grammar above.

### 2.3 Renaming

When a slug is changed in the step editor:

- **Rejected renames.** The new slug is rejected if it doesn't match the grammar, or if any other step already uses exactly that slug (this comparison is case-sensitive). A rename to the same value does nothing. The editor message is:
  `The slug "%1" cannot be applied. A slug must start with a letter, contain only letters, digits or hyphens (no underscore), be at most 20 characters long, and be unique within the flow.`
- **Rewriting references.** After a rename, every string value in every step's `configuration` (all depths, all branches) has the literal `{{<old>_` replaced by `{{<new>_`. Text outside braces and tokens without the `_` directly after the slug are left alone.
- **What isn't rewritten.** Keys outside `configuration` aren't rewritten, and neither are tokens inside `smartFieldDefs`. A hand-edited JSON file gets **no** automatic rewrite, so update the references yourself.

---

## 3. Structural step properties

| Property | Format | Notes |
|---|---|---|
| `id` | GUID string: **upper-case, no braces**, for example `"6F9619FF-8B86-D011-B42D-00C04FC964FF"` | Generated by the system's GUID function with the braces removed. Must be unique among all steps, edges and notes. Edges (`edges[].id`) use the same format. |
| `level` | integer ≥ 0 | Nesting depth: the number of `edges[` segments on the path to the element. Top-level steps are `0`, a group step's edges are its level + 1, and steps inside an edge share the edge's level. **It is written but never read.** The engine always works the level out from the step's position, so a wrong value is harmless. Keep it consistent anyway. |
| `x`, `y` | integers (canvas pixels) | Optional manual position from dragging in the designer. When the step is the first step of an edge, the same `x`/`y` is also stored on that edge. If omitted, the step is placed automatically. |
| `customIconUrl` | string | Optional per-step icon. If a step's `configuration.customIconUrl` exists, saving the configuration copies it to the step level, and an empty string clears it. The designer shows `customIconUrl` and falls back to `iconUrl`. |
| `status` | object such as `{"running":n,"pending":n,"repeat":n,"success":n,"error":n}` | Execution counters for the designer's monitoring view. Zero counts are omitted. Display only: **leave it out of authored flows**. |

**Notes.** These are canvas sticky notes, stored in the root `notes` array:

```json
{ "id": "1C9D0E4A-…", "html": "<b>Why</b><br>…", "color": "yellow", "x": 120, "y": 40, "width": 240, "height": 120 }
```

- **`color`** is one of `yellow`, `pink`, `blue`, `green`, `lavender`, `grey`. Any other value becomes `yellow` when a note is created, and is rejected when the color is changed.
- **`html`** is sanitised: only `<b> <i> <u> <br>` are kept, all attributes are removed, `<div>`/`<p>` boundaries become `<br>`, and the content is capped at 10,240 characters.
- **`width`/`height`** are optional. If they're missing, the note sizes itself automatically.

---

## 4. The Smart mini-languages

All of these live **inside string values** of `configuration`. Which keys accept which syntax is listed per step in the `smart` attribute of the step spec.

| Syntax | Delimiters | Produces |
|---|---|---|
| SmartField | `{{ … }}` | a value (section 1) |
| SmartFormula | `[[ expr ; format ]]` | a number |
| SmartDate | `[@ expr ; format @]` | a date, time, date-time or number |
| SmartControls | `{#if …#}`, `{#elseif …#}`, `{#else#}`, `{#endif#}`, `{#for {{sel}}[idx]#}`, `{#endfor#}` | conditional or repeated text |
| SmartFilter | none: the whole value is a condition | true or false |

The editor finds tokens by taking the earliest opener among `{{`, `[[`, `[@` and `{#`, then the first matching closer. An opener without a closer is plain text.

### 4.1 SmartText (single line and multiline)

SmartText is plain text that may contain any of the tokens above. Single-line and multiline fields store the same thing: a JSON string, with real line breaks stored as `\n` in the JSON. Multiline fields are used for bodies and messages, and some of them render in a monospace font.

There is **no escape syntax**. A literal `{{name}}` that happens to resolve can't be protected, and a token that doesn't resolve stays verbatim anyway.

### 4.2 SmartCode

SmartCode is a code editor (JSON, XML or plain text highlighting) for the same SmartText language. Tokens stay as raw, color-coded text instead of pills, so the stored string is exactly the payload you see.

The stored value is an ordinary string, like any SmartText. Because substituted values are JSON-escaped (1.4), write string tokens **inside** quotes in a JSON body: `"name": "{{trigger_Rec.name}}"`. In an XML body, use `;xmlEscape` for text.

### 4.3 SmartFormula `[[ … ]]`

```
formula   := "[[" expr [ ";" format ] "]]"
expr      := sum
sum       := product { ("+" | "-") product }
product   := power { ("*" | "/" | "%") power }        // % = integer modulo
power     := unary [ "^" power ]
unary     := ("-" | "+") unary | atom
atom      := number | "{{" path "}}" | "(" expr ")" | call
number    := digits [ "." digits ]                    // invariant: "." is the decimal separator
call      := abs(e) | min(a,b) | max(a,b) | round(v,d) | floor(v,d) | ceil(v,d)
           | sum({{list}}[, rowExpr]) | avg({{list}}[, rowExpr]) | count({{list}}[, rowExpr])
           | min({{list}}) | max({{list}}) | min({{refList}}, rowExpr) | max({{refList}}, rowExpr)
```

| Function | Meaning |
|---|---|
| `abs(a)` | absolute value |
| `min(a,b)`, `max(a,b)` | the smaller or larger of two values |
| `round(v,d)` | round to `d` decimals, to the nearest value. `d` can be negative: `round(1234,-2)` gives `1200`. |
| `floor(v,d)` | round down to `d` decimals |
| `ceil(v,d)` | round up to `d` decimals |
| `sum`, `avg`, `min`, `max`, `count` over a list | Aggregates (see below). |

**Aggregates.** The first argument is a `{{list}}`: a value array, a reference array, or a dotted relation.

- **Value array.** `sum({{x_amounts}})` reduces the array's own elements. A second argument is not allowed.
- **References.** A row expression is required (`count` excepted). In it, refer to the row through the same path: `sum({{trigger_Rec.Lines}}, {{trigger_Rec.Lines.amount}} * 1.19)`.
- **Short form.** `sum({{trigger_Rec.Lines.amount}})` is understood as `sum({{trigger_Rec.Lines}}, {{trigger_Rec.Lines.amount}})`.
- **`count`.** Without a row expression, `count` returns the number of rows. With one, it counts rows whose expression produced a value.
- **Blank rows.** Rows whose expression is blank or doesn't resolve are skipped. They don't count towards `avg`.
- **Empty or missing lists.** An empty or missing list gives `0`.

**Format.** The text after the top-level `;` is a BC format string for the decimal result. If it contains neither `<Standard Format` nor `<Integer`, `<Standard Format,9>` is appended, so the default output is invariant (`1234.5`). Examples:
- `[[{{a}}*1.19]]` → `119`
- `[[5/2;<Precision,2:2>]]` → `2.50`
- `[[{{x}};<Precision,2:2><Standard Format,0>]]` → locale formatting with two decimals.

**Runtime behaviour and limits.** These matter, because the runtime evaluator is simpler than the editor:

- **Unevaluable formulas.** A formula that can't be evaluated is left as literal `[[…]]` text, with no error. This includes bodies longer than 250 characters, unknown functions, text operands, and regex-looking text such as `[[a-z]]`.
- **Unresolved fields.** If any `{{…}}` in the same text segment stayed unresolved, the formulas in that segment are not evaluated (1.4).
- **Function calls must be whole operands.** A call is only recognised when it **spans a whole operand**. `max(1,2)+3` works because `+` splits first. Function names are matched case-insensitively.
- **Exponents.** At runtime `^` evaluates **left to right** (`2^3^2` = 64), while the editor parses it as right-associative. Use parentheses.
- **Negative literals.** A negative literal directly after an operator does not evaluate correctly at runtime: `2*-3` gives `-3`. Write `2*(0-3)`. The editor writes unary minus this way itself.
- **`round`, `floor` and `ceil` need both arguments.**
- **Resolved operands.**
  - Operands that resolve to a number are parsed invariant first, then in the session culture, then as `1.234,56` (`,` decimal, `.` thousands).
  - An empty operand counts as `0`.
  - Use `{{x;9}}` for decimals you want parsed exactly.

**Editor parse errors.** These appear when a formula is opened in the builder:
`Unexpected character "%1" in the formula.` · `A SmartField in the formula is missing its closing "}}".` · `The formula is incomplete.` · `Unexpected "%1" – check the brackets.` · `Unknown function "%1".` · `%1() needs %2 argument(s).` · `"%1" is not a number.` · `The aggregate %1() needs a {{list}} as its first argument.`

### 4.4 SmartControls `{# … #}`

```
if-block  := "{#if " cond "#}" text { "{#elseif " cond "#}" text } [ "{#else#}" text ] "{#endif#}"
for-block := "{#for " "{{" selector "}}" [ "[" indexVar "]" ] "#}" text "{#endfor#}"
```

**Keywords.** Keywords are case-insensitive, and the whitespace before `#}` is optional: `{#endif #}` and `{#endif#}` are both fine.

**Conditions.**
- `true` and `false` are literals. Anything else is resolved: `{{…}}`, then `[[…]]`. The result is evaluated as a **SmartFilter** condition (4.6).
- A condition is **false** if any `{{…}}` in it doesn't resolve, if a formula in it doesn't evaluate, or if it's empty.
- **SmartDates `[@…@]` and aggregates such as `sum({{list}})` are not evaluated inside an `{#if …#}` / `{#elseif …#}` condition.** Only `{{…}}` and `[[…]]` are. To use one, compute it in an earlier step, or use a Decision step: its condition key goes through the full pipeline.

**Loops.**
- The selector must be braced, as in 1.6. It can be a flat reference array, a single reference, or a dotted relation.
- Inside the body, refer to the current row with the same path. Nested `{#for#}` blocks over child paths work.
- `[i]` gives a 1-based counter, available as `{{i}}`. The index name must not be the name of a reference.
- An unbraced selector, a missing `{#endfor#}`, or an empty set produces **nothing** for the block.

**Layout.** A line that contains only control tags (and whitespace) is removed together with its line break, so tags on their own lines don't leave blank lines.

**Example** (an XML body):

```
<lines>
{#for {{trigger_Rec.Lines}}[n]#}
  <line no="{{n}}">{{trigger_Rec.Lines.description;xmlEscape}}</line>
{#endfor#}
</lines>
{#if {{trigger_Rec.amount}} > 1000 #}<approval>required</approval>{#else#}<approval>none</approval>{#endif#}
```

### 4.5 SmartDate `[@ … @]`

```
smartdate := "[@" expr [ ";" format ] "@]"
expr      := "today" | "now" | "workdate" | literal | "{{" path "}}"
           | dateadd(expr, n, "unit")          unit: day|week|month|year|hour|minute
           | startof(expr, "unit")             unit: day|week|month|year
           | endof(expr, "unit")               unit: day|week|month|year   (end of day is 23:59:59)
           | calc(expr, "dateFormula")         BC date formula: "+1D", "CM", "-1M+CM", "<CW>"…
           | datediff(a, b, "unit")            → number (a − b), unit: day|week|month|year|hour|minute
           | year(expr) | month(expr) | day(expr) | weekday(expr)   → number (weekday: 1 = Monday)
literal   := ISO date "2026-06-15" | ISO date-time "2026-06-15T08:00:00Z" | dd.mm.yyyy | dd.mm.yy | mm/dd/yyyy | number
```

**How expressions evaluate.**
- Everything is computed as a date-time. A date counts as 00:00, and a time counts as today.
- Function and unit names are not case-sensitive, and the unit must be in double quotes.
- Inside the flow JSON, the quotes appear escaped (`\"month\"`). The resolver un-escapes them.
- `calc` takes the invariant date-formula letters (`D W M Y C`) first, then the session's letters.

**Format** (after the top-level `;`):

| Format | Output |
|---|---|
| empty or `@date@` | the date in the session format |
| `@time@` | `HH:MM` |
| `@datetime@` | the date-time in the session format |
| any BC format string | that format, for example `<Year4>-<Month,2>-<Day,2>` or `9` |

Number results are rendered invariant unless a format is given.

**Nesting.** SmartDates are evaluated **before** `{{…}}` and `[[…]]`, so a number they produce can be used inside a formula: `[[ [@ datediff({{trigger_Rec.duedate;9}}, today, "day") @] * 10 ]]`.

**`workdate` difference.** Inside `[@…@]`, `workdate` is the work date of the session evaluating the step. The `{{workdate}}` token, by contrast, is the work date of the session that started the run.

**Errors.** A SmartDate that fails to evaluate is left verbatim, and nothing is reported. The internal messages are: `Unknown SmartDate function "%1".` · `The SmartDate function %1() got the wrong number of arguments.` · `"%1" is not a valid date or time.` · `"%1" is not a valid unit.`

Examples:
- `[@ endof(dateadd({{workdate}}, -1, "month"), "month") ; 9 @]` gives the last day of the previous month in ISO format.
- `Due [@ calc({{trigger_Rec.postingdate;9}}, "+14D"); <Day,2>.<Month,2>.<Year4> @]`

### 4.6 SmartFilter (conditions)

A SmartFilter is a **boolean condition string**. It is used by Decision, While Loop, the `{#if#}` tag, and Find Records' `smartFilter`. It is **not** converted into a BC table filter. After `{{…}}`/`[[…]]` substitution it is evaluated in memory. (Find Records also has a separate `filters` array, which uses native BC filter syntax per field.)

```
filter      := comparison | "!(" filter ")" | "(" filter ")" comb "(" filter ")" | "true" | "false"
comparison  := left op right
op          := "=" | "!=" | ">" | "<" | ">=" | "<=" | "~" (contains) | "^=" (starts with) | "$=" (ends with)
comb        := "&" (and) | "|" (or)
```

**Canonical stored form.** This is what the builder writes, with single spaces around operators: `{{x_total}} > 1000`, `!({{x_status}} = Released)`, `({{a}} = 1) & ({{b}} > 2)`.

**How a comparison is evaluated:**

1. The operator is chosen by finding the first match in this priority order: `^=`, `$=`, `>=`, `<=`, `!=`, `~`, `=`, `>`, `<`, `&`, `|`. The text is then split **at the first occurrence** of that operator.
2. Operands are trimmed. A value of `''` means the empty string. **Other quotes are not stripped**, so write `= Released`, not `= 'Released'`.
3. If both operands parse as decimals (in the session culture), they are compared as numbers. Otherwise they are compared as case-sensitive text.
4. `~`, `^=` and `$=` are always text comparisons.

**Parentheses.** Parenthesised groups are evaluated from the inside out and replaced by `true` or `false`. A leading `!` negates `true`/`false` or a parenthesised group. `!=` with an empty left side is handled correctly.

**Rules to follow:**
- **Wrap both sides of every `&` or `|` in parentheses**, and combine only **two** conditions per level. Nest for more: `(({{a}} = 1) & ({{b}} = 2)) & ({{c}} = 3)`. An unparenthesised `a = 1 & b = 2` is split at the first `=` and does not work.
- **Watch for operator characters in values.** A substituted value containing `& | ( ) = < > ! ~` can change the structure of the condition. The editor warns: `A value contains & | ( or ) outside a token – the filter may not evaluate as written.`
- **Unresolvable conditions.** A text that matches no rule evaluates to **false**. In `{#if#}`, any unresolved token also makes the condition false.

**Editor messages** (shown when the builder can't load the string):
`The SmartFilter expression is empty.` · `The SmartFilter expression "%1" cannot be parsed into the builder. Please edit it manually or clear it.` · `The SmartFilter expression "%1" combines more than two conditions at the top level. Wrap each pair in parentheses so the builder can load it.` · `Unknown SmartFilter operator "%1".` · `Unknown SmartFilter combinator "%1".`

### 4.7 SmartSorting

SmartSorting is an internal helper that generates keys which sort between two other keys, using a base-62, base-36 or base-26 alphabet. It is **not** part of the flow definition language: no configuration key stores a SmartSorting expression.

### 4.8 Field picker modes and what gets stored

The editor's SmartField picker always stores **text with the full braced path**, for example `{{trigger_Rec.Customer.Name}}`. The mode only controls what may be selected:

| Mode | Selectable | Typical use |
|---|---|---|
| Copy & Close | anything (copied to the clipboard) | browsing and managing SmartField definitions |
| `referenceorvalue` | a reference or a value | For Each selector |
| `referenceonly` | references only | `reference` of Modify, Delete and Rename Record |
| `valueonly` | value leaves only | scalar inputs |

A *scoped* picker, used for fields under a loop iterator, is locked to one root and stores the full path under that root.

Configuration-canvas field kinds that carry references:

| Kind | Stores |
|---|---|
| `smarttext` | a SmartText string. With the multiline flag, a multiline SmartText string. |
| `smartcode` | a SmartText string that is edited as code |
| `smartfilter` | a SmartFilter condition string |
| `selector` | one braced token, following the picker mode above |
| `picker` | a primary-key value, or a SmartField token |
| `keyref` | a comma-joined list of key field names |
| `tableref` | a table number |

A step's own page lists the kind of each key.

**Messages from SmartField definition editing:** `A SmartField must have a name.` · `A SmartField named %1 already exists on this table. Choose a different name.`

---

## 5. Value outputs vs reference outputs

| | Value output | Reference output |
|---|---|---|
| Declared in `outputs` | `{ "name": "total", "type": "value" }` | `{ "name": "Rec", "type": "reference", "tableNo": 36 }` |
| Holds at runtime | text. Binary payloads are kept as bytes and render as base64 unless a binary format is used. | a **record id**: the table number plus the primary-key values of one record |
| In SmartText | substituted, with formatting | **not substituted**: stays as `{{slug_Rec}}`. Walk to a field (`{{slug_Rec.no}}`) to get text. |
| As a step input | any text key | selector keys (1.6): the step resolves the token to the record |
| Arrays | `name[0]`, `name[1]`, …; the bare name gives the first element | `name[0]`, `name[1]`, …; the bare name selects the array (first element where one record is needed) |

- **`tableNo`.** The `tableNo` in `outputs` is what the designer uses to offer fields and relations below the reference, and to type-check selectors. At runtime the table comes from the record id itself.
- **Value vs reference depends on configuration.** Some steps declare an output as `value` when their configuration doesn't name a table. For example, record triggers emit `Rec` as a value when no table is set. Path navigation then isn't available.
- **Regenerating outputs.** Always regenerate `outputs` from the configuration the way the step defines them. Don't invent output names, because only names that the step actually registers at runtime resolve.

### Example

A trigger on Sales Header, Find Records over customers in the same city, and an email:

```jsonc
{ "slug": "trigger", "outputs": [ { "name": "Rec", "type": "reference", "tableNo": 36 } ] }
{ "slug": "FindCustomers",
  "configuration": { "tableNo": 18, "filters": [ … "{{trigger_Rec.selltocity}}" … ] },
  "outputs": [ { "name": "results", "type": "reference", "tableNo": 18 } ] }
{ "slug": "SendMail",
  "configuration": {
    "subject": "Order {{trigger_Rec.no}} – first of [[count({{FindCustomers_results}})]]: {{FindCustomers_results.name}}",
    "body": "Due: [@ calc({{trigger_Rec.duedate;9}}, \"+7D\"); <Day,2>.<Month,2>.<Year4> @]{#for {{FindCustomers_results}}[i]#}\n{{i}}. {{FindCustomers_results.name}}{#endfor#}"
  } }
```

---

## 6. Uncertainties

- **Case sensitivity of root names** (`trigger_Rec` vs `trigger_rec`) at runtime has not been verified. Write roots and SmartField definition names with the **exact** case used in `outputs` and `smartFieldDefs`. Only the BC-field-name fallback (1.3) is case-insensitive for certain.
- **How the selector-based `{#for#}` behaves for value arrays** (as opposed to reference arrays and relations) has not been verified. Use the For Each step for value collections.
