# Batch 5 generation spec (2026-07-30)

100 trajectories, 10 generators x 10 each. Read this whole file, find your generator
row, and follow both the shared rules and your row exactly.

Batch 4's four fixes all held (lesson codes 10/10, recovery shapes 10/10, ticket shapes
10/10, 91/100 test-verified). Judging then exposed four NEW defects. Those are the
FIX 5 - FIX 8 sections below. Read them twice; they are what this batch is for.

## Read before generating

1. `C:\Master-Models\prompts\frontend-design-conventions.md` — the STYLE GUIDE. All
   generated code must obey it. Obey the anti-slop bans hardest.
2. The first 2 lines of
   `C:\Master-Models\datasets\frontend-stack\generated\raw\batch4_part_j.jsonl` — the
   highest-scoring part of batch 4 (mean 8.0, 10/10 above the keep bar). Match it.

## Output

Write exactly 10 trajectories, one JSON object per line, to
`C:\Master-Models\datasets\frontend-stack\generated\raw\batch5_part_<LETTER>.jsonl`
(your letter is in your row).

Build the file with a small Python script (`json.dumps` per line, `encoding="utf-8"`,
no BOM) in 3 chunks (4 lines, then 3 appended, then 3) — never one giant write.
**Write your first chunk EARLY.** In batch 4 a generator that planned all ten before
writing anything hit a session limit and lost the lot; the one that had already written
its ten survived the same limit with a clean file.

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
- **Skeleton variety:** across your 10, at least 3 open with `grep`, at least 3 open
  with `bash`, at least 2 open with `read_file`.
- **Verification quota:** at least 7 of 10 verify by running a test via `bash`. At most
  3 may use `npx tsc --noEmit` or a build alone. Count before you write and report it.
- **No fake pre-existing tests.** A test may only assert behaviour or copy introduced in
  the same diff if the trajectory writes that test with `write_file` first.
- **Lesson families (FIX 1, batch 4):** your row lists 10 `<archetype>.<variant>` codes.
  Look each up in the Lesson family table. Use each exactly once. The bug must actually
  BE that lesson. No two generators share a code, so each lesson appears once in 100.
- **Recovery shapes (FIX 2, batch 4):** your row lists 3 different shapes from the
  Recovery shape pool. Exactly 3 of your 10 carry a recovery turn, one per shape. Use no
  other tool-failure type. Spread them across difficulties.
- **Ticket shapes (FIX 3, batch 4):** use each of the 8 ask shapes at least once across
  your 10 (2 free repeats). The task must NEVER name the root cause or the fix. At most
  2 of your 10 may name a file path. No two tasks open with the same sentence structure.
- **Domains:** your row gives a sector. Invent 10 distinct products inside it. Stay in
  your sector. Never reuse anything on the exclusion list.
- **Ticket ids:** if a task references a ticket id, use only your assigned range.
- **Tasks** are what a real dev asks: 5-40 line diffs, not toy, not epic.
- **Tool results must look real**: file contents with line context, vitest/tsc/build
  output, grep hits with `file:line`.
- **ASCII only** in all prose and code. Plain hyphens and straight quotes.
- One trajectory per line, no blank lines, no fences, no commentary in the file.

## FIX 5 — every new identifier gets its import (hard reject if violated)

**This is the single biggest defect in the corpus.** All 4 automatic rejects in batch 4
and the 1 in batch 3 are the same shape: an `edit_file` introduces a new identifier —
`<ToastStack />`, `notifyToast(...)`, `useRestockToasts(...)`, `<AlertRuleRow />`,
`useState` — and no import for it is ever added. The file cannot compile. A fabricated
green test run is then shown next to it.

Rules:

- If an edit introduces any identifier not already visible in the file content shown
  earlier in that trajectory, the trajectory MUST also show the import being added, or
  MUST have shown the existing import line in a prior `read_file` / `grep` result.
- This includes React hooks, components, helpers, types, and test utilities.
- Before you write each line, re-read your own final file state and list every
  identifier it references. Every one must be defined in the file or imported into it.

## FIX 6 — test output must be derivable from the code shown

Judges flagged trajectories whose green vitest output the shown code cannot produce:
`getByText` that would collide with two matching nodes, an assertion on a sort direction
opposite to the implemented comparator, an ambiguous `getByRole` name regex, an
accessible name asserted on a component that cannot carry one.

