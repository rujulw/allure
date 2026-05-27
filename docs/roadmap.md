# Roadmap

## Structure

Six phases, 22 milestones. Each bot unlocks a concept the next one depends on. The final five (Fast → Coach) synthesize everything into specialized roles.

```
Phase 1  — Foundation          Game engine and multiplayer
Phase 2  — Rule-Based          Random → Range (think in distributions)
Phase 3  — Math & Probability  Equity → Monte Carlo → Bayesian
Phase 4  — Game Theory         Search → GTO-ish → CFR → Exploit
Phase 5  — Learning            Imitation → Self-Play RL → Neural Eval → ML Opponent → Meta
Phase 6  — Specialized Roles   Fast → Analyst → Memory → Critic → Coach
```

---

## Phase 1 — Foundation

### Milestone 1 — Game Engine and Multiplayer

Fully playable Texas Hold'em: real-time tables, authoritative server-side state, human vs. human.

**Server**
- `feat/server-foundation` — FastAPI scaffold, Postgres, Alembic, JWT auth
- `feat/game-engine` — hand state machine (deal → pre-flop → flop → turn → river → showdown), deck, hand evaluator, pot/side-pot logic
- `feat/table-management` — table creation, seat assignment, buy-in, blind structure, leave/rejoin
- `feat/realtime` — WebSocket event stream (card dealt, action requested, pot updated, hand ended)

**Client**
- `feat/client-shell` — React scaffold, routing, TanStack Query, auth screens
- `feat/game-table` — live table UI: hole cards, community cards, pot, action controls, seat ring, WebSocket sync

**Exit criteria**
- [ ] two humans complete a hand end to end
- [ ] engine enforces all action rules (call ≤ pot, min raise, all-in)
- [ ] hand history persisted per session
- [ ] client recovers state on reconnect

---

## Phase 2 — Rule-Based

Bots that act on fixed rules. No probability, no learning. Purpose: validate the bot pipeline and establish shared poker utilities every later bot depends on.

### Milestone 2 — Random Bot

Legal action sampled uniformly. Validates the bot seat abstraction and action pipeline.

- `feat/random-bot` — `decide(state) → Action` by sampling legal actions
- Bot decisions visible in sidebar

**Exit criteria**
- [ ] completes full ring sessions without errors
- [ ] bot action pipeline (seat → request → decision → state update) verified end to end

---

### Milestone 3 — Tight/Passive Bot

Folds most hands, calls when strong, never raises. Establishes preflop range logic and hand strength evaluation.

- `feat/tight-passive-bot` — static preflop fold/call ranges by position; postflop call-only above strength threshold
- `server/app/poker/strength.py` — hand strength evaluator (shared by all future bots)

**Exit criteria**
- [ ] folds > 70% of hands preflop
- [ ] never initiates a raise
- [ ] `strength.py` tested in isolation

---

### Milestone 4 — Aggressive Bluff Bot

Wide ranges, frequent raises, bluffs on missed draws. Stress-tests pot logic and all-in handling.

- `feat/aggressive-bluff-bot` — wide opens, raise-heavy postflop, bluff frequency tuned by street and board texture
- Stresses multi-way raises, all-in side pots, re-raise caps

**Exit criteria**
- [ ] initiates raises > 50% of hands played
- [ ] all-in and side-pot logic holds under heavy pressure
- [ ] no illegal action accepted by engine

---

### Milestone 5 — Range Bot

**Concept unlocked: thinking in distributions.**

Represents opponent hands as a probability distribution over all possible holdings, not a single guessed hand. Foundation for every probability-based bot that follows.

- `feat/range-bot` — assign prior range to each opponent at deal; narrow range on each observed action (bet, check, fold, raise); decide based on most likely opponent holding
- `server/app/poker/ranges.py` — range representation and update primitives (shared)

**Exit criteria**
- [ ] range narrows correctly as opponent actions arrive
- [ ] decisions demonstrably differ against tight vs. loose ranges
- [ ] `ranges.py` interface tested and documented

---

## Phase 3 — Math and Probability

Bots that compute before acting. Each adds a new mathematical tool built on `ranges.py` and `strength.py`.

### Milestone 6 — Equity Calculator Bot

Exact equity of hero hand vs. estimated villain range. Calls when equity exceeds pot odds.

- `feat/equity-bot` — enumerate board runouts; compute hero equity vs. range; act on EV
- `server/app/poker/equity.py` — equity calculator (shared)

**Exit criteria**
- [ ] equity verified against known matchups
- [ ] positive-EV calls made, negative-EV spots folded
- [ ] decision latency ≤ 500ms

---

### Milestone 7 — Monte Carlo Bot

Replaces enumeration with sampling. Handles multi-way pots and complex boards too slow for exact equity.

- `feat/monte-carlo-bot` — N sampled runouts; confidence interval on equity; act when CI is tight enough
- Implements `equity.py` interface as a drop-in backend; configurable N

