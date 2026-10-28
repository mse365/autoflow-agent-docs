# Actions

Every action step has `"type": "action"` and `"action": <ordinal>`. The ordinal is the number stored in the JSON; the name is the enum value name used for the file names here.

- **Terminating** steps must be the last step in their sequence (`"terminating": true`).
- **Group** steps carry `edges` with nested step sequences.
- **Early access** steps are released in stages (selected customers first, everyone a few weeks later): they only work where their AutoFlow feature is already switched on. Use them only when the user confirms it is.

Machine-readable list: [`spec/index.json`](../../spec/index.json).

## Control

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Case | `105` |  | yes | [CaseStep](CaseStep.md) |
| Confirm dialog | `5564418` |  | yes | [ConfirmDialog](ConfirmDialog.md) |
| Decision | `100` |  | yes | [Decision](Decision.md) |
| Loop Over Elements | `101` |  | yes | [ForEachLoop](ForEachLoop.md) |
| While Loop | `106` |  | yes | [WhileLoop](WhileLoop.md) |

## Data

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Add to Collection | `201` |  |  | [AddToCollection](AddToCollection.md) |
| Create Collection | `200` |  |  | [CreateCollection](CreateCollection.md) |
| Create Element | `202` |  |  | [ElementCreate](ElementCreate.md) |
| Parser | `5564403` |  |  | [Parser](Parser.md) |
| Set Element | `203` |  |  | [ElementSet](ElementSet.md) |

## Documents

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Azure Blob: Get file | `5564421` |  |  | [AzureBlobGet](AzureBlobGet.md) |
| Azure Blob: List files | `5564420` |  |  | [AzureBlobList](AzureBlobList.md) |
| Azure Blob: Upload file | `5564422` |  |  | [AzureBlobPut](AzureBlobPut.md) |
| Create PDF | `5564410` |  |  | [PdfPrint](PdfPrint.md) |

## Records

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Add Item Tracking | `5564417` |  |  | [AddItemTracking](AddItemTracking.md) |
| Add Stamp | `5564428` |  |  | [AddStamp](AddStamp.md) |
| Cancel Stamp | `5564429` |  |  | [CancelStamp](CancelStamp.md) |
| Delete Record | `5564407` |  |  | [DeleteRecord](DeleteRecord.md) |
| Draw number from number series | `5564554` |  |  | [NoSeriesDraw](NoSeriesDraw.md) |
| Find Records | `5564409` |  |  | [FindRecords](FindRecords.md) |
| Get Dimensions | `5564559` |  |  | [GetDimensions](GetDimensions.md) |
| Insert Record | `5564405` |  |  | [InsertRecord](InsertRecord.md) |
| Modify Record | `5564406` |  |  | [ModifyRecord](ModifyRecord.md) |
| Rename Record | `5564408` |  |  | [RenameRecord](RenameRecord.md) |
| Set Dimension Values | `5564558` |  |  | [SetDimensionValues](SetDimensionValues.md) |

## SubFlows

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Run SubFlow | `5564411` |  |  | [RunSubFlow](RunSubFlow.md) |
| Start flow | `5564424` |  |  | [StartManualFlow](StartManualFlow.md) |

## Tasks

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Approval task (early access) | `5564560` |  | yes | [ApprovalTask](ApprovalTask.md) |
| Selection task (early access) | `5564423` |  |  | [SelectionTask](SelectionTask.md) |

## Trigger Responses

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Prevent page close | `5564419` |  |  | [PreventPageClose](PreventPageClose.md) |
| Respond to Webhook | `5564404` |  |  | [RespondToWebhook](RespondToWebhook.md) |
| Return PDF | `5564414` | yes |  | [PdfReturn](PdfReturn.md) |
| Return SubFlow Output | `5564412` | yes |  | [SubFlowOutput](SubFlowOutput.md) |
| Set File Name | `5564416` | yes |  | [SetReportFileName](SetReportFileName.md) |
| Set document field values | `5564530` | yes |  | [SetDocumentField](SetDocumentField.md) |

## Utilities

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| Error | `102` | yes |  | [Error](Error.md) |
| Log | `104` |  |  | [Log](Log.md) |
| Run Codeunit / Report | `5564415` |  |  | [RunCodeunit](RunCodeunit.md) |
| Send Notification | `5564557` |  |  | [SendNotification](SendNotification.md) |
| Sleep | `103` |  |  | [Sleep](Sleep.md) |

## Web

| Action | `action` | Terminating | Group | Page |
|---|---:|:---:|:---:|---|
| HTTP Request | `5564402` |  |  | [HttpRequest](HttpRequest.md) |
| Send Email | `5564413` |  |  | [SendEmail](SendEmail.md) |
