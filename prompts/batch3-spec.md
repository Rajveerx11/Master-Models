# Batch 3 generation spec (2026-07-28)

100 trajectories, 10 generators x 10 each. Read this whole file, find your generator
row, and follow both the shared rules and your row exactly.

## Read before generating

1. `C:\Master-Models\prompts\frontend-design-conventions.md` — the STYLE GUIDE. All
   generated code must obey it. Obey the anti-slop bans hardest.
2. The first 2 lines of
   `C:\Master-Models\datasets\frontend-stack\generated\raw\batch2_part_d.jsonl` — the
   gold format and quality bar. Match it exactly.

## Output

Write exactly 10 trajectories, one JSON object per line, to
`C:\Master-Models\datasets\frontend-stack\generated\raw\batch3_part_<LETTER>.jsonl`
(your letter is in your row).

Build the file with a small Python script (`json.dumps` per line, `encoding="utf-8"`,
no BOM) in 3 chunks (4 lines, then 3 appended, then 3) — never one giant write.

## Schema (the validator enforces this exactly)

```
{"messages":[
 {"role":"system","content":"You are a coding agent with tools: read_file, write_file, edit_file, bash, grep."},
 {"role":"user","content":"<realistic task>"},
 {"role":"assistant","tool_calls":[{"name":"grep","arguments":{...}}]},
 {"role":"tool","name":"grep","content":"<realistic result>"},
 ... ,
 {"role":"assistant","content":"<final summary>"}
]}
```

- The system string must be byte-identical to the one above.
- Only these tools: `read_file`, `write_file`, `edit_file`, `bash`, `grep`.
- Every assistant `tool_calls` message is immediately followed by a `tool` message
  with the SAME name. `arguments` is always a JSON object.
- Last message: assistant summary with `content` and NO `tool_calls`.
- `edit_file` takes `{"path","old_string","new_string"}` and `old_string` must appear
  verbatim in file content shown earlier in that same trajectory.
- File contents stay self-consistent across turns.
- 3-8 tool turns per trajectory (see your difficulty mix).

## Shared rules (all generators)

- **Stack:** React 18 + TypeScript + Tailwind.
- **Difficulty mix per generator:** 3 easy (3-4 tool turns), 4 medium (5-6), 3 hard (7-8).
- **Archetypes:** your row lists 10 bug/issue archetypes. Use each **exactly once**
  across your 10 trajectories. Do not invent extras, do not repeat one.
- **Skeleton variety:** across your 10, at least 3 open with `grep`, at least 3 open
  with `bash`, at least 2 open with `read_file`.
- **Verification:** at least 6 of 10 verify by running a test via `bash` with realistic
  output. The rest may use `npx tsc --noEmit` or a build command.
- **Recovery:** your row assigns ONE tool-failure mode. Use it in exactly 3 of your 10,
  made to look different each time. Use no other tool-failure type.
- **HARD RULE — no fake pre-existing tests.** A test may only assert behaviour or copy
  introduced in the same diff if the trajectory itself writes that test with
  `write_file` first. Otherwise the test must assert behaviour that already existed.
- **Domains:** your row gives you a sector. Invent 10 distinct products inside it. Never
  reuse a domain from the exclusion list below, and stay inside your sector so no two
  generators collide.
- **Ticket ids:** if a task references a ticket id, use only your assigned range.
- **Tasks** are what a real dev asks: 5-40 line diffs, not toy, not epic. Vary phrasing
  (bug report, QA ticket, Slack message, terse one-liner, design review note).
- **Vary** file paths, component names, and project shape per trajectory.
- **Tool results must look real**: file contents with line context, vitest/tsc/build
  output, grep hits with `file:line`.
- **ASCII only** in all prose and code. No em dashes, smart quotes, checkmarks, arrows,
  or emoji. Plain hyphens and straight quotes.
- One trajectory per line, no blank lines, no markdown fences, no commentary in the file.

## Domain exclusion list (already used in batches 1-2)