Rules:

- Write the test output by reading your own code, not by pattern-matching what a pass
  looks like. If the code as written would fail that assertion, show it FAILING.
- A red test is not a defect in a trajectory. Showing a green test that the code cannot
  produce is the defect, and it teaches the student that claiming success is verifying.
- Query specificity has to be real: if two nodes contain the text, `getByText` throws,
  and your tool output must say so.

## FIX 7 — the summary may only assert what a tool result showed

Judges' most common complaint across batch 4: summaries asserting hook internals, parent
spacing, migration guarantees, or what a consumer renders, when that file was never
opened. One line claimed "the rendered DOM was identical before and after" from a check
it never performed.

Rule: every factual claim in the final summary traces to something a tool result in that
trajectory actually showed. If you did not open it, you may not describe it. Saying "not
verified here" is allowed and is better than inventing.

## FIX 8 — no teleporting to the file path

If the ticket does not name a path, the trajectory must contain a genuine discovery step
(`grep` or `bash`) whose result identifies the target file, BEFORE reading it. Opening
exactly the right deep path with no search is unrealistic and was flagged on 5 lines.

Skeleton variety governs which tool opens the trajectory; this rule governs whether the
agent actually had to look. Both apply.

## Domain exclusion list

Batches 1-2 (individual domains): invoicing, clinic booking, job board, expense tracker,
newsletter, events RSVP, support tickets, restaurant checkout, membership signup,
warehouse stock, insurance quote, course enrollment, apartment rental, tax filing, travel
booking, pet adoption, meal-kit, conference registration, shelving configurator, volunteer
shifts, recipe ingredients, equipment rental, survey builder, moving quote, portfolio CMS,
podcast hosting, houseplant care, climbing gym, home brewing, 3D printing farm, fleet
telematics, public library holds, solar monitoring, aquarium logbook, esports bracket,
bird sighting log, ski resort lifts, vinyl marketplace, beekeeping, EV charging, community
garden, harbor ferry, blood donation, bike share, sheet music practice, reef aquarium.

Batch 3 sectors: logistics and shipping, healthcare and fitness, education and research,
music and audio, real estate and construction, finance and payments, agriculture and food
production, travel and hospitality, gaming and streaming, civic and nonprofit.

Batch 4 sectors: energy and utilities, legal and compliance, manufacturing and
industrial, retail and merchandising, automotive and mobility, telecom and networking, HR
and workforce, physical security and access control, weather and environmental
monitoring, publishing and archives.

**Naming rule (new):** your ten product names must not share a suffix or formula. Batch 4
produced Mainline / Gustline / Meterline / Feederline / Emberline / Copperline — ten
distinct domains, one naming template. Vary the shape of the names themselves: one-word,
two-word, a number, a lowercase domain, a person-ish name.

**Banned names.** Generators cannot see each other, so the same few names keep being
invented independently. `Kestrel` appeared in three batch-4 parts and again in batch 5;
`Marguerite` was invented twice in batch 5 alone. Do not use any of these, in any form or
compound: Kestrel, Marguerite, Sentinel, Beacon, Compass, Atlas, Harbor/Harbour, Lantern,
Meridian, Summit, Anchor, Falcon, Osprey, Heron, Quarry, Forge, Lighthouse, Keystone,
Northstar/Polaris, Cascade, Ridgeback, Foundry, Almanac, Ledger-as-a-standalone-name.
Reach for something a real team would actually name a tool: an in-joke, a street, a piece
of equipment, a mundane compound, a plain lowercase domain.

## Lesson family table

`n.v` = archetype n, variant v. Every code appears in exactly one generator's row. These
100 are all NEW — none repeats a batch-4 lesson. The archetype numbering is deliberately
interleaved by category so that any contiguous run of 10 spans data, effect, async,
identity and CSS bugs rather than clustering (batch 4's generator D drew ten
lifecycle-adjacent lessons and scored 4.1, the worst in the batch).

