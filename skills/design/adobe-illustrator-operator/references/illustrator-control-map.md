# Illustrator control map

Use this reference when the task needs Illustrator itself, Flue, or UI control.

## Authority order

1. User request and current project instructions
2. Real file state and app state
3. Adobe official scripting references
4. Local runtime readback
5. Flue docs when Flue is the selected bridge
6. Model memory


## Official API anchors

Use the Adobe Illustrator Scripting Guide before writing non-trivial JavaScript. The guide is community-hosted docsforadobe material based on Adobe scripting content.

Core pages to check:

- Illustrator guide index: https://ai-scripting.docsforadobe.dev/
- Document object: https://ai-scripting.docsforadobe.dev/jsobjref/Document/
- SVG export options: https://ai-scripting.docsforadobe.dev/jsobjref/ExportOptionsSVG/
- PNG24 export options: https://ai-scripting.docsforadobe.dev/jsobjref/ExportOptionsPNG24/
- ExtendScript guide: https://extendscript.docsforadobe.dev/

Confirmed anchors from current docs:

- `app.activeDocument.exportFile(exportFile, exportFormat, options)` is the core export method.
- `app.activeDocument.artboards` exposes document artboards.
- `app.activeDocument.layers` exposes document layers as a read-only collection reference.
- `ExportOptionsSVG` supports `saveMultipleArtboards`, `artboardRange`, `preserveEditability`, `embedRasterImages`, `coordinatePrecision` and related SVG settings.
- `ExportOptionsPNG24` supports `artBoardClipping`, `horizontalScale`, `verticalScale`, `transparency`, `matte` and `antiAliasing`.

Do not rely on model memory for exact enum names. Check docs or live runtime before using export formats or option enums.


## Adobe app boundary

Keep this skill focused on Illustrator and local `.ai` asset work: artboards, layers, paths, swatches, text and native export behavior.

Do not add Photoshop, Express, Firefly, Creative Cloud asset registry or App Builder workflows here unless they directly affect an Illustrator file operation. Those belong in separate Adobe Photoshop, Adobe Express or Adobe workflow/orchestration skills.

For Illustrator-to-Penpot reconstruction, use `penpot-1to1-reconstruction.md` after this control map. The control map chooses the safe Illustrator lane. The reconstruction reference defines the required tree order, text handling, naming and proof gates.

## Native options

### Illustrator scripting

Illustrator supports scripting with JavaScript/ExtendScript, AppleScript on macOS, and VBScript on Windows. Prefer JavaScript payloads that return JSON strings.

Useful operations:

- `app.documents.length`
- `app.activeDocument.name`
- `app.activeDocument.artboards`
- `app.activeDocument.layers`
- `app.activeDocument.swatches`
- `app.activeDocument.selection`
- `Document.exportFile`
- `Document.saveAs`

Treat `saveAs`, `close`, `package`, relink, overwrite exports, and destructive layer operations as approval-gated.

Official reference starting points:

- https://ai-scripting.docsforadobe.dev/
- https://extendscript.docsforadobe.dev/

## macOS bridge sketch

Use only after confirming Illustrator exists and the user wants live app control. Keep the bridge read-only until the first JSON smoke test succeeds. Prefer a local script file or reviewed bridge command over pasting a multi-line shell snippet from memory.

If the app name differs by version, discover it with Launch Services or ask the user to open Illustrator and retry against the visible app.

## Flue bridge

Flue is an optional upstream MIT project. It provides shell-to-app bridges and app-specific skills. It is not required for file-level work.

Use only after review and user approval:

```bash
python3 -m pip show flue
flue where
flue test illustrator
```

If installed from source or package docs, read the local Illustrator adapter docs before scripting. Do not trust generic examples for active documents.

## Computer-use bridge

Use UI control when scripting cannot complete the flow. Good examples:

- install or operate an Illustrator plugin
- resolve a modal dialog
- choose an export preset visually
- inspect appearance that the DOM cannot describe
- operate a cloud or account UI

Stop on payment, login, license, destructive overwrite, or cloud sync decisions.

## Smoke tests

### Read-only Illustrator smoke

Goal: confirm bridge connection, no edits.

Expected JSON fields:

- `ok`
- `documents`
- `activeDocument` when a document is open

### Export smoke

Goal: export a copy to a new temp path.

Rules:

- output path must be explicit
- never overwrite without approval
- verify output exists and has nonzero size
- visually inspect when the task is visual
