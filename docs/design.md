# Design Log

## product direction pivot

- Status: accepted
- Area: product
- Decision: allure is a multiplayer poker platform where the owner builds progressively smarter bots to learn AI/ML concepts hands-on
- Context: original direction (recommendations platform) was a placeholder — owner had a real idea
- References: `docs/roadmap.md`, `docs/bot-curriculum.md`

---

## stack selection

- Status: accepted
- Area: platform
- Decision: FastAPI + PostgreSQL + React/TypeScript/Vite
- Context: split server/client layout, fast iteration, typed contracts
- References: `docs/architecture.md`

---

## table UI design language

- Status: accepted
- Area: frontend
- Decision: pure black, large minimal cards, players seated around an oval, actions bottom-anchored, no chrome

- Context: reference app (mobile poker with clean iOS aesthetic) established the visual direction. Desktop adaptation keeps the same minimal language but uses the full viewport — oval table, players on all sides, bot sidebar on the right.

- Principles from the reference:
  - Cards are the hero element — large, white, high contrast, nothing competes with them
  - Player identity is avatar + name + stack only — no extra decoration
  - Actions live at the bottom, close to the hero's hands — thumb zone on mobile, natural focus zone on desktop
  - Pot and hand strength are secondary info — present but not dominant
  - Black background makes everything else readable without effort

- Desktop adaptations:
  - Oval felt table occupies the full viewport center
  - Hero seat is bottom-center, always
  - Bot/human seats distributed around the oval (top arc for opponents)
  - Bot decision panel slides in from the right — doesn't overlap the table
  - Wider viewport allows a persistent sidebar for hand history and bot traces

- What we do NOT copy:
  - Memoji avatars (use initials or user-uploaded avatar)
  - Mobile-specific card fan animation
  - Any layout that implies portrait/mobile orientation

---

## action interaction model

- Status: accepted
- Area: frontend / UX
- Decision: desktop action controls mirror live poker physical conventions, not generic button clicks

- Constraint: browser on macOS only receives mouse events, wheel events (two-finger scroll), pointer drag, and keyboard. Three-finger and four-finger trackpad gestures are intercepted by the OS (Mission Control, Exposé, Spaces) before the browser sees them. The interaction model works within these limits.

- Mapping:

| Live poker action | Physical tell | Desktop implementation |
|---|---|---|
| **Check** | Single knock on table | Single click on table felt, or `Space` |
| **Call** | Two knocks / tap forward | Double-click table felt, or `C` |
| **Fold** | Slide cards to muck | Drag hole cards toward center pot, or `F` |
| **Raise** | Count out chips slowly | Click raise zone → scroll wheel on amount display to adjust → `Enter` to fire |
| **All-in** | Shove stack into pot | Drag chip stack fully into pot, or dedicated button when stack ≤ pot |

- Gesture design logic:
  - **Check**: one click — cheapest action, cheapest input
  - **Call**: two clicks — more deliberate, mirrors two knocks on a real table
  - **Fold**: pointer drag — physical, directional, irreversible — cards go toward the muck
  - **Raise**: scroll wheel within the raise element — `preventDefault()` stops page scroll, wheel delta maps to chip increments. Slow scroll = BB increments, fast scroll = large jumps. Feels like turning a dial to count chips out.

- Raise UX detail: clicking the raise zone opens the raise interface inline — no modal. Amount displayed large above hero cards. Scroll to adjust. Click amount to type-override. `Enter` confirms, `Escape` cancels.

- All interactions have keyboard fallbacks. Mouse/trackpad interactions are the primary feel — keyboard is always available.

- Fold drag: cards animate sliding toward center pot and disappear. No confirmation modal. The drag is the confirmation.

- What we do NOT do:
  - "Are you sure?" modal for fold
  - Disabled buttons for unavailable actions — hide them
  - Numeric text input as the primary raise interface — scroll first, type to override
  - Any multi-finger trackpad gestures beyond two-finger scroll

---

## card visual design

- Status: accepted
- Area: frontend
- Decision: large, white, minimal cards — rank and suit only, no decoration

- Card face: white background, rank top-left, suit center, suit color (red for hearts/diamonds, near-black for clubs/spades)
- Card back: diagonal stripe pattern, dark gray on black — subtle, not the focus
- Card size: large enough to read at a glance from full viewport distance — rank should be legible without leaning in
- Hole cards: slight fan/overlap when dealt, flat when player is deciding
- Community cards: horizontal row, evenly spaced, revealed one at a time with a quick flip animation
- Folded cards: slide to center and fade — not a pile, just gone
- Hand strength label (e.g. "Pair", "Flush draw"): small, muted, positioned above hole cards — present but secondary

---

## bot presence on the table

- Status: accepted
- Area: frontend
- Decision: bots sit at the table like humans — same seat layout, same avatar treatment — but their decision trace surfaces in a collapsible right panel

- Bots are not visually marked as bots at the table (no robot icon, no indicator) — they play as opponents
- After each bot action, the right panel updates with: action taken, one-line rationale, and (for Analyst/Memory/Critic bots) the full decision trace expandable
- Coach report surfaces as a full-width drawer that slides up after the hand ends — covers the table, dismissable
- Bot "thinking" state: subtle pulse on their avatar while the decision is being computed — not a spinner, not a loading bar
