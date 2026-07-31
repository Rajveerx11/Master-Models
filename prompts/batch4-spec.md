# Batch 4 generation spec (2026-07-30)

100 trajectories, 10 generators x 10 each. Read this whole file, find your generator
row, and follow both the shared rules and your row exactly.

This is batch 3's contract with four hard changes, driven by measured batch-3 failures:
a batch-wide **lesson-family** ledger (not just archetype), **three different recovery
shapes** per generator, **eight required ticket shapes**, and a **verification quota you
must count before writing**. Read those four sections twice.

## Read before generating

1. `C:\Master-Models\prompts\frontend-design-conventions.md` — the STYLE GUIDE. All
   generated code must obey it. Obey the anti-slop bans hardest.
2. The first 2 lines of
   `C:\Master-Models\datasets\frontend-stack\generated\raw\batch3_part_a.jsonl` — the
   gold format and quality bar. Match it exactly.

## Output

Write exactly 10 trajectories, one JSON object per line, to
`C:\Master-Models\datasets\frontend-stack\generated\raw\batch4_part_<LETTER>.jsonl`
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
- **Skeleton variety:** across your 10, at least 3 open with `grep`, at least 3 open
  with `bash`, at least 2 open with `read_file`.
- **HARD RULE — no fake pre-existing tests.** A test may only assert behaviour or copy
  introduced in the same diff if the trajectory itself writes that test with
  `write_file` first. Otherwise the test must assert behaviour that already existed.
- **Domains:** your row gives you a sector. Invent 10 distinct products inside it. Never
  reuse a domain from the exclusion list below, and stay inside your sector so no two
  generators collide.
- **Ticket ids:** if a task references a ticket id, use only your assigned range.
- **Tasks** are what a real dev asks: 5-40 line diffs, not toy, not epic.
- **Vary** file paths, component names, and project shape per trajectory.
- **Tool results must look real**: file contents with line context, vitest/tsc/build
  output, grep hits with `file:line`.
- **ASCII only** in all prose and code. No em dashes, smart quotes, checkmarks, arrows,
  or emoji. Plain hyphens and straight quotes.
- One trajectory per line, no blank lines, no markdown fences, no commentary in the file.

## FIX 1 — lesson families (the important one)

Batch 3 capped each *archetype* at once per generator. It did not stop the same
*lesson* recurring across the batch: `key={index}` 5x, class-merge 4x, default-param
shadowing 5x. So a lesson family is now assigned explicitly and is unique batch-wide.

Your row lists 10 codes of the form `<archetype>.<variant>`, e.g. `9.1`. Look each one
up in the **Lesson family table** below. That exact lesson is the root cause of exactly
one of your 10 trajectories. Rules:

- Use each of your 10 codes **exactly once**. Do not invent extras, do not repeat one.
- The bug in the code must actually BE that lesson — not a cousin of it.
- No two generators in this batch share a code, so a lesson family appears once in the
  whole 100. If two of your assigned lessons feel similar, they are not: write the
  mechanism the table names, precisely, and they will differ.
- Your final assistant summary must state the root cause in the lesson's own terms.

## FIX 2 — three different recovery shapes

Batch 3 gave each generator ONE failure mode used 3x, and the three came out nearly
identical. Your row now lists **three different recovery shapes**, numbered against the
**Recovery shape pool** below.

- Exactly 3 of your 10 trajectories carry a recovery turn: one per assigned shape.
- Use no other tool-failure type anywhere in your 10.
- Spread them across difficulties — do not put all three in the hard trajectories.

## FIX 3 — the ask itself must vary

Judge 1 on batch 3: nearly every prompt was the same "do X, and by the way bug Y
exists" shape. That shape is now **banned**. Instead, across your 10 tasks use each of
these eight shapes at least once (2 are free repeats of your choice):

1. **Symptom only.** What the user sees, no diagnosis. "The row I delete disappears but
   the one below it keeps my typed value."
2. **Verbatim customer quote** pasted in by support, including its imprecision.
3. **Failing CI log** pasted raw with no prose around it.
4. **Terse one-liner** from a lead. Under 12 words.
5. **Design review note** about spacing, contrast, motion, or copy.
6. **QA ticket**: repro steps, expected, actual.
7. **Slack thread fragment**, two people, mid-conversation.
8. **Plain feature ask** that never mentions a bug at all; the bug is what the agent
   finds while building it.

Hard constraints on every task text:

- The task must **never name the root cause or the fix**. No "the dependency array is
  wrong", no "use `??` here".
