import assert from "node:assert/strict";
import test from "node:test";
import { relativeImports } from "./imports.mjs";

test("checks actual imports without interpreting fixtures as programs", () => {
  const source = [
    `const fixture = 'require("./python3")';`,
    '// import "./comment.js"',
    'import "./side-effect.js";',
    'export * from "../export.mjs";',
    'import("./lazy.js");',
    'require("./real.cjs");',
  ].join("\n");
  assert.deepEqual(relativeImports(source), ["./side-effect.js", "../export.mjs", "./lazy.js", "./real.cjs"]);
});
