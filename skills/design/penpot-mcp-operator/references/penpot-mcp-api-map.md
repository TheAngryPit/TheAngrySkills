# Penpot MCP API Map

Status: practical map for agent-driven Penpot workflows. Verify live API members with `penpot_api_info` because Penpot MCP is version-sensitive.

## Primary Sources

- Official help: `https://help.penpot.app/mcp/`
- Official repository: `https://github.com/penpot/penpot/tree/develop/mcp`
- Official AI workflow kit: `https://github.com/penpot/penpot-ai-kit`

## Tool Map

| MCP tool | Use | Notes |
|---|---|---|
| `high_level_overview` | Read once per session before Penpot MCP work | Do not call repeatedly after already read. |
| `penpot_api_info` | Inspect concrete API types and members | Required before relying on unfamiliar methods. |
| `execute_code` | Run JavaScript in the Penpot plugin context | Use for read probes and controlled mutations. |
| `export_shape` | Export a shape or page to PNG/SVG | Remote mode may be limited compared with local mode. |
| `import_image` | Import local images | Available in local MCP, not remote MCP. |

## Connection Modes

Remote MCP:

- URL shape: `https://design.penpot.app/mcp/stream?userToken=...`
- Best for simple Cloud setup.
- Does not expose privileged local filesystem access.
- For image uploads, local file imports, drag-and-drop asset work, plugin UI work or file picker workflows, use browser control with Chrome or computer-use. Remote MCP alone is not a local asset bridge.
- For custom fonts, use Penpot team/dashboard font upload first. Supported font formats include TTF, OTF, WOFF and WOFF2. Then use the uploaded font family in the Penpot file.
- Do not persist or expose `userToken`.

Local MCP:

- URL shape: `http://localhost:4401/mcp`
- Plugin manifest: `http://localhost:4400/manifest.json`
- Requires local server, browser tab, open Penpot file and active plugin connection.
- Better when local asset import/export is needed.

## Known API Patterns

Confirmed examples from current docs/tool responses:

```js
const page = penpot.createPage();
page.name = "Page name";
penpot.openPage(page);
```

```js
const board = penpot.createBoard();
board.name = "Board name";
board.resize(1440, 900);
penpot.root.appendChild(board);
```

```js
const rect = penpot.createRectangle();
rect.name = "Rectangle name";
rect.resize(200, 100);
rect.fills = [{ fillColor: "#FFDF00", fillOpacity: 1 }];
rect.strokes = [{
  strokeColor: "#333333",
  strokeStyle: "solid",
  strokeWidth: 1,
  strokeAlignment: "center"
}];
board.appendChild(rect);
```

```js
const text = penpot.createText("Copy");
text.name = "Text name";
text.resize(400, 80);
text.growType = "fixed";
text.fontFamily = "Inter";
text.fontSize = "24";
text.fills = [{ fillColor: "#F4F4F1", fillOpacity: 1 }];
board.appendChild(text);
```

```js
penpot.viewport.zoomIntoView([board]);
```

## Anti-Guessing Rules

- Do not assume a member exists because it exists in Figma, SVG DOM, browser DOM, or another design API.
- Do not assume page objects expose `children`.
- Do not assume deletion APIs exist. Query first.
- Do not assume `export_shape` can write local files in remote mode.
- Do not try to upload local images through remote MCP unless they are first made available through a supported browser/UI workflow or an accessible URL.
- Do not build long write scripts until a small read probe and a tiny write proof have passed.
- Do not use remote MCP tokens in markdown docs, commits, screenshots, logs, or shared boards.

## First Prompts

Read-only inspection:

```text
Use Penpot MCP Operator. Inspect the active Penpot file and page only. Return the current page name, root shape keys, available pages if exposed, and the safest next write pattern. Do not modify the file.
```

Small write proof:

```text
Use Penpot MCP Operator. Create one small test board on the active Penpot page with a title, a yellow rectangle, and a status label. Verify by readback and zoom the viewport to the board. Do not rename the file.
```

Design production:

```text
Use Penpot MCP Operator. Before writing, query the exact API methods needed. Then create the requested design as a named board on the active page, keep it editable, verify structure, and report limitations.
```