- At most 2 of your 10 tasks may name a file path.
- No two of your tasks may open with the same sentence structure.

## FIX 4 — verification quota, counted before you write

tsc-only verification survived at about a third of batch-3 lines despite the rule.

- **At least 7 of your 10** must verify by running a test via `bash`, with realistic
  pass/fail output (vitest, jest, jest-axe, playwright).
- **At most 3** may verify with `npx tsc --noEmit` or a build command alone.
- Before you write the file, tally the 10 and state the count in your reply. If the
  tally is under 7, rewrite the offending trajectories first, do not write the file.

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

Batch 3 (whole sectors — avoid all of them): logistics and shipping, healthcare and
fitness, education and research, music and audio, real estate and construction, finance
and payments, agriculture and food production, travel and hospitality, gaming and
streaming, civic and nonprofit.

## Lesson family table

Each row is one lesson family. `n.v` = archetype n, variant v. Every code appears in
exactly one generator's row.

**1. missing null/undefined guard**
- 1.1 optional chaining missing on a nested API field that is absent for new records
- 1.2 `Array.prototype.find` result used without checking for `undefined`
- 1.3 destructuring a prop that is undefined on the first render, before data loads
- 1.4 `Object.keys()` called on a nullable map from a partial response
- 1.5 a ref's `.current` read inside a handler that can run before the node mounts

**2. off-by-one index**
- 2.1 pagination computes `page * size` instead of `(page - 1) * size`
- 2.2 a `for` loop uses `<=` against `.length` and walks one past the end
- 2.3 arrow-key navigation wraps at `length` instead of `length - 1`
- 2.4 a step counter shows the 0-based index to the user ("Step 0 of 4")
- 2.5 a date range treats the end day as exclusive while the copy says inclusive

**3. wrong operator**
- 3.1 `||` swallows a legitimate `0`, where `??` was needed
- 3.2 `&&` renders a literal `0` instead of nothing for an empty count
- 3.3 `>` instead of `>=` drops the row sitting exactly on the threshold
- 3.4 `!==` between a numeric string and a number makes a check always true
- 3.5 `&&` used where a ternary was needed, so `false` lands in an attribute value

**4. stale closure over state**
- 4.1 a `setInterval` callback keeps the first render's counter value
- 4.2 a listener attached once reads a filter object from the initial render
- 4.3 a debounced submit sends the values from before the last keystroke
- 4.4 a `useCallback` with empty deps closes over an old page number
- 4.5 a `.then` after an `await` writes back state that was captured pre-await

**5. race condition / out-of-order response**
- 5.1 fast typing shows results for an earlier query (no abort or sequence guard)
- 5.2 two parallel saves land out of order and the older payload wins
- 5.3 a tab switch fires a fetch whose response applies to the newly selected tab
- 5.4 a retried request resolves after the fresh one and overwrites it
- 5.5 the initial load and a socket snapshot race, and the initial load lands last

**6. type mismatch (union never narrowed)**
- 6.1 a discriminated-union branch is accessed without checking the tag
- 6.2 a `string | number` id is compared against a `string` map key
- 6.3 a `Status` union widened to `string` by a `.map`, losing exhaustiveness
- 6.4 an optional field is treated as required immediately after `JSON.parse`
- 6.5 an `as` cast hides that the API returns `null` for a documented field

**7. wrong useEffect dependency array**
- 7.1 a missing dep means the effect never re-runs when the id changes
- 7.2 an object literal in the deps re-runs the effect on every render
- 7.3 a value derived from the same setter causes an infinite fetch loop
- 7.4 empty deps on a subscription that must follow a changing channel
- 7.5 a function dep recreated each render restarts a poll timer

**8. state mutated in place**
- 8.1 `.sort()` on the state array reorders it with no re-render
- 8.2 `.push` into a state array, so React sees no change
- 8.3 a nested object field assigned directly, so a memoized child never updates
- 8.4 `.splice` on what looks like a local list mutates the props array
- 8.5 a `Set` mutated with `.add`, then set back by the same reference

**9. wrong list key / identity churn**
- 9.1 `key={index}` makes an input's value follow the wrong row after a delete
- 9.2 a `Math.random()` key remounts every row on every render
- 9.3 duplicate ids from two merged sources collapse rows
- 9.4 the key is derived from a mutable field, so editing it remounts the row
- 9.5 the key sits on the wrapper fragment instead of the mapped element

