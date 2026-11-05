# Documenting your own steps for AutoFlow AI

For publishers of Business Central apps – vendor apps and per-tenant extensions – that add their own triggers or actions to AutoFlow.

The AutoFlow AI Flow Builder inside Business Central works with every trigger and action installed in the environment, not only with AutoFlow's. Before it configures a step, it reads that step's **page** (markdown) and **spec** (JSON). AutoFlow does not take these from this repository: it asks the app that owns the step, through two events. AutoFlow's own steps answer the same way – the pages in [actions/](actions/README.md) and [triggers/](triggers/README.md) are copies of what AutoFlow hands to its AI.

## What the AI does with your step

| Your app | What the AI gets |
|---|---|
| answers with a page and a spec | your page and spec. The validator checks every flow the AI builds against the spec's rules (see [validation.md](validation.md#in-app-checks-ai-flow-builder)). |
| answers with a page only | your page. The step's configuration is not checked (`step.no-spec` lint). |
| does not answer | a page AutoFlow generates and marks **auto-generated**: description, category, app and publisher, the fields of the step's configuration page, the configuration keys and defaults the step writes, its outputs and edges, and the keys used in existing flows. It works, but the model has to guess more – documented steps give much better results. |
| answer fails with an error | the generated page, plus a warning that your documentation failed. |

The AI only sees the steps a flow designer could pick in the editor. A step your app hides with `OnFilterActions` (for example while it is not licensed, or under a trigger it does not work with) is not listed for the AI and is reported as `step.unavailable` if a flow uses it. The checks your app runs at publish with `OnValidateFlowStep` already run while the AI builds the flow: an error becomes `step.publish-check`, a warning `step.publish-warning`. In that call `FlowVersionId` is `0`, because the definition is not saved yet – read the step from `Configuration` and `Definition`, not from the database.

## What you provide

For every trigger and action your app adds:

- **A page**: English markdown, written for a model. What the step does, every configuration key with its type, default and allowed values, the outputs, a short example of the step in a flow definition, and pitfalls. The pages in [actions/](actions/README.md) show the shape.
- **A spec** (optional, recommended): a JSON object in the [spec format](../spec/_FORMAT.md) – `kind` (`action` or `trigger`), `id` (your enum value's ordinal), `name`, `caption`, `configuration`, `outputs`, `edges` for group steps, and `rules` with `machine` checks where they can be expressed. `worksWithTriggers` lists the trigger ordinals an action works with. A spec whose `kind` or `id` does not match the step it was asked for, or that does not parse, is ignored with a warning; the page is still used.

## The events

AutoFlow Core publishes two integration events on codeunit **`mse365 AF-CO Config. Mgt.`**:

```al
[IntegrationEvent(false, false)]
procedure OnGetActionAgentDocs(Action: Enum "mse365 AF-CO Action"; var Docs: Text; var Spec: Text; var Handled: Boolean)

[IntegrationEvent(false, false)]
procedure OnGetTriggerAgentDocs(EventTrigger: Enum "mse365 AF-CO Event Trigger"; var Docs: Text; var Spec: Text; var Handled: Boolean)
```

| Parameter | Meaning |
|---|---|
| `Action` / `EventTrigger` | The step AutoFlow asks about: a value of the step enum, possibly declared by another app. |
| `Docs` | Your page as markdown. |
| `Spec` | Your spec as JSON text, or empty. |
| `Handled` | Set it to `true` when you answered. The first app that answers wins. |

Rules for the subscriber:

- Start with `if Handled then exit;`. Answer only for enum values your app declares, and set `Handled` only when you did.
- No pages, dialogs or messages, no database writes and no errors. AutoFlow raises the events while the AI works in the background, inside a try function.
- AutoFlow asks only when the AI needs the step and keeps the answer for the session. Nothing is stored, and a catalogue rebuild never raises the events.
- Build long texts with a `TextBuilder` from text literals of at most 1,000 characters each. That compiles with every Business Central version AutoFlow supports.

To read the answer the way AutoFlow AI does – for example in a test – call `GetActionAgentDocs(Action, Docs, Spec)` or `GetTriggerAgentDocs(EventTrigger, Docs, Spec)` on the same codeunit. They clear `Docs` and `Spec`, raise the event and return `true` when a page came back.

## Example

```al
codeunit 50100 "ACME Step Agent Docs"
{
    Access = Internal;

    [EventSubscriber(ObjectType::Codeunit, Codeunit::"mse365 AF-CO Config. Mgt.", 'OnGetActionAgentDocs', '', false, false)]
    local procedure OnGetActionAgentDocs(Action: Enum "mse365 AF-CO Action"; var Docs: Text; var Spec: Text; var Handled: Boolean)
    begin
        if Handled then
            exit;
        case Action of
            Action::"ACME Send Shipment":
                begin
                    Docs := SendShipmentPage();
                    Spec := SendShipmentSpec();
                end;
            else
                exit;
        end;
        Handled := true;
    end;

    local procedure SendShipmentPage(): Text
    var
        Tb: TextBuilder;
    begin
        Tb.AppendLine('# Send shipment (ACME)');
        Tb.AppendLine('');
        Tb.AppendLine('Sends a posted sales shipment to the ACME carrier portal and returns the tracking number.');
        // ... configuration, outputs, example, notes
        exit(Tb.ToText());
    end;

    local procedure SendShipmentSpec(): Text
    var
        Tb: TextBuilder;
    begin
        Tb.Append('{"kind":"action","name":"SendShipment","id":50100,"caption":"Send shipment (ACME)",');
        Tb.Append('"configuration":[{"key":"shipmentNo","type":"string","required":true,"default":"","enum":null,"maxLength":20,"smart":"text","description":"Posted sales shipment number"}],');
        Tb.Append('"outputs":[{"name":"trackingNo","type":"value","tableNo":null,"when":"always"}],');
        Tb.Append('"rules":[{"id":"SendShipment.shipment-required","severity":"error","stage":"publish","check":"shipmentNo must be filled","message":"Enter a shipment number.","machine":{"type":"required","key":"shipmentNo"}}]}');
        exit(Tb.ToText());
    end;
}
```

The trigger event works the same way. If your steps change often, keep the pages as `.md` and `.json` files in your repository and generate the subscriber from them in your build – that is how AutoFlow's own step pages are maintained.

## Checklist

1. Every trigger and action of your app answers with a page, and preferably a spec.
2. The spec's `kind`, `id` and `name` match the enum value; the configuration keys and outputs are the ones your step really reads and writes.
3. Publish checks live in `OnValidateFlowStep` and work with `FlowVersionId = 0`; availability (licence, trigger) is expressed with `OnFilterActions`.
4. Test the answer with `GetActionAgentDocs` / `GetTriggerAgentDocs`, then ask the AI Flow Builder for a flow that needs your step and check that it reads the step's documentation.