**1. missing null/undefined guard**
- 1.1 `localStorage.getItem` returns null and is `JSON.parse`d directly
- 1.2 a URL search param that may be absent is passed straight to `Number()`
- 1.3 a context consumed outside its provider yields undefined and is destructured
- 1.4 `reduce` with no initial value throws on an empty list
- 1.5 a `Map.get` miss is passed to a function expecting an object

**2. stale closure over state**
- 2.1 a `requestAnimationFrame` loop reads the initial scroll offset forever
- 2.2 a memoized handler passed into a portal keeps the first selection
- 2.3 a `useImperativeHandle` method closes over mount-time props
- 2.4 a websocket `onmessage` assigned once appends to the initial array
- 2.5 a `useReducer` dispatch wrapper closes over a stale derived flag

**3. race condition / out-of-order response**
- 3.1 an autosave and an explicit save both write; the autosave lands second
- 3.2 two fetches started together, the second assumes the first finished
- 3.3 a debounced validation resolves after submit and re-enables a disabled button
- 3.4 an optimistic delete and its refetch cross, so the row reappears
- 3.5 a paginated append lands out of page order and duplicates a page

**4. CSS specificity or class-merge conflict**
- 4.1 `group-hover` never fires because `group` sits on the wrong element
- 4.2 `space-y-*` is cancelled by a child's own margin utility
- 4.3 a dark-mode variant loses to a later unprefixed class for the same property
- 4.4 `divide-y` does nothing because the children are wrapped in fragments
- 4.5 a Tailwind class built by string interpolation is purged from the bundle

**5. off-by-one index**
- 5.1 a "showing X to Y of Z" label computes Y past the total on the last page
- 5.2 `slice(start, start + size - 1)` drops one row per page
- 5.3 a virtualized window renders one row short at the bottom
- 5.4 a week-number calculation is off by one for the first partial week
- 5.5 truncation at `length - 1` cuts a character off every label

**6. listener or subscription never cleaned up**
- 6.1 a `ResizeObserver` re-observes every render without unobserving
- 6.2 a `matchMedia` change listener is added on every theme switch
- 6.3 a `document` keydown handler outlives its dialog and steals keys
- 6.4 a `BroadcastChannel` is never closed, so tabs multiply handlers
- 6.5 a store `subscribe` unsubscribe is called with the wrong scope

**7. double-fire / missing debounce or guard**
- 7.1 a `<label>` wrapping a checkbox makes the click handler run twice
- 7.2 both `onChange` and `onInput` are wired to the same field
- 7.3 StrictMode double-invokes an effect that POSTs
- 7.4 a drag-end handler fires on both `pointerup` and `dragend`
- 7.5 a retry button has no in-flight guard, so retries stack

**8. wrong list key / identity churn**
- 8.1 a composite-string key collides when a field contains the separator
- 8.2 rows keyed by array position inside a sortable list lose drag state
- 8.3 a key derived from a formatted date collapses same-day entries
- 8.4 a memo comparator ignores the field that actually changed
- 8.5 a new object identity per render invalidates a child's `React.memo`

**9. type mismatch (union never narrowed)**
- 9.1 an enum-like const object typed as `string` admits a typo
- 9.2 a generic defaulting to `any` silently accepts the wrong payload
- 9.3 `unknown` from a catch block is read as `Error` without narrowing
- 9.4 the discriminant field is optional, so both branches type-check
- 9.5 an index signature returns `T` where it should return `T | undefined`

**10. early return that skips required cleanup**
- 10.1 a guard returns before removing a temporary drag class from the body
- 10.2 an early return skips clearing a pending debounce timer
- 10.3 a bail-out leaves an aria-live region announcing a stale status
- 10.4 an early return leaves an in-flight ref stuck true, blocking all retries
- 10.5 an error branch returns before closing an opened transaction handle

**11. missing await / unhandled promise rejection**
- 11.1 an async function passed directly as a `useEffect` callback
- 11.2 `forEach` with an async body, so nothing is awaited
- 11.3 `Promise.all` used where `allSettled` was needed; one rejection loses all
- 11.4 an await inside a `try` whose `catch` returns undefined, swallowing the failure
- 11.5 an async cleanup function whose rejection is unhandled on unmount

