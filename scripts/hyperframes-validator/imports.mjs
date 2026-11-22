import { parse } from "acorn";
import { simple } from "acorn-walk";

export function relativeImports(source) {
  const imports = [];
  function collect(node) {
    const value = node?.value;
    if (typeof value === "string" && /^\.{1,2}\//.test(value)) imports.push(value);
  }
  let tree;
  try {
    tree = parse(source, { ecmaVersion: "latest", sourceType: "module" });
  } catch {
    tree = parse(source, { ecmaVersion: "latest", sourceType: "commonjs" });
  }
  simple(tree, {
    ImportDeclaration(node) { collect(node.source); },
    ExportNamedDeclaration(node) { collect(node.source); },
    ExportAllDeclaration(node) { collect(node.source); },
    ImportExpression(node) { collect(node.source); },
    CallExpression(node) {
      if (node.callee.type === "Identifier" && node.callee.name === "require") collect(node.arguments[0]);
    },
  });
  return imports;
}
