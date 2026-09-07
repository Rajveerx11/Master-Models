// Static analysis only. Never imports, evaluates, installs or executes dataset code.
// node scripts/check_frontend_snapshots.cjs <typescript-dir> <snapshots.json> <report.json>
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const [typescriptDir, input, output] = process.argv.slice(2);
if (!typescriptDir || !input || !output) throw new Error('Expected TypeScript directory, input, output');
const ts = require(path.resolve(typescriptDir));
const libRoot = path.resolve(typescriptDir, 'lib');
const rows = JSON.parse(fs.readFileSync(input, 'utf8'));
const result = {
  version: ts.version,
  analyzer_sha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),
  input_sha256: crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex'),
  method: 'Reconstructed full snapshots; syntax and unresolved local identifiers only. Dependencies are not resolved; no repository typecheck/test execution.',
  checked_files: 0,
  records: {},
};
const files = new Map();
const owners = new Map();
for (const row of rows) {
  for (const [p, text] of Object.entries(row.files).filter(([p]) => /\.[cm]?[jt]sx?$/.test(p))) {
    const virtual = path.resolve('/virtual-frontend-audit', row.id.replace(':', '-'), p);
    files.set(virtual, text);
    owners.set(virtual, {id: row.id, file: p});
  }
}
  const options = { noEmit: true, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.Preserve, skipLibCheck: true, noResolve: true, allowJs: true, checkJs: true, module: ts.ModuleKind.ESNext, moduleDetection: ts.ModuleDetectionKind.Force };
  const base = ts.createCompilerHost(options);
  const allowedLib = p => path.resolve(p).startsWith(libRoot + path.sep);
  const host = {
    ...base,
    fileExists: p => files.has(path.resolve(p)) || (allowedLib(p) && base.fileExists(p)),
    readFile: p => files.get(path.resolve(p)) ?? (allowedLib(p) ? base.readFile(p) : undefined),
    getSourceFile: (p, languageVersion) => {
      const text = files.get(path.resolve(p)) ?? (allowedLib(p) ? base.readFile(p) : undefined);
      return text === undefined ? undefined : ts.createSourceFile(p, text, languageVersion, true);
    },
    writeFile: () => { throw new Error('Emission prohibited'); },
  };
  const program = ts.createProgram([...files.keys()], options, host);
  for (const p of files.keys()) {
    const issues = [];
    const source = program.getSourceFile(p);
    result.checked_files++;
    const syntax = program.getSyntacticDiagnostics(source);
    const selected = syntax.length ? syntax : program.getSemanticDiagnostics(source).filter(d => [2304, 2552, 2448, 2451].includes(d.code));
    for (const d of selected) {
      const loc = source.getLineAndCharacterOfPosition(d.start ?? 0);
      issues.push({file: owners.get(p).file, line: loc.line + 1, code: d.code, text: ts.flattenDiagnosticMessageText(d.messageText, ' ')});
    }
    if (issues.length) (result.records[owners.get(p).id] ??= []).push(...issues);
  }
fs.mkdirSync(path.dirname(output), {recursive: true});
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
process.stdout.write(JSON.stringify({files: result.checked_files, records_with_errors: Object.keys(result.records).length, version: ts.version}) + '\n');