**Exit criteria**
- [ ] estimates within ±2% of exact at N=1000
- [ ] decision latency ≤ 2s at N=1000
- [ ] multi-way equity correct

---

### Milestone 8 — Bayesian Bot

**Concept unlocked: belief updating.**

Updates opponent range beliefs after every observed action using Bayes' theorem. Starts with a prior range; each bet, check, or fold shifts the posterior.

- `feat/bayesian-bot` — prior range at deal → posterior after each action; likelihood of action given candidate hand computed per street
- Shares `ranges.py`; Bayesian update is a new primitive added to it
- `explain()` shows how each action shifted the belief distribution

**Exit criteria**
- [ ] posterior range shifts meaningfully on every observed action
- [ ] bot decisions change when opponent deviates from prior behavior
- [ ] belief update verified against worked hand examples

---

## Phase 4 — Game Theory

Bots that reason about strategy, balance, and exploitation. Build on equity and belief tools from Phase 3.

### Milestone 9 — Search Bot

**Concept unlocked: lookahead.**

Builds a tree of possible future actions and card outcomes, evaluates leaf nodes with equity tools, and backs up values to choose the best action now.

- `feat/search-bot` — depth-limited game tree search; leaf evaluation via `equity.py`; action selection by backed-up EV
- Configurable depth; pruning for illegal or dominated branches

**Exit criteria**
- [ ] search tree generates correct legal action branches
- [ ] backed-up EV demonstrably better than greedy equity-only decisions
- [ ] decision latency ≤ 5s at practical depth

---

### Milestone 10 — GTO-ish Bot

**Concept unlocked: balance.**

Stays balanced across all board textures and action lines — hard to exploit because it mixes actions rather than always doing the "obvious" thing.

- `feat/gto-ish-bot` — hand categorized into value/draw/bluff buckets; each bucket assigned a mixed strategy (raise X%, call Y%, fold Z%); action sampled from distribution
- Non-deterministic: same state, different action each time

**Exit criteria**
- [ ] executes mixed strategies (verified non-deterministic)
- [ ] bluff-to-value ratio on river within accepted GTO bounds
- [ ] harder to exploit by Aggressive Bluff Bot than Tight/Passive Bot

---

### Milestone 11 — CFR Bot

**Concept unlocked: regret minimization.**

Learns a near-Nash-equilibrium strategy via Counterfactual Regret Minimization trained offline. Runtime is pure lookup — no computation during play.

- `feat/cfr-bot` — offline CFR training script; hand abstraction layer (`server/app/poker/abstraction.py`) maps states to buckets; strategy table stored as file artifact; runtime samples from distribution
- Training script lives in `server/scripts/train_cfr.py`

**Exit criteria**
- [ ] strategy profile trained to Nash distance < 5% on abstracted game
- [ ] decision latency < 100ms (lookup only)
- [ ] mixed strategies executed correctly at runtime

---

### Milestone 12 — Exploit Bot

**Concept unlocked: adaptive exploitation.**

Identifies and punishes statistical leaks in predictable opponents. Plays GTO as default; shifts to an exploitative counter-strategy when it detects a pattern.

- `feat/exploit-bot` — collect opponent stats (VPIP, fold-to-cbet, bet sizing tells); detect deviation from balanced play; switch strategy toward max-exploit counter
- Exploit thresholds tuned per stat; reverts to GTO when stats are thin

**Exit criteria**
- [ ] measurably outperforms CFR Bot against Tight/Passive and Aggressive Bluff bots
- [ ] reverts to balanced play when facing another CFR/GTO-ish bot
- [ ] exploit triggers logged in decision sidebar

---

## Phase 5 — Learning

Bots that improve from data — hand histories, simulated games, or opponent observations.

### Milestone 13 — Imitation Learning Bot

**Concept unlocked: learning from demonstration.**

Trained on saved hand histories from stronger bots (or humans). Learns to reproduce their decision patterns without explicit reward.

- `feat/imitation-bot` — supervised learning on `(state, action)` pairs extracted from hand history; lightweight classifier or policy network; inference at decision time
- Training pipeline in `server/scripts/train_imitation.py`

**Exit criteria**
- [ ] trained on ≥ 10k hands from CFR Bot or GTO-ish Bot
- [ ] action accuracy > 70% on held-out hand history
- [ ] decision latency ≤ 200ms

---

### Milestone 14 — Self-Play RL Bot

**Concept unlocked: learning from experience.**

Improves by playing against itself. No labeled data needed — reward signal is chips won or lost.

- `feat/selfplay-bot` — RL training loop: agent plays against a copy of itself; policy updated via policy gradient or actor-critic; training runs headlessly via simulation harness
- `server/scripts/train_selfplay.py`; trained weights stored as artifact

