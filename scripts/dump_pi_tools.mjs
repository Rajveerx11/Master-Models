// Dump pi's real tool definitions as an OpenAI-style `tools` array.
//
// This is the wire contract. pi sends these to llama-server as the request's
// top-level `tools` field (see pi-ai/dist/api/openai-completions.js convertTools),
// and llama.cpp --jinja renders them into the prompt via the chat template.
// Training data must carry the SAME array so the rendered prompt matches.
//
// Regenerate after any pi upgrade:
//   node scripts/dump_pi_tools.mjs > training/pi_tools.json
//
// ponytail: resolves pi from the global npm prefix; pass PI_DIST to override.

import { execSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { join } from "node:path";

const dist =
  process.env.PI_DIST ??
  join(
    execSync("npm root -g", { encoding: "utf8" }).trim(),
    "@earendil-works/pi-coding-agent/dist",
  );

const mod = await import(
  pathToFileURL(join(dist, "core/tools/index.js")).href
);

// createAllToolDefinitions() needs no live session to produce schemas.
const defs = mod.createAllToolDefinitions({});
const list = Array.isArray(defs) ? defs : Object.values(defs);

const tools = list.map((t) => ({
  type: "function",
  function: {
    name: t.name,
    description: t.description,
    parameters: t.parameters,
  },
}));

if (tools.length === 0) throw new Error("no tool definitions found in " + dist);
for (const t of tools) {
  if (!t.function.name || !t.function.parameters?.properties) {
    throw new Error("malformed tool definition: " + JSON.stringify(t).slice(0, 200));
  }
}

process.stdout.write(JSON.stringify(tools, null, 2) + "\n");
