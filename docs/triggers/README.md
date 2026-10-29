# Triggers

Every flow starts with exactly one trigger step, `steps[0]`:

```json
{ "id": "<GUID>", "type": "trigger", "trigger": <ordinal>, "description": "...", "slug": "trigger",
  "iconUrl": "...", "configuration": { }, "outputs": [ ], "level": 0 }
```

`trigger` is the ordinal from the table below. `outputs` lists what the trigger exposes to later steps, which reference it as `{{trigger_<name>}}`. The trigger's slug is always `trigger`. Rebuild `outputs` whenever you change `configuration`, because outputs are derived from it (see each page).

## Comparison

| Trigger | `"trigger"` | Runs | Transaction | Record context (outputs) | Typical use |
|---|---|---|---|---|---|
| [When manually started](Manual.md) | `100` | async (Job Queue entry per start), or inline when an extension asks for it | commit per step | `Rec` if `tableNo` set | On-demand jobs, "Start Flow" page action, called by other flows or extensions by Code |
| [On a schedule](Scheduled.md) | `101` | async, recurring Job Queue entry (60 min) | commit per step | none | Periodic batch work |
| [When a record is inserted](GlobalInsert.md) | `5564402` | async (picked up every 5 min) | commit per step | `Rec` | React to new records in any table |
| [When a record is modified](GlobalModify.md) | `5564450` | async (picked up every 5 min) | commit per step | `Rec`, `ChangedFields` | React to field changes (watch fields) |
| [When a record is deleted](GlobalDelete.md) | `5564451` | async (picked up every 5 min) | commit per step | selected field values only, no `Rec` | Clean-up or sync after deletes |
| [When a webhook is received](Webhook.md) | `5564403` | InstantReturn: async. WaitForResponse: sync until Respond to Webhook or `timeoutSec`, the rest async | sync phase: one commit at the end | `Payload`, `Method`, `Headers`, `Query` | Inbound HTTP integrations (BC online only) |
| [When invoked as a SubFlow](SubFlow.md) | `5564404` | sync, inline in the calling Run SubFlow step | no commits of its own, part of the calling step | one output per declared input | Reusable building blocks |
| [When a PDF is printed](OnPdfPrint.md) | `5564405` | sync, inside the report request (up to `timeoutSec`) | commits when the run starts and again at the end | `ObjectPayload`, `DocumentStream`, `ReportId`, … | Replace or stamp PDFs (one flow per environment) |
| [When a report file name is generated](OnReportFileName.md) | `5564406` | sync, inside the report request (up to `timeoutSec`) | commits when the run starts and again at the end | `ProposedFileName`, `Rec_<reportId>`, … | Custom file names (one flow per environment) |
| [When a record is created or modified (interactive)](OnDocumentModify.md) | `5564529` | sync, in the user's save | **atomic** with the user's write, no commit | `Rec`, `xRec_<f>` / `Rec_<f>` | Validate or adjust records while they are saved |
| [When a document is released (interactive)](OnDocumentRelease.md) | `5564543` | sync, before the release | **atomic**, no commit | `Rec` (header) | Release checks, custom approval status |
| [When a document is posted (interactive)](OnDocumentPost.md) | `5564549` | sync, before posting | **atomic**, no commit | `Rec` (header) | Posting checks, last-minute header values |
| [When a document is reopened (interactive)](OnDocumentReopen.md) | `5564409` | sync, before the reopen | **atomic**, no commit | `Rec` (header, status before the reopen) | Control reopen, also for Pending Approval |
| [When a page is opened (interactive)](OnPageOpen.md) | `5564407` | sync, before the page shows | commits its own execution | `Rec`, `PageNo` | Hints on open, block access |
| [When a page is closed (interactive)](OnPageClose.md) | `5564408` | sync, before the page closes | commits its own execution | `Rec`, `PageNo` | Keep the page open until data is complete |

### AutoFlow Supplier Foundation (separate app)

These triggers exist only when the **AutoFlow Supplier Foundation** app is installed. A page action fires them for one record at a time; every flow on the trigger runs inline while the user waits, in one transaction per record. The exceptions are the price update and sending orders, whose runs are queued; the Start steps of Supplier Foundation queue any of four triggers for one record. Read the [overview](../apps/SupplierFoundation.md) first.

