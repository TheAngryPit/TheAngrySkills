import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const scriptsDirectory = import.meta.dir;
const commanderPackagePath = join(scriptsDirectory, "node_modules", "commander", "package.json");

export function ensureDependenciesInstalled(): void {
  if (!existsSync(commanderPackagePath)) {
    throw new Error("Missing pstack CLI dependencies. Dependency installation requires separate authorization; provision with bun install --frozen-lockfile in the scripts directory before retrying.");
  }
  const expected = JSON.parse(readFileSync(join(scriptsDirectory, "package.json"), "utf8")).dependencies.commander;
  const installed = JSON.parse(readFileSync(commanderPackagePath, "utf8")).version;
  if (installed !== expected) {
    throw new Error(`Pstack CLI requires commander ${expected}; installed ${installed}. Review and reprovision the pinned dependencies before retrying.`);
  }
}
