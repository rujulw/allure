# Bot Curriculum

Per-bot learning guide. For each milestone: the concept it teaches, what to understand first, what to read, and the first experiment to run before writing bot code.

---

## M2 — Random Bot

**Concept:** baseline agent, legal action enumeration, bot interface

**Prereqs:** none

**Understand first:**
- What is a legal action at each street? (fold/call/raise constraints, all-in edge cases)
- What does a uniform distribution over a discrete set look like in code?

**Resources:**
- Python `random` module docs — `random.choice()`
- The game engine's `HandState` object — read it, understand every field

**First experiment:**
Print all legal actions for a given hand state. Make sure you can enumerate them correctly before you randomly pick one.

---

## M3 — Tight/Passive Bot

**Concept:** rule-based strategy, preflop hand strength, position

**Prereqs:** M2 complete, understand what VPIP means

**Understand first:**
- Sklansky hand groups — why are some starting hands stronger than others?
- How does position affect hand playability?
- What is pot odds at a basic level?

**Resources:**
- Sklansky & Malmuth: *Hold'em Poker for Advanced Players* — hand group tables
- [Preflop hand charts](https://www.tightpoker.com/poker_hands.html) — read these before coding
- Two Plus Two forums: "What hands should I play from UTG vs BTN?"

**First experiment:**
Write a function that takes two hole cards and returns a strength score 1–9 (Sklansky groups). Test it against known hands before touching the bot file.

---

## M4 — Aggressive Bluff Bot

**Concept:** aggression, bluff-to-value ratio, continuation betting

**Prereqs:** M3 complete

**Understand first:**
- What is a continuation bet and when is it profitable?
- What bluff-to-value ratio makes a player unexploitable on the river?
- What is fold equity?

**Resources:**
- [The Theory of Poker](https://www.amazon.com/Theory-Poker-Professional-Player/dp/1880685000) by David Sklansky — chapters on bluffing and semi-bluffing
- [Upswing Poker: Bluff-to-Value Ratios](https://upswingpoker.com/value-bet-bluff-ratio/) — free article
- Think about: if villain calls 1/3 pot bets with 70% of their range, what's your minimum bluff frequency to break even?

**First experiment:**
Calculate break-even bluff frequency for a given bet size by hand (not in code). Prove you understand the math before implementing it.

---

## M5 — Range Bot

**Concept:** probability distributions over discrete sets, range notation, range updating

**Prereqs:** M4 complete, basic probability

**Understand first:**
- What does it mean to "put someone on a range" vs. "put someone on a hand"?
- How do you represent a range as a data structure? (set of (rank, suit) combos? probability vector?)
- How does an observed action eliminate combos from a range?

**Resources:**
- [Flopzilla](https://flopzilla.com/) — play with this tool to build intuition for ranges before coding
- [PokerStove concept explained](https://www.pokerstrategy.com/strategy/various-poker/range-of-hands/) — read this
- Think about: how many possible two-card combos exist from a 52-card deck? How does knowing board cards reduce this?

**First experiment:**
Build a `Range` class in a notebook. It holds a probability distribution over all possible two-card combos. Write an `update(action, street)` method that zeroes out combos inconsistent with the observed action. Test it: if a player 3-bets preflop, which combos should survive?

---

## M6 — Equity Calculator Bot

**Concept:** combinatorics, enumeration, expected value

**Prereqs:** M5 complete, Range class working

**Understand first:**
- What is equity? (probability of winning the hand at a given moment)
- How do you enumerate all possible board runouts from a partial board?
- How do you compute equity for hand A vs. range R (not just hand A vs. hand B)?

**Resources:**
- [ProPokerTools equity calculator](https://www.propokertools.com/simulations) — use this to verify your results before and after
- [Two Plus Two: equity calculation from first principles](https://forumserver.twoplustwo.com/15/poker-theory/equity-calculations-1184348/)
- Combinatorics: C(n, k) — how many ways to choose k cards from n remaining cards?

**First experiment:**
By hand (or numpy, no poker libraries): calculate the equity of AhKh vs. a range of {JJ, QQ, KK, AA} on a board of Tc 8d 2s. List every possible runout, count wins and ties. Verify against ProPokerTools. Then write it in code.

---

## M7 — Monte Carlo Bot

**Concept:** Monte Carlo simulation, sampling, convergence, variance

**Prereqs:** M6 complete, equity calculator working

**Understand first:**
- Why is exact enumeration too slow for multi-way pots?
- What is the law of large numbers and what does it mean for sample size?
- How do you estimate confidence intervals on a sampled mean?

**Resources:**
- [Monte Carlo method — Wikipedia](https://en.wikipedia.org/wiki/Monte_Carlo_method) — read the intro
- Sutton & Barto *Reinforcement Learning* Ch. 2 — Monte Carlo estimation (free PDF online)
- Think about: at N=100, N=1000, N=10000 samples, how tight is your equity estimate? Plot the variance curve.

**First experiment:**
In a notebook, estimate π using Monte Carlo (the classic dart board problem). Then apply the same logic: estimate equity by sampling 1000 random runouts instead of enumerating all of them. Compare to your M6 exact result.

---

## M8 — Bayesian Bot

**Concept:** Bayes' theorem, conditional probability, belief updating

**Prereqs:** M5 Range Bot complete (range as a probability distribution is the prior)

**Understand first:**
- Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
- In poker terms: P(villain has hand X | villain bet) = P(villain bets | villain has X) * P(villain has X) / P(villain bets)
- How do you estimate P(villain bets | villain has X)? (This is the likelihood — it comes from a betting frequency model)

**Resources:**
- [3Blue1Brown: Bayes theorem visual explanation](https://www.youtube.com/watch?v=HZGCoVF3YvM) — watch this first
- [Bayesian Poker — academic paper by Aaron Davidson](https://poker.cs.ualberta.ca/publications/davidson.msc.pdf) — Chapter 2 specifically
- Think about: after villain checks the flop, which hands become more likely in their range? Which become less likely?

**First experiment:**
In a notebook, implement Bayesian range updating manually. Start with a uniform prior over 10 candidate hands. Apply a likelihood model (e.g. villain bets strong hands 80% of the time, medium 40%, weak 10%). After observing a bet, compute the posterior. Verify it sums to 1. Do it for a check too.

---

## M9 — Search Bot

**Concept:** game tree search, lookahead, backed-up value estimation

**Prereqs:** M6/M7 (equity as leaf evaluator), basic tree data structures

**Understand first:**
- What is a game tree? (nodes = game states, edges = actions)
- What is backed-up value? (leaf values propagate up through the tree)
- Why can't you use minimax directly in poker? (imperfect information — you don't know opponent's cards)
- What is depth-limited search and why is the leaf evaluator critical?

**Resources:**
- AIMA (Russell & Norvig) Ch. 5 — Adversarial Search (you covered this in CSC422 — re-read it with poker in mind)
- [Counterfactual Regret Minimization intro — Neller & Lanctot](http://modelai.gettysburg.edu/2013/cfr/cfr.pdf) — just the first 4 pages on game trees
- Think about: in a 2-player game with 3 streets and 3 actions per node, how many leaf nodes does the full tree have? Why do we need pruning?

**First experiment:**
Build a game tree for a simplified 1-street, 2-player game (just river, 2 actions: bet or check). Enumerate all paths. Compute EV at each leaf using your equity calculator. Back up values manually. Verify the optimal action at the root.

---

## M10 — GTO-ish Bot

**Concept:** Nash equilibrium, mixed strategies, balance

**Prereqs:** M9 complete, understand what "exploitable" means

**Understand first:**
- What is a Nash equilibrium? (no player can improve by unilaterally changing strategy)
- What is a mixed strategy? (randomize over actions with specific probabilities)
- What does it mean to be "balanced"? Why does balancing your betting range make you harder to exploit?
- What is the minimum defense frequency and where does it come from?

**Resources:**
- *The Mathematics of Poker* by Bill Chen & Jerrod Ankenman — Ch. 3-4 (this book is worth owning)
- [GTO+ concepts — basic explanation](https://www.gtoplus.com/learn)
- Think about: if you always bet your strong hands and always check your weak hands, what will a smart opponent do? How does mixing prevent this?

**First experiment:**
Work through the toy game: 1 card each, 1 betting round, 2 actions. Solve for the Nash equilibrium by hand (the math is in the Chen/Ankenman book). Verify your solution makes both players indifferent to the other's strategy.

---

## M11 — CFR Bot

**Concept:** counterfactual regret minimization, regret matching, Nash convergence

**Prereqs:** M10 complete, understand mixed strategies and game trees

**Understand first:**
- What is regret in game theory? (difference between what you got and what you could have gotten)
- What is counterfactual regret? (regret weighted by probability of reaching a state)
- How does regret matching produce a mixed strategy?
- What does it mean to converge to Nash equilibrium through iterative self-play?

**Resources:**
- [Neller & Lanctot — An Introduction to Counterfactual Regret Minimization](http://modelai.gettysburg.edu/2013/cfr/cfr.pdf) — read all of it, implement the Kuhn poker example yourself first
- [Solving Kuhn Poker with CFR — Python walkthrough](https://justinsermeno.com/posts/cfr/) — read after the paper, not before
- Do NOT look at Texas Hold'em CFR implementations until your Kuhn poker CFR works correctly

**First experiment:**
Implement CFR for Kuhn poker (3-card, 1-round game) in a notebook. Run it for 10,000 iterations. Verify your strategy converges to the known Nash equilibrium (exact values are in the Neller paper). Only move to Hold'em abstraction after this works.

---

## M12 — Exploit Bot

**Concept:** exploitative play, leak identification, adaptive counter-strategy

**Prereqs:** M10/M11 complete (need GTO baseline to know when to deviate)

**Understand first:**
- What is an exploitative strategy? (maximally exploits a specific opponent, not balanced)
- What stats reveal exploitable tendencies? (high fold-to-cbet, low 3-bet %, always continuation bet)
- What is the risk of playing exploitatively? (you become exploitable yourself if opponent adjusts)
- When should you abandon exploit mode and revert to GTO?

**Resources:**
- *Poker's 1%* by Ed Miller — practical leak identification
- Think about: if villain folds to river bets 80% of the time, what should your river betting frequency be? What's the math?

**First experiment:**
Pick one specific leak (e.g. villain folds to c-bet 75% of the time). Calculate the exact EV of always c-betting vs. never c-betting vs. optimal frequency. Show the math. Then think about how to detect this leak from observed hand history.

---

## M13 — Imitation Learning Bot

**Concept:** behavioral cloning, supervised learning, generalization

**Prereqs:** M11/M12 complete, basic ML (you have this from CSC422)

**Understand first:**
- What is behavioral cloning? (supervised learning on (state, action) pairs)
- What is distribution shift? (why imitation learning fails when the learned policy makes mistakes the expert never made)
- What features of a hand state are informative for action prediction?
- What are the limits of imitation learning vs. reinforcement learning?

**Resources:**
- CS229 lecture notes on imitation learning (Stanford, free online)
- [DAgger paper — Ross et al.](https://arxiv.org/abs/1011.0686) — the fix for distribution shift, read the introduction
- Scikit-learn: `RandomForestClassifier` or logistic regression as your first model

**First experiment:**
Export 1000 hand decisions from your CFR or GTO-ish bot as (features, action) pairs. Train a logistic regression classifier. Evaluate held-out accuracy. What features matter most? What does the model get wrong?

---

## M14 — Self-Play RL Bot

**Concept:** reinforcement learning, policy gradient, reward signal, exploration vs. exploitation

**Prereqs:** M13 complete, understand what a policy is

**Understand first:**
- What is the difference between supervised learning and reinforcement learning?
- What is a policy? A value function? A reward signal?
- What is REINFORCE (vanilla policy gradient)?
- What is the credit assignment problem? Why is it hard in poker?

**Resources:**
- Sutton & Barto *Reinforcement Learning: An Introduction* — Ch. 1, 2, 13 (free PDF at incompleteideas.net)
- [Spinning Up in Deep RL — OpenAI](https://spinningup.openai.com/en/latest/) — policy gradient section
- Start simple: don't use deep RL. Use tabular Q-learning on an abstracted state space first.

**First experiment:**
Implement tabular Q-learning on a simplified 1-street, 2-action poker variant (bet or check, 5-card stud). Train it against a fixed opponent (Random Bot). Plot win rate over episodes. Verify learning is actually happening before scaling up.

---

## M15 — Neural Evaluator Bot

**Concept:** neural networks as function approximators, state representation, regression

**Prereqs:** M14 complete, understand basic neural nets

**Understand first:**
- What features describe a poker game state? (hole cards, board, pot, position, street, stack sizes)
- How do you encode categorical card features (suit, rank) for a neural net?
- What is the prediction target? (win probability? EV? action probabilities?)
- What training data do you need and where does it come from?

**Resources:**
- Fast.ai Practical Deep Learning — Lesson 1 and 2 (tabular data chapter)
- [DeepStack paper](https://arxiv.org/abs/1701.01724) — read the abstract and intro to understand what a neural evaluator achieves at the state of the art
- PyTorch or scikit-learn — start with scikit-learn MLP before going deep

**First experiment:**
Generate 10,000 (hand state, equity) pairs using your Monte Carlo bot. Train a 2-layer MLP to predict equity from state features. Compare predictions to ground truth. What features matter? Where does it fail?

---

## M16 — Opponent-Modeling Bot (ML)

**Concept:** classification, feature engineering, adaptive strategy

**Prereqs:** M13/M14 complete, hand history storage working

**Understand first:**
- What features predict opponent behavior? (VPIP, PFR, aggression factor, positional stats)
- What is the difference between predicting opponent hand range vs. predicting opponent action?
- How do you handle small sample sizes? (only 20 hands of history on a new player)
- When is the model confident enough to deviate from baseline strategy?

**Resources:**
- [VPIP/PFR/AF explained](https://www.pokertracker.com/guides/general-guides/poker-statistics-guide/) — HUD stats primer
- Scikit-learn: classification with small samples, confidence thresholds
- Think about: what's the minimum number of hands before your opponent model is reliable?

**First experiment:**
Export hand history from 500 hands against Tight/Passive Bot and 500 hands against Aggressive Bluff Bot. Extract features. Train a classifier to distinguish the two. Evaluate accuracy. Then think: given a new opponent with only 10 hands of history, how confident should you be?

---

## M17 — Meta Bot

**Concept:** meta-learning, strategy selection, multi-armed bandit

**Prereqs:** all previous bots complete and working

**Understand first:**
- What is a multi-armed bandit problem?
- How does UCB (Upper Confidence Bound) balance exploration and exploitation?
- What signals tell you which opponent type you're facing?
- What is the cost of misclassifying an opponent type?

**Resources:**
- Sutton & Barto Ch. 2 — Multi-Armed Bandits (free PDF)
- Think about: you're at a table with 3 unknown opponents. You have 10 hands of history on each. Which strategy do you assign each one, and how confident are you?

**First experiment:**
Build a simple opponent classifier with 3 classes: tight/passive, aggressive/loose, balanced. Test it against your existing bots after N hands. Plot accuracy vs. N. What's the minimum N for reliable classification?

---

## M18–M22 — Specialized Role Bots (Fast, Analyst, Memory, Critic, Coach)

These bots are orchestration and synthesis — they depend on all prior work being solid. By the time you reach M18, re-read the full roadmap and assess honestly:

- Which of M2–M17 do you fully understand and can explain from scratch?
- Which did you rush or partially understand?

Go back and fill gaps before building role bots. Fast Bot distills M2–M4. Analyst Bot orchestrates M5–M7. Memory Bot applies M16 without ML. Critic and Coach require every other bot's `explain()` output to be meaningful.

There are no shortcuts listed here on purpose.