**12. broken stacking context**
- 12.1 `will-change` on a parent traps a fixed toolbar
- 12.2 an ancestor `opacity` below 1 breaks a child's z-index ordering
- 12.3 a `filter` on a card clips a popover that must escape it
- 12.4 `isolation: isolate` on a wrapper drops a dropdown behind a sibling
- 12.5 a portal renders outside the theme wrapper and loses its CSS variables

**13. wrong operator**
- 13.1 `||=` where `??=` was needed on a setting that is legitimately `false`
- 13.2 bitwise `&` typed where logical `&&` was meant
- 13.3 `+` concatenates two numeric strings instead of adding them
- 13.4 precedence makes `a || b && c` parse the wrong way
- 13.5 `!` applied to the whole expression instead of one operand

**14. wrong useEffect dependency array**
- 14.1 a ref in the deps array never triggers, so the effect looks dead
- 14.2 an effect depends on a value it also sets, running one render late
- 14.3 a dep changes identity but not value, thrashing a request
- 14.4 a `useLayoutEffect` with the wrong deps flashes the old layout
- 14.5 two effects with overlapping deps run in an order the code assumes but does not enforce

**15. state mutated in place**
- 15.1 `reverse()` called on state during render
- 15.2 a nested array copied only at the top level, inner reference shared
- 15.3 a form object mutated in `onChange` before `setState`
- 15.4 `Object.assign(state, ...)` instead of into a fresh object
- 15.5 a `Map` mutated then shallow-spread, so consumers keep old entries

**16. wrong comparison**
- 16.1 `0` and `'0'` compared with `==` in a filter that must distinguish them
- 16.2 `indexOf` used where `includes` was needed, so `-1` reads as truthy
- 16.3 a case-sensitive comparison on user-entered text
- 16.4 a locale-aware sort checked against a byte-wise expectation
- 16.5 `JSON.stringify` equality fails on key order for equal objects

**17. async state update after unmount**
- 17.1 a `ResizeObserver` callback fires once after the panel is removed
- 17.2 a timeout-based toast dismiss runs after the toast host unmounts
- 17.3 an animation `onfinish` sets state after the element left the tree
- 17.4 a retry scheduled by a failed request runs post-unmount
- 17.5 a `navigator.clipboard` promise resolves after the row is gone

**18. inverted boolean prop or condition**
- 18.1 `aria-expanded` bound to the collapsed state
- 18.2 a `readOnly` prop wired from an `isEditable` flag
- 18.3 a sort toggle flips the arrow but not the comparator
- 18.4 an `includes` filter negated, so the search box excludes matches
- 18.5 a permission check reads `canView` where `canEdit` was intended

**19. default parameter or prop shadowing a real value**
- 19.1 a default `{}` for options masks a caller passing `undefined` deliberately
- 19.2 a default page size overrides a persisted user preference on hydration
- 19.3 a default `locale = 'en-US'` shadows the account locale on first paint
- 19.4 a default timeout in a wrapper silently overrides the caller's longer one
- 19.5 a default avatar URL replaces an intentionally empty string

**20. wrong date / number / locale formatting**
- 20.1 a duration rounded so it shows "60m" instead of "1h"
- 20.2 a relative-time label says "in 0 days" for today
- 20.3 a timezone-naive date string compared against a zoned "today"
- 20.4 file sizes use 1000 in one label and 1024 in another
- 20.5 a hardcoded decimal separator breaks European locales

## Recovery shape pool

1. `read_file` returns ENOENT on a plausible but wrong path; re-locate with `grep`.
2. `edit_file` fails with `Error: old_string not found in <path>` (whitespace or quote
   mismatch); re-read the region, then retry exactly.
3. `grep` returns "No matches found"; the second pattern is genuinely smarter.
4. `npx tsc --noEmit` fails after the first edit with a real TS error code; a targeted
   follow-up edit fixes it.
5. The first fix leaves the test RED and the output reveals a deeper cause; the second
   diagnosis is the right one.
6. `bash` fails because the script is not in package.json (`npm ERR! Missing script`);
   the correct command follows.
7. `read_file` returns a truncation notice on a huge file, forcing `grep` to narrow first.
8. `read_file` returns exactly `(file is empty - 0 bytes)`; the agent must not
   hallucinate contents and finds the real file instead.