**10. listener or subscription never cleaned up**
- 10.1 a `resize` listener added per render, so handlers pile up
- 10.2 an `EventSource` left open on unmount keeps reconnecting
- 10.3 an `IntersectionObserver` never disconnected leaks across route changes
- 10.4 a `setTimeout` never cleared fires after the dialog has closed
- 10.5 an `AbortController` is created but never aborted in cleanup

**11. double-fire / missing debounce or guard**
- 11.1 the submit button is never disabled, so two identical POSTs go out
- 11.2 an `onClick` on nested elements bubbles and fires twice
- 11.3 a form `onSubmit` and a `type="submit"` button handler both run
- 11.4 scroll-triggered loading fires again before the first request resolves
- 11.5 a shortcut handler fires on both the keydown and the keypress path

**12. broken stacking context**
- 12.1 a `transform` on an ancestor traps a `position: fixed` dropdown
- 12.2 `overflow-hidden` on a scroll container clips a tooltip
- 12.3 two layers in different stacking contexts, and the higher z-index loses
- 12.4 a sticky header inside an `overflow-auto` parent never sticks
- 12.5 a backdrop blur creates a context that hides the modal's close button

**13. early return that skips required cleanup**
- 13.1 a guard clause returns before clearing the loading flag
- 13.2 an early return inside an effect skips returning the unsubscribe
- 13.3 a validation bail-out leaves the progress bar stuck at its last value
- 13.4 an error path returns without revoking an object URL
- 13.5 a permission check returns before restoring the body scroll lock

**14. async state update after unmount**
- 14.1 a fetch resolving after navigation sets state on a dead component
- 14.2 an `await` in a submit handler continues after the modal closed
- 14.3 a polling loop keeps setting state after a route change
- 14.4 an image `onload` fires after its gallery item unmounted
- 14.5 a `finally` block clears a spinner on an unmounted component

**15. wrong comparison**
- 15.1 objects compared with `===`, so a filter never matches
- 15.2 `NaN === NaN` makes a numeric equality guard always false
- 15.3 empty string treated as "no value", hiding a legitimately blank field
- 15.4 an array compared by reference in a memo dep, so it is always unequal
- 15.5 dates compared with `>` across mixed `string` and `Date` types

**16. missing await / unhandled rejection**
- 16.1 an un-awaited save shows the success toast before the write lands
- 16.2 a `Promise.all` result is not awaited and a pending promise is read
- 16.3 an async function called from a non-async caller drops its rejection
- 16.4 a missing `.catch` on a fire-and-forget call breaks the surrounding flow
- 16.5 a forgotten `await` inside a loop destroys the ordering guarantee

**17. CSS specificity or class-merge conflict**
- 17.1 the caller's `className` loses because the base class is concatenated last
- 17.2 two conflicting Tailwind width classes, and the intended one loses
- 17.3 an arbitrary-value class beaten by a variant of the same property
- 17.4 an `!important` in a legacy stylesheet defeats the utility class
- 17.5 a conditional class string leaves both `hidden` and `flex` applied

**18. inverted boolean prop or condition**
- 18.1 a `disabled` prop is handed the value of `isEnabled`
- 18.2 a `hidden`/`visible` rename left exactly one call site inverted
- 18.3 a default of `true` on an opt-in flag turns the feature on everywhere
- 18.4 an `!isLoading` guard shows the empty state during the fetch
- 18.5 a negated predicate keeps precisely the rows it was meant to drop

**19. default parameter or prop shadowing a real value**
- 19.1 a falsy-check default replaces an explicit `0` with the fallback
- 19.2 a default `[]` prop creates a new array each render and breaks memo
- 19.3 a destructuring default masks an explicit `null` from the parent
- 19.4 a default currency shadows a per-account setting that arrives later
- 19.5 a default sort key overrides a URL query param on first render

**20. wrong date / number / locale formatting**
- 20.1 `toLocaleDateString()` with no locale drifts per machine and breaks snapshots
- 20.2 a UTC timestamp rendered in local time shifts the day boundary
- 20.3 currency minor units are divided by 100 twice
- 20.4 a percentage is formatted from an already-multiplied value
- 20.5 `Intl.NumberFormat` built per row, and with the wrong `maximumFractionDigits`

## Recovery shape pool

1. `read_file` returns ENOENT on a plausible but wrong path; re-locate with `grep`.
2. `edit_file` fails with `Error: old_string not found in <path>` (whitespace or quote
   mismatch); re-read the region, then retry the edit exactly.
3. `grep` returns "No matches found"; the second pattern is genuinely smarter.
4. `npx tsc --noEmit` fails after the first edit with a real TS error code (e.g.
   `TS2345`); a targeted follow-up edit fixes it.
