# Evaluation protocol

Evaluation is the release boundary. Model outputs are judged by repository-task
completion, not answer similarity or author preference.

## Frozen-set rules

1. Tasks are committed before production dataset generation.
2. Frozen tasks never change. Corrections create a versioned successor set.
3. No task wording, paraphrase, reference diff, or solution fragment enters training.
4. Tasks come from real repository history, not synthetic teacher output.
5. Every arm starts from the same recorded commit and uses the same harness settings.
6. Results are committed whether the specialist wins, loses, or invalidates the run.

Historical exception: batches 1 and 2 were pilots created before the frontend eval
freeze. Eval tasks were mined later from private repository history, preventing task
leakage. This deviation remains recorded in `plan/v1-release-plan.md`.

## Frozen frontend set

Status: **frozen 2026-07-28**, commit `f2fb8f1`.

- 20 tasks
- 5 easy / 9 medium / 6 hard
- 17 from `terax-ai`
- 3 from Testing IDE / Tessera
- each task records source repository, reference commit, start revision, verbatim agent
  prompt, checkable success criteria, and graders-only reference evidence

Backend-stack and code-review evals remain deferred.

## Three required arms

| Arm | Model | Primary comparison |
|---|---|---|
| A | trained frontend-stack Qwen3-8B Q4_K_M | candidate |
| B | stock Qwen3-8B Q4_K_M | training effect: A versus B |
| C | stock Qwen3-Coder-30B-A3B Q4_K_M | size competitiveness: A versus C |

Arm B is mandatory. A two-arm A-versus-C test cannot distinguish ineffective training
from an ordinary 8B-versus-30B size gap.

## Qualification before gate

Candidate A must pass:

- local byte count, `GGUF` header, and SHA-256 match against Colab artifact metadata;
- llama-server template verification with normalized prompt match;
- guard-proxy unit tests;
- 10/10 post-export smoke test through the served stack.

Full commands and prerequisites: `training/README.md`.

## Gate execution

`scripts/run_gate.py` runs one arm. It creates an isolated depth-1 repository for each
task at the recorded start commit, installs frozen dependencies, invokes Neura/pi,
archives logs and patches, records tool metrics, runs TypeScript checking, and leaves
grading to the evaluator. Source repositories remain untouched.

Recommended ports:

- guard proxy: `127.0.0.1:18080`
- llama-server: `127.0.0.1:18081`

Example after serving the arm-A model and starting the proxy:

```powershell
$modelPath = (Resolve-Path 'outputs\frontend-stack\gguf\frontend-stack-qwen3-8b-q4_k_m.gguf').Path
python scripts/run_gate.py --arm A --tasks all --model-path $modelPath --server-url http://127.0.0.1:18080
```

Repeat for B and C only after relaunching llama-server with that arm's exact model.
Use the same Neura configuration for all arms.

## Scoring and report

For every task and arm, record:

- `pass`, `partial`, or `fail` against frozen success criteria;
- verification/test evidence;
- tool-call count and validity;
- right-tool use;
- tool errors and malformed stream lines;
- relevant failure notes.

Write one consolidated result:
`evals/results/<date>-frontend-stack-vs-baseline.md`.

Read A versus B first. Tool validity for A materially below B invalidates capability
comparison and triggers train/serve diagnosis. Then read A versus C. Exact decision
matrix: `plan/v1-release-plan.md`.

## Layout

```text
evals/
  tasks/frontend-stack/   Frozen 20-task set
  tasks/backend-stack/    Deferred placeholder
  tasks/code-review/      Deferred placeholder
  results/                Historical probes and final gate report
```