invoicing, clinic booking, job board, expense tracker, newsletter, events RSVP, support
tickets, restaurant checkout, membership signup, warehouse stock, insurance quote, course
enrollment, apartment rental, tax filing, travel booking, pet adoption, meal-kit,
conference registration, shelving configurator, volunteer shifts, recipe ingredients,
equipment rental, survey builder, moving quote, portfolio CMS, podcast hosting, houseplant
care, climbing gym, home brewing, 3D printing farm, fleet telematics, public library holds,
solar monitoring, aquarium logbook, esports bracket, bird sighting log, ski resort lifts,
vinyl marketplace, beekeeping, EV charging, community garden, harbor ferry, blood donation,
bike share, sheet music practice, reef aquarium.

## Archetype pool

1. missing null/undefined guard
2. off-by-one index
3. wrong operator (`&&` vs ternary, `||` vs `??`, `>` vs `>=`)
4. stale closure over state
5. race condition / out-of-order response
6. type mismatch (union never narrowed)
7. wrong useEffect dependency array
8. state mutated in place instead of copied
9. wrong list key / identity churn
10. listener or subscription never cleaned up
11. double-fire / missing debounce or guard
12. broken stacking context (z-index / overflow / transform)
13. early return that skips required cleanup
14. async state update after unmount
15. wrong comparison (object identity, NaN, empty string)
16. missing await / unhandled promise rejection
17. CSS specificity or class-merge conflict
18. inverted boolean prop or condition
19. default parameter or prop shadowing a real value
20. wrong date / number / locale formatting

## Generator assignments

| Gen | File | Cell (feature x task type) | Archetypes | Sector | Recovery mode | Ticket ids |
|---|---|---|---|---|---|---|
| A | `batch3_part_a.jsonl` | tables & lists x build new | 1-10 | logistics & shipping | `read_file` ENOENT on a wrong path, then re-locate | LOG-1000..1099 |
| B | `batch3_part_b.jsonl` | modals & overlays x bug fix | 3-12 | healthcare & fitness | `edit_file` fails: "Error: old_string not found in <path>" (whitespace/quote mismatch), then re-read and retry exactly | HF-1100..1199 |
| C | `batch3_part_c.jsonl` | routing & navigation x extend existing | 5-14 | education & research | `grep` returns "No matches found", then a genuinely smarter second pattern | EDU-1200..1299 |
| D | `batch3_part_d.jsonl` | animation & motion x design-polish | 7-16 | music & audio | `npx tsc --noEmit` fails after the first edit with a real TS error code, then a targeted follow-up edit | AUD-1300..1399 |
| E | `batch3_part_e.jsonl` | file uploads & media x bug fix | 9-18 | real estate & construction | the first fix leaves the test RED and the output reveals a deeper cause; second, better diagnosis fixes it | RE-1400..1499 |
| F | `batch3_part_f.jsonl` | optimistic updates x extend existing | 11-20 | finance & payments | `bash` fails: script not in package.json / command not found, then the correct command | FIN-1500..1599 |
| G | `batch3_part_g.jsonl` | virtualization & performance x refactor | 13-20, 1-2 | agriculture & food production | `read_file` returns a truncation notice on a huge file, forcing `grep` to narrow the region first | AGR-1600..1699 |
| H | `batch3_part_h.jsonl` | i18n & formatting x review-and-fix | 15-20, 1-4 | travel & hospitality | `read_file` returns exactly "(file is empty - 0 bytes)" and the agent must not hallucinate contents | TRV-1700..1799 |
| I | `batch3_part_i.jsonl` | realtime & websockets x bug fix | 17-20, 1-6 | gaming & streaming | `write_file` to the wrong directory, spotted on the next read, then corrected | GAM-1800..1899 |
| J | `batch3_part_j.jsonl` | onboarding & empty states x build new | 19-20, 1-8 | civic & nonprofit | test passes but a lint/typecheck step then fails, forcing a cleanup pass | CIV-1900..1999 |

Archetype ranges are inclusive and refer to the numbered pool above. Each archetype
appears in 5 different cells across the batch, never twice inside one generator.

## Self-check before you finish

```
cd C:\Master-Models
python scripts/validate_jsonl.py "datasets/frontend-stack/generated/raw/batch3_part_<LETTER>.jsonl"
```

Fix any FAIL and re-run until it prints 10 trajectories with 0 FAIL lines.

Then reply with only: the validator summary line, and one short line per trajectory —
domain, archetype used, difficulty, and whether it carries the recovery turn.