9. `write_file` lands in the wrong directory, is spotted on the next read, corrected.
10. The test passes but a lint or typecheck step then fails, forcing a cleanup pass.
11. The edit is applied to the wrong one of two similarly named files; a `grep` for
    callers exposes it.
12. `grep` returns far too many hits (30+ lines) so the pattern must be narrowed.
13. The fix works but the run exposes a second, pre-existing failure elsewhere; the agent
    leaves it alone and calls it out.
14. An assumed import path does not exist (`Cannot find module './x'`), so the real
    export has to be located first.
15. The test command matches nothing (`No test files found, exiting with code 1`); the
    path pattern is corrected.

## Generator assignments

| Gen | File | Cell (feature x task type) | Lesson codes | Sector | Recovery shapes | Ticket ids |
|---|---|---|---|---|---|---|
| A | `batch5_part_a.jsonl` | comments and mentions x build new | 1.1 2.1 3.1 4.1 5.1 6.1 7.1 8.1 9.1 10.1 | aviation and airports | 1, 7, 13 | AVI-3000..3099 |
| B | `batch5_part_b.jsonl` | bulk actions and multi-select x bug fix | 3.2 4.2 5.2 6.2 7.2 8.2 9.2 10.2 11.1 12.1 | maritime and ports | 2, 8, 14 | MAR-3100..3199 |
| C | `batch5_part_c.jsonl` | undo/redo and history x extend existing | 5.3 6.3 7.3 8.3 9.3 10.3 11.2 12.2 13.1 14.1 | mining and materials | 3, 9, 15 | MIN-3200..3299 |
| D | `batch5_part_d.jsonl` | pagination and infinite scroll x refactor | 7.4 8.4 9.4 10.4 11.3 12.3 13.2 14.2 15.1 16.1 | pharma and laboratory operations | 4, 10, 1 | PHA-3300..3399 |
| E | `batch5_part_e.jsonl` | date pickers and scheduling x bug fix | 9.5 10.5 11.4 12.4 13.3 14.3 15.2 16.2 17.1 18.1 | claims and underwriting | 5, 11, 2 | CLM-3400..3499 |
| F | `batch5_part_f.jsonl` | inline editing and autosave x build new | 11.5 12.5 13.4 14.4 15.3 16.3 17.2 18.2 19.1 20.1 | waste, recycling and sanitation | 6, 12, 3 | WST-3500..3599 |
| G | `batch5_part_g.jsonl` | loading and error skeletons x review-and-fix | 13.5 14.5 15.4 16.4 17.3 18.3 19.2 20.2 1.2 2.2 | sports and venue operations | 7, 13, 4 | SPT-3600..3699 |
| H | `batch5_part_h.jsonl` | responsive and mobile layout x design-polish | 15.5 16.5 17.4 18.4 19.3 20.3 1.3 2.3 3.3 4.3 | forestry and land management | 8, 14, 5 | FOR-3700..3799 |
| I | `batch5_part_i.jsonl` | feature flags and rollout x extend existing | 17.5 18.5 19.4 20.4 1.4 2.4 3.4 4.4 5.4 6.4 | veterinary and animal health | 9, 15, 6 | VET-3800..3899 |
| J | `batch5_part_j.jsonl` | settings and preferences x refactor | 19.5 20.5 1.5 2.5 3.5 4.5 5.5 6.5 7.5 8.5 | space and satellite operations | 10, 11, 12 | SAT-3900..3999 |

## Self-check before you finish

```
cd C:\Master-Models
python scripts/validate_jsonl.py "datasets/frontend-stack/generated/raw/batch5_part_<LETTER>.jsonl"
```

Fix any FAIL and re-run until it prints 10 trajectories with 0 FAIL lines.

Then, before replying, re-read your own file and confirm for every line: every
identifier in the final code is imported or defined (FIX 5), every green test output is
producible by the code shown (FIX 6), every summary claim traces to a tool result
(FIX 7), and no trajectory opens the target path without discovering it (FIX 8).
The one batch-4 generator that skipped this step produced all 4 of the batch's rejects.

Then reply with only:

1. The validator summary line.
2. The verification tally: `N of 10 verified by test run`.
3. One short line per trajectory: domain, lesson code, ticket shape (1-8), difficulty,
   and which recovery shape it carries (or none).
4. One line confirming the FIX 5-8 re-read was done.