**Exit criteria**
- [ ] training loop runs without instability for ≥ 1000 episodes
- [ ] policy improves measurably against Random Bot baseline over training
- [ ] decision latency ≤ 200ms at inference

---

### Milestone 15 — Neural Evaluator Bot

**Concept unlocked: learned state evaluation.**

Replaces hand-coded strength/equity heuristics with a neural network that scores game states directly.

- `feat/neural-eval-bot` — neural network trained to predict win probability (or EV) from raw game state features; used as leaf evaluator in search or standalone decision maker
- `server/app/poker/neural_eval.py` — evaluator interface (shared by Search Bot and future bots)

**Exit criteria**
- [ ] evaluator predictions correlate with Monte Carlo equity at r > 0.90
- [ ] decision quality equal to or better than Equity Calculator Bot
- [ ] evaluator inference ≤ 50ms

---

### Milestone 16 — Opponent-Modeling Bot (ML)

**Concept unlocked: adaptive opponent model.**

Builds a live ML model of each opponent from observed actions. Adjusts strategy dynamically as the model updates.

- `feat/ml-opponent-bot` — per-opponent feature extraction; range prediction via trained classifier; strategy shifted toward exploit when prediction confidence is high
- Opponent model persisted in Postgres; updated after every hand
- `explain()` surfaces which opponent reads drove the decision

**Exit criteria**
- [ ] model improves win rate against Tight/Passive and Aggressive Bluff bots
- [ ] features update after every hand, persist across sessions
- [ ] per-seat model overlay in UI

---

### Milestone 17 — Meta Bot

**Concept unlocked: strategy switching.**

Classifies each opponent at the table and delegates to the appropriate strategy bot. Against unknowns: GTO-ish. Against predictables: Exploit. Against strong players: CFR.

- `feat/meta-bot` — opponent classifier (rule-based or ML); strategy router maps opponent type → bot strategy; live reclassification as new hands reveal more information

**Exit criteria**
- [ ] correctly classifies Tight/Passive, Aggressive Bluff, and Random bots after ≤ 20 hands
- [ ] switches strategy on reclassification
- [ ] outperforms any single fixed-strategy bot against a mixed table

---

## Phase 6 — Specialized Roles

These bots synthesize everything above. Each plays a distinct role beyond winning chips.

### Milestone 18 — Fast Bot

Distills heuristics from Phases 2–3 into a < 50ms decision engine. Establishes the shared `decide()/explain()` interface used by Critic and Coach.

- `feat/fast-bot` — preflop chart lookup + postflop heuristic tree; no external calls
- Exposes `decide(state) → Action` and `explain(state, action) → str`

**Exit criteria**
- [ ] decision latency < 50ms p99
- [ ] preflop decisions consistent with basic GTO ranges
- [ ] `explain()` returns human-readable rationale

---

### Milestone 19 — Analyst Bot

Chains internal analysis tools (equity, Monte Carlo, neural evaluator) before acting. Records full `DecisionLog`.

- `feat/analyst-bot` — `decide()` calls tools from `server/app/tools/`; `DecisionLog` records tool inputs, outputs, final action
- Decision trace panel rendered in UI

**Exit criteria**
- [ ] completes hands within action timeout (≤ 10s)
- [ ] `DecisionLog` records full tool call chain
- [ ] trace panel in UI

---

### Milestone 20 — Memory Bot

Rule-based opponent modeling using stat thresholds. Explicit and auditable unlike ML Opponent Bot.

- `feat/memory-bot` — VPIP, PFR, aggression factor, showdown frequency tracked per opponent in Postgres
- `decide()` adjusts ranges based on live stats; `explain()` names the reads
- Per-seat stat overlay in UI

**Exit criteria**
- [ ] stats persist across sessions
- [ ] demonstrably tighter against loose opponents, wider against nits
- [ ] stat overlay in UI

---

### Milestone 21 — Critic Bot

Does not play. Reviews other bots' decisions, scores them 0–10, generates counter-arguments.

- `feat/critic-bot` — `critique(decision_log: DecisionLog) → Critique` with score and specific objection
- Runs after each bot action; output attached to hand timeline in UI

**Exit criteria**
- [ ] scores every Fast Bot and Analyst Bot action during a hand
- [ ] critique includes specific objection with supporting reasoning
- [ ] critique stored for Coach to reference

---

### Milestone 22 — Coach Bot

Post-hand explainer. Synthesizes hand history, decision logs, and critiques into a structured coaching report.

- `feat/coach-bot` — `coach(hand_history, decision_logs, critiques) → CoachReport`
- Per-street breakdown; best alternative action per decision point; overall assessment
- Expandable post-hand review drawer; step-by-step replay for any completed hand

**Exit criteria**
- [ ] report generated for every hand with at least one bot participant
- [ ] covers every decision where a bot deviated from Critic's preferred line
- [ ] humans can replay a coached hand step-by-step in UI
