# train.jsonl — build manifest

Built by `python scripts/build_train_mix.py` (seed 731). Rebuilding is deterministic;
`--demo` runs the shape assertions without writing.

## Composition — 404 records

| Source | Records | Share | Licence | Role |
|--------|--------:|------:|---------|------|
| `frontend-stack` (our `filtered/keep_ge7.pi.jsonl`) | 242 | 60% | private | the specialism |
| `NousResearch/hermes-function-calling-v1` | 81 | 20% | Apache-2.0 | general tool-calling |
| `databricks/databricks-dolly-15k` | 81 | 20% | CC-BY-SA-3.0 | general instruction |

Split: **384 train / 20 holdout**, stratified 5% per source so the holdout is not
accidentally all one kind. The holdout is for loss tracking only — it is **not** the
frozen eval in `evals/tasks/frontend-stack/`.

## Licence check (HF datasets API, 2026-07-31)

Accepted above. Rejected, with reasons:

| Candidate | Declared licence | Why not |
|-----------|------------------|---------|
| `teknium/OpenHermes-2.5` | none declared | no licence to rely on, plus GPT-4-distilled content |
| `HuggingFaceTB/smoltalk` | none declared | no licence to rely on |
| `HuggingFaceH4/no_robots` | CC-BY-NC-4.0 | non-commercial only |
| `allenai/tulu-3-sft-mixture` | ODC-BY | clean, but 939k rows across shards and mixed distilled subsets — dolly is one file and human-written |

Dolly is human-written by Databricks employees, so it carries no model-output terms-of-use
question the way distilled corpora do. CC-BY-SA-3.0 share-alike attaches to the dataset;
attribution is recorded here.

## Record shape

```json
{"messages": [...], "tools": [...], "source": "frontend-stack"}
```

- `tools` is **pi's real tool array** (`training/pi_tools.json`, regenerate with
  `node scripts/dump_pi_tools.mjs`) on the 242 domain records, and the example's own
  tools on Hermes records. Dolly records carry **no** `tools` — deliberate, it keeps
  plain-chat ability alive.
- The training formatter must consume `messages` + `tools` and ignore `source`.
- Do **not** run `validate_jsonl.py --pi` on this file. Hermes records legitimately call
  non-pi tools; `--pi` is for `keep_ge7.pi.jsonl` only.

## Shape decisions, and the evidence behind them

**`tools` was the actual missing piece.** pi sends tool schemas as the request's
top-level `tools` field (`pi-ai/dist/api/openai-completions.js` → `convertTools`), and
`llama-server --jinja` renders them into the prompt. The corpus had no `tools` field at
all, so the model would have trained without the `<tools>` block it sees at serve time.

**`tool_calls` stay flat — `{"name", "arguments"}`, not OpenAI's nested form.** The
Qwen3-8B template unwraps `.function` when present, reads `.name`/`.arguments`
otherwise, and ignores `id` / `tool_call_id` entirely. Both shapes render byte-identical;
`demo()` asserts it. Restructuring would have been churn with no effect on the trained text.

**`arguments` stays a dict, not a JSON string.** The template branches on
`arguments is string`, so both render — but `llama.cpp` parses the wire string into an
object before templating, so a dict is what the server-side template actually sees.

**Hermes was re-shaped, not used raw.** It encodes calls as `<tool_call>` XML inside
message text with its own `<tools>` system prompt. Training on that teaches a syntax
that competes with Qwen3's. Its tools moved to the `tools` field and its calls became
real `tool_calls`; the build asserts no raw `<tool_call>`/`<tool_response>` markers
survive. 65 of the scanned records were dropped for unparseable call/response JSON.

**The system prompt gained `find` and `ls`.** The corpus listed the five tools it uses;
pi presents seven. Snippets are the first sentence of pi's own tool descriptions. Neura
**appends** to pi's system prompt (`event.systemPrompt + persona`) rather than replacing
it, so pi's stable core is the right training target — volatile parts (Neura persona,
memory, doc paths, cwd, skills catalog) stay out on purpose.

## T4-safe bounded derivative

The 404-record source corpus remains frozen as 384 train / 20 holdout. Colab training
uses a deterministic whole-record derivative capped at **4,096 rendered tokens**:

| Split | Source | Retained | Dropped over cap | Rendered range |
|---|---:|---:|---:|---:|
| Train | 384 | 328 | 56 | 27–4,069 |
| Holdout | 20 | 18 | 2 | 88–3,914 |

Bounded train composition is 174 frontend-stack, 77 Hermes, and 77 Dolly records.
This retains 174/230 source-train domain records, or 53.0% of the bounded set. The
holdout remains validation-only and never moves into training.

`scripts/build_short_train.py` renders with the pinned template, counts the TRL
terminal token, rejects over-cap records whole, checks train/holdout non-overlap, and
writes `train-short4096.manifest.json`. That JSON manifest is authoritative for source,
template, and output hashes.

The approved run is the self-contained Colab notebook, not local QLoRA. Notebook
SHA-256: `87355EDDA48F2425AADB2698B505685020CDAECB618B9EF8AEDBBEF6C6FCAE86`.

## Residual risk carried forward

- ~10% of the 242 domain trajectories (batches 1–4, pre-FIX 6/7) assert verification
  they never performed. If the specialist confidently claims unverified results, this is
  the first suspect — not the tool schema and not the template.
- Prompt whitespace: transformers' Jinja `tojson` emits `{"path": "a"}` while llama.cpp's
  minja/nlohmann emits `{"path":"a"}`. This affects prior assistant turns in context, not
  parsing of fresh output. The real byte-match test must be run against `llama-server`
  itself, not against transformers.