| Trigger | `"trigger"` | Fired by | Transaction | Record context (outputs) | Typical use |
|---|---|---|---|---|---|
| [When an item search is performed](ItemSearch.md) | `5564012` | *Search supplier items* (sales documents, Item List), per search text | committed after the search | `Query`, `Context`, `SalesHeader` | Search the supplier, Add search result per hit |
| [When a search result is selected](SearchSelected.md) | `5564013` | OK in the search dialog | one, committed at the end | every result field, `Payload`, `ExistingItemNo`, `Item` | Import the item, add a sales line |
| [When an item is updated](ItemUpdate.md) | `5564014` | *Update from supplier* (Item Card, Item List); Start item update (queued) | one per item | `Item`, `ItemVendor`, `VendorNo` | Refresh item master data |
| [When a price update is requested](PriceUpdate.md) | `5564015` | *Update price and availability* (sales/purchase documents and lines, items) | **queued**: one async run (Job Queue entry) per line or item and flow, commit per step | `Source`, `SalesLine` / `PurchaseLine` / `Item`, `ItemVendor`, `VendorNo` | Price (Set supplier price) and stock from the supplier |
| [When a purchase order is sent](POSent.md) | `5564016` | *Send to supplier* (Purchase Order, list) | **queued**: one async run per order and flow, commit per step | `PurchaseHeader`, `VendorNo` | Transmit the order |
| [When an order status is updated](OrderStatus.md) | `5564017` | *Update order status* (Purchase Order, list); Start order status update (queued) | one per order | `PurchaseHeader`, `VendorNo` | Order status, create supplier documents |
| [When a supplier document is accepted](DocAccepted.md) | `5564018` | *Accept* (Supplier Documents) | one per document, with the status change | `SupplierDocument`, `PurchaseHeader`, `DocumentType`, `VendorNo` | Apply a confirmation or delivery note |
| [When a supplier document is rejected](DocRejected.md) | `5564019` | *Reject* (Supplier Documents) | one per document, with the status change | `SupplierDocument`, `PurchaseHeader`, `DocumentType`, `VendorNo` | Tell the supplier or the buyer |

"async" runs execute in a background Job Queue session and commit after every step. No trigger opts into one-transaction background runs, so a failed background run leaves the work of earlier steps in place. The interactive document triggers run inside the user's own transaction: an error in the flow rolls back the user's action, together with the flow's work and its execution entry.

## Steps that depend on the trigger

The step picker hides steps that do not apply to the flow's trigger. This is a **picker filter only**: a hand-written definition that uses them elsewhere is not rejected at publish unless a rule below says so.

| Step | Offered only with |
|---|---|
| Respond to Webhook (`5564404`) | Webhook |
| Return SubFlow Output (`5564412`) | SubFlow |
| Return PDF (`5564414`) | OnPdfPrint |
| Set report file name (`5564416`) | OnReportFileName |
| Set document field values (`5564530`) | OnDocumentModify, OnDocumentRelease, OnDocumentPost, OnDocumentReopen |
| Prevent page close (`5564419`) | OnPageClose |
| Add search result (`5564012`, Supplier Foundation) | ItemSearch |
| Run SubFlow (`5564411`), Start flow (`5564424`) | never shown directly. Published SubFlows and Manual flows appear as their own tiles. |

Publish rules that depend on the trigger:

| Step | Trigger(s) | Severity | Message |
|---|---|---|---|
| Confirm dialog (`5564418`) | OnDocumentModify, GlobalInsert, GlobalModify, GlobalDelete | warning | The confirm dialog '%1' runs inside the record change that started the flow. Business Central does not open dialogs there, so when a user triggers the flow it fails at this step. It only works when the flow runs in the background, where the answer under 'Without a user interface' applies. |

## Publish sequence and trigger errors

When a flow is published, checks run in this order:

1. Every flow needs a Code on the flow card (root `code` on import): "Flow %1 (%2) has no Code. Enter a Code on the flow card before activating it – for example YOURCOMPANY.FLOW-NAME. The Code identifies the flow across companies and environments."
2. The flow must contain at least one action step: "A flow must contain at least one action step before it can be published. Add a step after the trigger and try again."
3. **Trigger validation (hard stop).** Manual, OnDocumentModify, OnDocumentRelease, OnDocumentPost, OnDocumentReopen, OnPageOpen and OnPageClose check their configuration. Errors are reported as `This flow's trigger cannot be published:` followed by the list. The other triggers have no checks at this point.
4. Step warnings, such as dangling references and terminating steps with successors, are collected and need the user's confirmation. A headless publish cannot confirm them, so it fails.
5. Licensing (free tier: 2 published flows per production environment). SubFlow skips it.
6. Trigger registration: OnPdfPrint and OnReportFileName require at least one report line and allow only one published flow per environment. Webhook registers with the AutoFlow portal (production needs a paid license); failures there do not stop the publish.
7. Job Queue: Scheduled gets a recurring entry every 60 minutes. GlobalInsert, GlobalModify and GlobalDelete get a recurring pick-up entry every 5 minutes. Supplier Foundation's price update and order sending, and its Start steps, create one entry per run when used. All other triggers get none.

Before 27.0.40 only Manual and SubFlow flows needed a Code, with their own messages.

## Shared configuration patterns

- **`tableNo`** (integer): the watched table. It is stored on the trigger registration at publish. For record triggers, `0` means the flow never fires.
- **`filters`**: `[{ "fieldNo": int, "filter": "text" }]`, used by every record, document and page trigger. Each filter is a standard Business Central filter expression on one field of the triggering record. It is applied literally, so `{{…}}` placeholders are **not** resolved. Max. 250 characters. Rows with `fieldNo` 0 are skipped, and a second row on the same field replaces the first. An invalid expression never errors; the record just does not match.
- **`guiOnly`** (boolean, default `true`) on the interactive document triggers skips sessions without a UI.
- **`timeoutSec`** (integer) on the synchronous triggers: 30 by default, 10 for the page triggers, 30 / 60 for the Supplier Foundation triggers (none for the queued price update and order sending). For Webhook and OnPdfPrint the limit is checked between steps (a running step is not interrupted), and `0` or less means no limit.
- Values that triggers emit as text (watch-field values, deleted-record fields) use a locale-invariant format, such as `1234.5` and `2026-10-23`.
