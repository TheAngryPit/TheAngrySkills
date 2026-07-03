# Illustrator to Penpot 1:1 reconstruction

Use this reference when recreating an Illustrator source file inside Penpot.

The goal is not a similar-looking preview. The goal is a Penpot file that a human designer can review and edit with the same practical intent as the Illustrator source.

## Canon

Illustrator is the canonical source for:

- document identity;
- artboard order;
- artboard dimensions and positions;
- layer tree;
- visual stacking;
- text content and text styling;
- object grouping;
- source naming.

Penpot is the reconstruction target. It must follow Illustrator. It must not redefine the structure just because SVG import, PDF extraction, or MCP output made a different tree.

## Start gate

Before creating or modifying Penpot objects:

1. Identify the exact Illustrator source file.
2. Record source size and modified timestamp.
3. Confirm the user asked for reconstruction, not a new design.
4. Confirm whether this is one document in a larger sequence.
5. Read the full Illustrator tree through Illustrator scripting or direct app inspection.
6. Export visual references from Illustrator for comparison.

Do not continue if the source tree has not been read.

## Illustrator tree read

Capture at minimum:

- document name;
- artboard count, names, bounds and order;
- top-level layers in order;
- nested layer, group and object order;
- object type: layer, group, compound path, path, placed item, raster item, clipping group or text frame;
- object name when present;
- visibility and lock state when extractable;
- text frame content, bounds, font family, style, size, color and alignment when extractable.

Return the tree as JSON or a compact table before import work. If the tree is huge, summarize the full tree by artboard and keep the raw JSON as a local debug artifact.

## Import order

Recreate each artboard in Illustrator tree order.

Default order:

1. Create or select the matching Penpot file.
2. Rename the Penpot file and page before import.
3. Create one Penpot board per Illustrator artboard.
4. Match board dimensions and relative positions.
5. For each board, process source layers from back to front.
6. For each source layer, process child groups and objects in tree order.
7. Recreate TextFrames as Penpot text.
8. Import non-text vector groups as editable vector groups where practical.
9. Use reference exports only for comparison or temporary debugging.

Do not bulk-import all pages as flattened SVGs and then fix on top.

## Transfer unit choice

Use the smallest meaningful unit that preserves editability and review value.

Priority:

1. named Illustrator layer;
2. named group or compound object;
3. semantic object cluster derived from neighboring tree context;
4. individual path only when needed for editability or accuracy;
5. page-level export only as reference, never as final structure.

Avoid object-by-object extraction when it creates a useless Penpot tree or destabilizes Illustrator.

## Native text rule

If the Illustrator object is a TextFrame, recreate it as Penpot text wherever technically possible.

Preserve:

- text content;
- font family and style or closest installed equivalent;
- font size;
- fill color;
- text box bounds;
- alignment when extractable;
- source tree path.

Do not turn text into outlines or raster images unless it is documented as a technical compromise.

## Naming grammar

Source names win.

When Illustrator gives generic or empty names, generate names from context:

`Document / Artboard / SourceLayer / SemanticObject / Role_Type_Index`

Use lowercase semantic object names in generated segments. Keep the original `Pag_*` artboard names when present.

Examples:

- `Brand_Guidelines_v8_Layered_Pit / Pag_01 / hero_title / title_text_001`
- `Brand_Guidelines_v8_Layered_Pit / Pag_08 / dont_stretch_logo / logo_mark_group_001`
- `Brand_Guidelines_v8_Layered_Pit / Pag_14 / final_composition / logo_red_hexagon_path_001`
- `Logo_ExampleBrand_Layered / Pag_09 / color_palette / swatch_cyan_rect_001`

Rejected final names:

- `SVG path`
- `svg-path_001`
- `Imported SVG`
- `Group`
- `Rectangle`
- `TEMP`
- `TEST`
- `NOT_FINAL`

Generic names may exist during a single operation only. They must be resolved before the page gate passes.

## Page gate

Do not advance to the next artboard until the current artboard has:

- matching board dimensions and position;
- visible match against Illustrator reference export;
- source layer order represented in Penpot;
- native text recreated where applicable;
- semantic layer names;
- zero unresolved temp names;
- zero unresolved generic imported names;
- structural readback recorded.

## Final gate

Do not report the file as complete until:

- every Illustrator artboard exists in Penpot;
- board count matches source artboard count;
- all boards were visually checked against Illustrator references;
- all boards pass the structure gate;
- source file size and timestamp match the starting snapshot;
- any technical compromises are listed by artboard;
- the goal report includes time and token usage when a goal is active.

## Failure protocol

If the import strategy produces a wrong tree, stop.

Do not keep layering fixes on top of the wrong import.

1. Delete the wrong Penpot import if safe.
2. Keep failed scripts or exports only as debug artifacts.
3. State why the method failed.
4. Move to the next more faithful method.
5. Re-test on one page before continuing.
