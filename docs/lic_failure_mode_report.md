# Failure Modes in "Lost in Conversation": Detailed Report

## The Core Finding

The paper documents a **39% average performance degradation** when going from single-turn (Full) to multi-turn sharded conversations across 15 LLMs and 6 tasks. Critically, this is **not** an aptitude problem — it's a **reliability** problem. Aptitude drops only ~16% on average, while unreliability **more than doubles** (+112%). Even the best models (GPT-4.1, Gemini 2.5 Pro) become wildly unreliable in multi-turn settings, with 50 percentage point gaps between best-case and worst-case runs on the same instruction.

## The Decomposition: Why Multi-Turn Degrades

The paper isolates the cause to underspecification + multi-turn interaction (not rephrasing artifacts) via the **Concat** control: when all shards are delivered in a single turn, performance stays within 95% of the Full baseline. The degradation is specifically caused by information being **spread across turns**.

## Four Root Causes (Appendix F)

### 1. Premature Answer Attempts (F.1)

LLMs jump to generating complete solutions before they have enough information. On the first shard (which is intentionally vague/high-level), models already try to produce a full answer rather than asking clarifying questions.

**Quantified impact**: Conversations where the first answer attempt occurs in the first 20% of turns score **30.9** on average, versus **64.4** when the model waits until the last 20%. This is a 2x difference. The effect is consistent across all 15 models tested.

**Mechanism**: The premature solution forces the model to fill in unspecified details with **assumptions**. These assumptions then become anchored in the conversation history and conflict with the actual specifications revealed in later turns.

### 2. Answer Bloat (F.2)

Once a model has made an initial (incorrect) answer attempt, subsequent attempts don't cleanly replace it — they **accumulate** on top of previous wrong answers.

**Quantified impact**: Final answer attempts in sharded conversations are **20-300% longer** than equivalent solutions from single-turn settings. Even when models *do* reach correct solutions in sharded mode, those solutions are bloated — correct Code solutions are 27% longer (850 vs 668 chars), correct SQL queries are 14% longer (129 vs 113 chars).

**Mechanism**: The model overly relies on its previous (incorrect) attempts rather than starting fresh. It tries to patch/extend the previous answer rather than rewrite it, leading to accumulated cruft and incorrect assumptions that were never properly invalidated.

### 3. Loss-in-Middle-Turns (F.3)

LLMs disproportionately attend to information from the **first and last turns**, neglecting middle turns. This mirrors the known "lost in the middle" phenomenon for long-context single-turn, but manifests **across conversation turns**.

**Quantified impact**: In 8-turn summary conversations, 20% of citations come from turn 8 documents vs only 8% from turns 2-3 (a 150% gap). Middle-turn information is systematically under-weighted.

**Mechanism**: The model's attention is drawn to recency (last turn) and primacy (first turn), causing it to over-adjust based on the most recent shard while also anchoring to its initial interpretation from turn 1. Information delivered in middle turns gets relatively ignored.

### 4. Over-Verbosity (F.4)

Longer assistant responses correlate strongly with worse outcomes.

**Quantified impact**: On 5 of 6 tasks, the shortest-response conversations outperform the longest by **10-50%**. The effect is monotonic — performance drops steadily as verbosity increases (avg 40.7 → 35.6 across quintiles).

**Mechanism**: Longer responses introduce more assumptions, hypotheses, and speculative content that gets treated as established context in later turns. Short responses (e.g., a focused clarification question) keep the conversation on track.

## Compounding Cascade

These four failure modes **feed each other** in a vicious cycle:

1. Model receives vague first shard → generates **verbose** response with a **premature** full answer
2. The premature answer contains **assumptions** that fill in unspecified details
3. User reveals the next shard (actual specification) → model tries to patch the previous answer rather than rewrite → **answer bloats**
4. As turns accumulate, middle-turn information gets **forgotten** → model anchors to its (wrong) first attempt and the most recent turn
5. Once "lost," the model **does not recover** — it continues to overly rely on its wrong initial attempt

## What Doesn't Help

- **Reasoning models** (o3, Deepseek-R1): No better at multi-turn — in fact they generate 33% longer responses, introducing *more* assumptions
- **Lower temperature**: Reduces unreliability in single-turn by 50-80%, but only 15-20% in multi-turn (GPT-4o), and **0%** for GPT-4o-mini. Even T=0 for both user and assistant leaves ~30 unreliability
- **Agent-like recapitulation** (Recap/Snowball): Snowball recovers only 15-20% of the degradation; the damage from early wrong turns persists even when all information is restated
- **Model scale**: Larger models have slightly better aptitude but **equally terrible reliability** — all models converge to similar unreliability levels in multi-turn

## The Threshold Effect

The gradual sharding experiment shows the degradation is **binary, not gradual**: as soon as you go from 1 shard (single turn) to 2 shards (two turns), the full reliability collapse occurs. Further increasing the number of shards doesn't substantially worsen things beyond the initial 2-turn drop. This means even minimal underspecification (one piece of information withheld for one turn) triggers the full "lost in conversation" phenomenon.