5. The first fix leaves the test RED and the failure output reveals a deeper cause; the
   second diagnosis is the right one.
6. `bash` fails because the script is not in package.json (`npm ERR! Missing script`);
   the correct command follows.
7. `read_file` returns a truncation notice on a huge file, forcing `grep` to narrow the
   region before reading again.
8. `read_file` returns exactly `(file is empty - 0 bytes)`; the agent must not
   hallucinate contents and finds the real file instead.
9. `write_file` lands in the wrong directory, is spotted on the next read, and is
   corrected.
10. The test passes but a lint or typecheck step then fails, forcing a cleanup pass.
11. The edit is applied to the wrong one of two similarly named files; a `grep` for
    callers exposes it.
12. `grep` returns far too many hits (30+ lines) so the pattern must be narrowed before
    any read.
13. The fix works but the run exposes a second, pre-existing failure elsewhere in the
    file; the agent leaves it alone and calls it out in the summary.
14. An assumed import path does not exist (`Cannot find module './x'`), so the real
    export has to be located first.
15. The test command runs but matches nothing (`No test files found, exiting with code
    1`); the path pattern is corrected.

## Generator assignments

| Gen | File | Cell (feature x task type) | Lesson codes | Sector | Recovery shapes | Ticket ids |
|---|---|---|---|---|---|---|
| A | `batch4_part_a.jsonl` | search and filtering x build new | 1.1 2.1 3.1 4.1 5.1 6.1 7.1 8.1 9.1 10.1 | energy and utilities | 1, 2, 3 | ENR-2000..2099 |
| B | `batch4_part_b.jsonl` | drag and drop reordering x bug fix | 3.2 4.2 5.2 6.2 7.2 8.2 9.2 10.2 11.1 12.1 | legal and compliance | 4, 5, 6 | LEG-2100..2199 |
| C | `batch4_part_c.jsonl` | charts and data viz x extend existing | 5.3 6.3 7.3 8.3 9.3 10.3 11.2 12.2 13.1 14.1 | manufacturing and industrial | 7, 8, 9 | MFG-2200..2299 |
| D | `batch4_part_d.jsonl` | notifications and toasts x refactor | 7.4 8.4 9.4 10.4 11.3 12.3 13.2 14.2 15.1 16.1 | retail and merchandising | 10, 11, 12 | RTL-2300..2399 |
| E | `batch4_part_e.jsonl` | auth and permission gating x bug fix | 9.5 10.5 11.4 12.4 13.3 14.3 15.2 16.2 17.1 18.1 | automotive and mobility | 13, 14, 15 | MOB-2400..2499 |
| F | `batch4_part_f.jsonl` | export and print (CSV/PDF) x build new | 11.5 12.5 13.4 14.4 15.3 16.3 17.2 18.2 19.1 20.1 | telecom and networking | 1, 6, 11 | TEL-2500..2599 |
| G | `batch4_part_g.jsonl` | keyboard shortcuts and focus x review-and-fix | 13.5 14.5 15.4 16.4 17.3 18.3 19.2 20.2 1.2 2.2 | HR and workforce | 2, 7, 12 | HRW-2600..2699 |
| H | `batch4_part_h.jsonl` | theming and dark mode x design-polish | 15.5 16.5 17.4 18.4 19.3 20.3 1.3 2.3 3.3 4.3 | physical security and access control | 3, 8, 13 | SEC-2700..2799 |
| I | `batch4_part_i.jsonl` | offline and caching x extend existing | 17.5 18.5 19.4 20.4 1.4 2.4 3.4 4.4 5.4 6.4 | weather and environmental monitoring | 4, 9, 14 | ENV-2800..2899 |
| J | `batch4_part_j.jsonl` | multi-step wizards x refactor | 19.5 20.5 1.5 2.5 3.5 4.5 5.5 6.5 7.5 8.5 | publishing and archives | 5, 10, 15 | PUB-2900..2999 |

## Self-check before you finish

```
cd C:\Master-Models
python scripts/validate_jsonl.py "datasets/frontend-stack/generated/raw/batch4_part_<LETTER>.jsonl"
```

Fix any FAIL and re-run until it prints 10 trajectories with 0 FAIL lines.

Then reply with only:

1. The validator summary line.
2. The verification tally: `N of 10 verified by test run`.
3. One short line per trajectory: domain, lesson code, ticket shape (1-8), difficulty,
   and which recovery shape it carries (or none).
