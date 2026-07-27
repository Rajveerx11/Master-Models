# Frontend Design Conventions (distilled from taste-skill, ui-ux-pro-max, impeccable)

## Code conventions
- Function components only; named exports only, never `export default`.
- Type props with an explicit `interface`/`type`; never `any`, never `React.FC`.
- Call hooks unconditionally at the top; derive values instead of mirroring props into state.
- Never track continuous input (scroll, mouse position) in `useState`; use refs or CSS.
- Import order: react, third-party, local; no unused imports, no unused vars.
- Every diff must compile under `tsc --noEmit` strict; no `@ts-ignore` without a reason comment.

## Layout & spacing
- Spacing only from the 4px Tailwind scale (`p-2/4/6/8`, `gap-2/4/6`); no arbitrary values like `p-[13px]`.
- Group related items tight (`gap-2`), separate groups generously (`gap-6`+); more space above a heading than below it.
- Prefer `gap` on the parent over per-child margins for sibling rhythm.
- Never flex percentage math (`w-[calc(33%-1rem)]`); use `grid grid-cols-3 gap-6`.
- Page content max `max-w-7xl mx-auto`; prose max `max-w-[65ch]`.
- Use `min-h-dvh`, never `h-screen`.
- Every multi-column layout declares its mobile collapse in the same component (`grid-cols-1 md:grid-cols-3`).
- z-index only from a fixed scale (0/10/20/40/50); no `z-[999]`.
- Reserve space for async content (fixed heights, `aspect-ratio`, skeletons); zero layout shift on load.

## Typography
- Sizes only from the Tailwind type scale (`text-xs` through `text-2xl`); no arbitrary font sizes.
- Body text `text-base` (16px) minimum; `text-sm` only for secondary text and metadata.
- Body line-height 1.5+ (`leading-relaxed`); tight leading (`leading-tight`) on headings only.
- Weight hierarchy: headings 600, labels 500, body 400; never signal hierarchy by size alone.
- Truncate with `truncate` or `line-clamp-2` plus `title` for the full text; add `min-w-0` to flex children holding text.
- Use `tabular-nums` on numbers in tables, prices, counters, and timers.
- No fixed widths on text containers; text must survive 30% longer strings (i18n) without breaking.

## Color & contrast
- Colors only via semantic tokens or Tailwind theme classes; never raw hex in JSX.
- One accent color per app; one gray family only (never mix slate + zinc + gray).
- Text contrast >= 4.5:1; large text, icons, and controls >= 3:1 - in every state, both themes.
- Pair every color utility with its `dark:` variant (`bg-white dark:bg-zinc-950`); never ship light-only.
- Dark mode is composed, not inverted: lighter desaturated variants, contrast re-checked separately.
- No pure `#000` or `#fff`; use off-black (`zinc-950`) and off-white.
- Never convey state by color alone; pair with an icon or text.
- Visible focus ring on every interactive element (`focus-visible:ring-2 ring-offset-2`); `outline-none` without a replacement is banned.

## Interactive states
- Every interactive element ships hover, focus-visible, active, and disabled styles in the same diff.
- Disabled = `disabled` attribute + `disabled:opacity-50 disabled:pointer-events-none`, never style-only.
- Async actions disable their trigger while pending and show a spinner; double-submit must be impossible.
- Loads over 300ms show a skeleton matching the final layout shape, not a bare centered spinner.
- Every list/table/panel handles empty: message plus a next action, never a blank region.
- Every fetch handles error: inline message naming the problem plus a retry action; "An error occurred" is banned.
- Press feedback on tappable cards/buttons: `active:scale-[0.98]`, restored on release.

## Forms UX
- Visible `<label htmlFor>` above every input; placeholder-as-label is banned.
- Validate on blur or submit, never on keystroke; show errors only after the user finishes the field.
- Error text sits below its field, wired with `aria-invalid` and `aria-describedby`, contrast >= 4.5:1.
- On submit failure, move focus to the first invalid field.
- Submit button shows pending state (disabled + spinner), then explicit success or error feedback.
- Preserve user input through every error; never clear a failed form.
- Use semantic input types (`email`, `tel`, `number`, `url`) and `autocomplete` attributes.
- Mark required fields; helper text is persistent below the input, not a placeholder.
- Destructive actions use the danger token, sit apart from the primary action, and confirm before executing.
- Whole form operable by keyboard: Tab order matches visual order, Enter submits, Escape cancels.

## Motion
- Micro-interactions 150-300ms; nothing over 400ms.
- Ease-out on enter, ease-in on exit; exit ~70% of enter duration; linear easing is banned for UI.
- Animate only `transform` and `opacity`; never `width`/`height`/`top`/`left`/`margin`.
- Max 1-2 animated elements per view; every animation must justify itself as feedback, state change, or hierarchy.
- Stagger list entrances 30-50ms per item; never all-at-once fades on long lists.
- Gate all animation behind `prefers-reduced-motion` (`motion-reduce:` variants); reduced = instant, not slower.
- Never `window.addEventListener("scroll")`; use `IntersectionObserver`.
- Never block input during an animation; animations are interruptible.

## Accessibility
- Semantic HTML first: `<button>` for actions, `<a>` for navigation, `<nav>/<main>/<table>` for structure; `onClick` on a `<div>` is banned.
- aria only when no native element fits; `aria-label` is required on every icon-only button.
- Meaningful images get descriptive `alt`; decorative images get `alt=""`.
- Heading levels are sequential (no h2 to h4 skip); one h1 per view.
- Modals trap focus, close on Escape, and return focus to the trigger.
- Tap targets >= 44x44px with >= 8px gap between adjacent targets.
- Dynamic errors and toasts announce via `role="alert"` / `aria-live="polite"` and never steal focus.
- Layout survives 200% browser zoom without loss of content or function.

## Anti-slop bans
- No lorem ipsum or "placeholder text here"; write real domain copy.
- No em-dash or en-dash in UI copy; use a comma, period, or hyphen.
- No emoji as icons; one SVG icon family per app, one `strokeWidth` globally.
- No fake-looking fake data: no "John Doe", "Acme", "99.99%", "1234567"; use realistic messy values ("Priya Raman", "47.2%").
- No gray placeholder boxes or div-built fake screenshots standing in for content.
- No gradient text; emphasis comes from weight or size.
- No neon glows or zero-offset colored halo shadows; shadows carry offset plus soft blur.
- No mixed corner radii; one radius scale per app, applied identically to cards, inputs, and buttons.
- No cards inside cards; no card at all when a border or spacing can group it.
- No colored `border-left` thicker than 1px on cards, list items, or alerts.
- No monospace as a "technical" costume; mono is for code, data, and measurement only.
- No decorative status dots; a dot must encode real semantic state.
- No section-number eyebrows ("01 / OVERVIEW") or uppercase micro-labels above every heading.
- No filler copy verbs: "Seamless", "Elevate", "Unleash", "Next-Gen", "Revolutionize".
- No `console.log`, dead code, or commented-out blocks in a shipped diff.
