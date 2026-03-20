# Context Editing for Multi-Turn Conversations: Project Motivation

## 1. The Problem: LLMs Get Lost in Conversation

Laban et al. (2025) document a systematic failure of LLMs in multi-turn, underspecified conversations. Through large-scale simulation (200,000+ conversations, 15 LLMs, 6 tasks), they show that when task instructions are revealed incrementally across turns — mimicking how real users naturally communicate — model performance drops by 39% on average compared to receiving the full instruction in a single turn.

### 1.1 It's a Reliability Problem, Not an Aptitude Problem

The paper decomposes the degradation into two components:
- **Aptitude** (best-case performance): drops only ~16%
- **Unreliability** (variance between best and worst runs): increases by 112%

The models *can* still solve the problems — in the best 10% of runs, they perform nearly as well as single-turn. But in the majority of runs, they fail catastrophically. All 15 models tested, from Llama3.1-8B to Gemini 2.5 Pro, exhibit similarly high unreliability in multi-turn settings regardless of their single-turn capability.

### 1.2 Root Causes

The paper identifies four failure modes through analysis of simulation logs:

**Premature answer attempts.** LLMs jump to generating complete solutions before they have enough information. Conversations where the first answer attempt occurs in the first 20% of turns score 30.9 on average, versus 64.4 when the model waits until the last 20%. The premature solution forces the model to fill in unspecified details with assumptions, which then anchor the model even when contradicted by later user messages.

**Answer bloat.** Once the model has made an incorrect attempt, subsequent attempts don't cleanly replace it — they patch and extend the previous answer. Final answers in multi-turn conversations are 20–300% longer than equivalent single-turn solutions. Even correct solutions obtained in multi-turn are bloated (27% longer for code, 14% for SQL).

**Loss-in-middle-turns.** LLMs disproportionately attend to information from the first and last turns, neglecting middle turns. In 8-turn conversations, 20% of citations come from turn 8 documents versus only 8% from turns 2–3. This mirrors the known "lost in the middle" phenomenon but manifests across conversation turns rather than within a single context.

**Over-verbosity.** Longer assistant responses correlate with worse outcomes. On 5 of 6 tasks, the shortest-response conversations outperform the longest by 10–50%. Longer responses introduce more assumptions and speculative content that gets treated as established facts in later turns.

### 1.3 The Cascade

These failure modes compound: the model receives a vague first message, generates a verbose premature answer full of assumptions, then when corrected, patches rather than rewrites, causing the answer to bloat. As turns accumulate, middle-turn information is forgotten and the model anchors to its initial (wrong) attempt. Once lost, it does not recover.

### 1.4 What Doesn't Help

- **Reasoning models** (o3, Deepseek-R1): generate 33% longer responses, introducing more assumptions.
- **Lower temperature**: reduces single-turn unreliability by 50–80% but only 15–20% in multi-turn. Even T=0 for both parties leaves ~30 unreliability.
- **Agent-like recapitulation** (Recap/Snowball): restating all user information within the same conversation recovers only 15–20% of the degradation. The damage from early wrong turns persists.
- **Model scale**: all models converge to similarly high unreliability in multi-turn.

### 1.5 The Threshold Effect

The gradual sharding experiment shows the degradation is binary: as soon as you go from 1 turn to 2 turns, the full reliability collapse occurs. Even minimal underspecification triggers the phenomenon.

### 1.6 Current Band-Aid

The only effective user-side mitigation is to notice when the model is lost, ask it to consolidate everything discussed so far, and bring that consolidation into a **new conversation** — effectively converting multi-turn back into single-turn. Restating information within the same conversation is insufficient because the model still anchors on its prior incorrect attempts.

## 2. Existing Approaches

### 2.1 ERGO: Entropy-Guided Resetting (Khalid et al., 2025)

**Mechanism.** ERGO monitors the model's average token-level Shannon entropy at each turn. When the change in entropy between consecutive turns exceeds a calibrated threshold τ, it triggers a context reset: all prior user messages are summarized into a single prompt, assistant messages are discarded, and generation continues in a fresh context.

**Decision logic.** Hardcoded: entropy delta > threshold. The threshold is calibrated per-model.

**Reset operation.** Summarize user messages into a single prompt, discard all assistant messages, start a new context branch.

**Results.** On the LiC simulator, ERGO achieves a 56.6% average performance gain over the sharded baseline, increases aptitude by 24.7%, and reduces unreliability by 35.3%. Entropy-guided resets outperform both random and fixed-interval reset baselines.

**Limitations.**
- Requires logprob access, which is limited for many API-served models (e.g., OpenAI only provides top-20 logprobs, degrading entropy estimates).
- Discards all assistant messages — equivalent to recovering the Concat/single-turn baseline, which the LiC paper explicitly shows performs at ~95% of full single-turn.
- Evaluated only on the LiC synthetic simulator, not on real-world conversations.
- Uses a simplified version of the LiC simulator that feeds shards directly as user messages rather than using an LLM to simulate natural user rephrasing.
- Risk of semantic drift: poorly timed resets can lose critical details through over-abstraction.

### 2.2 Huang et al. (2026): "Do LLMs Benefit from Their Own Words?"

**Core finding.** On real-world multi-turn conversations (WildChat, ShareLM), omitting all prior assistant responses frequently does not hurt — and sometimes improves — response quality. 36.4% of turns in real conversations are self-contained "new asks" that don't depend on prior assistant output at all.

**Mechanism.** They test three context configurations: full context (FC), assistant-omitted (AO, replacing assistant messages with "[Response provided]"), and summarized (replacing assistant messages with one-sentence summaries).

**Decision logic.** For their adaptive approach, they train an L1-regularized logistic regression classifier on metadata (round number, context lengths), prompt category (new ask / follow-up with/without feedback), and PCA-reduced embeddings of the user prompt and conversation history. The classifier predicts per-turn whether FC or AO will produce better results. This is a shallow statistical model, not LLM-driven reasoning.

**Results.**
- On LiC: both DeepSeek-R1-Distill-Llama-8B and Qwen3-4B improve with assistant omission. One-sentence summaries beat full context for both models on both LiC and WildChat.
- The adaptive classifier retains >95% of FC performance at 70% of context consumption for GPT-5.2.
- They identify "context pollution" as a core phenomenon: earlier assistant outputs introduce errors, hallucinations, or stylistic artifacts that propagate across turns.

**Limitations.**
- The LiC experiments use straight AO vs FC comparisons without the adaptive classifier, and the improvement there is essentially recovering the single-turn baseline.
- The adaptive classifier is trained per-model and requires labeled preference data from an LLM judge.
- Makes a binary choice (full context vs. completely omit) per-turn — no surgical editing of what to keep or discard within a response.
- Does not evaluate whether preserving useful portions of assistant responses could outperform full omission.

### 2.3 The Exploit Problem

Both ERGO and Huang's approaches, when applied to LiC, essentially recover the single-turn Concat baseline by removing assistant messages and concatenating (or summarizing) user messages. The LiC paper explicitly shows that Concat performance is within 95% of the original single-turn Full baseline. This means strong results on LiC can be achieved by the trivial strategy of ignoring everything the assistant said — which is not a realistic solution for deployed systems. LiC is valuable as a demonstration of the problem, but should not be treated as a benchmark to hill-climb on.

## 3. Our Approach: Context Editing

We propose a context editing system that automatically detects when the assistant is lost and surgically rewrites the conversation history to remove incorrect assumptions and failed attempts while preserving useful progress. The key metaphor is "hard attention": future generation cannot attend to previous bad content because it has been literally removed from context.

### 3.1 How It Differs

Our approach has three key differentiators from prior work:

#### 3.1.1 LLM-Driven Decision Making

Both ERGO (entropy threshold) and Huang (logistic regression on embeddings) use hardcoded or shallow statistical signals to decide when to intervene. We use the LLM itself to analyze the conversation and determine whether a reset or edit is needed.

**Why this matters:**

- **Generality.** Works with any black-box API. Does not require logprob access (unlike ERGO, which degrades when only top-20 logprobs are available) or model-specific training data from an LLM judge (unlike Huang's classifier).
- **Richer signal.** Entropy detects that the model is uncertain, but not *why*. An LLM can reason about whether uncertainty stems from conflicting assumptions, missing information, or genuine problem difficulty. Not all uncertainty means the model is lost.
- **Actionable granularity.** An LLM can decide *what specifically* to discard — particular incorrect assumptions, a flawed code block, a wrong equation — rather than making a binary reset/don't-reset or keep/omit choice.
- **Training target.** If the model can recognize when it's confused through prompting, this capability is a natural target for reinforcement learning or fine-tuning, suggesting a path toward models that natively handle multi-turn recovery.

#### 3.1.2 Preserving (Edited) Assistant Messages

ERGO discards all assistant messages on reset. Huang's primary intervention omits all assistant messages entirely, and their one-sentence summary variant is an aggressive compression that loses most content. We instead surgically edit assistant messages to remove harmful content while preserving useful progress.

**Why this matters:**

- **Preserving useful work.** In real conversations, the assistant may have done correct partial work — valid sub-computations, correct code structure, right approach with wrong parameter details. Full omission forces complete re-derivation of everything, including the parts that were right.
- **User message coherence.** In real deployments, user messages frequently reference assistant messages: "The second one is not working," "Use the approach from before but change X." These user turns become meaningless without assistant context. Huang acknowledges this — 33.1% of turns are "follow-up without feedback" that reference assistant outputs. The LiC simulator sidesteps this issue because shards are designed as self-contained user specifications, but this does not reflect real usage.
- **Not an exploit.** Because we preserve (edited) assistant content rather than discarding it, our approach cannot trivially recover the Concat baseline. Improvements must come from genuinely useful editing decisions, making results on LiC more meaningful.
- **Deployment realism.** In a real system, an assistant that completely "forgets" what it just said would be jarring. Selective editing is more natural and user-compatible than wholesale amnesia.

Huang's results actually support this position: their finding that one-sentence summaries beat both full context *and* full omission on LiC and WildChat suggests that the right answer is neither keeping everything nor discarding everything, but intelligent compression — which is what context editing provides with finer granularity.

#### 3.1.3 Memory-Based Learning

All prior approaches use static intervention logic: ERGO's entropy threshold is calibrated once, Huang's classifier is trained once. We incorporate a persistent text-based memory system that allows the context editing operation to improve over time.

**Two application modes:**

**(a) Memory on the context editor.** The editor/analyzer learns patterns from past editing decisions:
- "When the assistant's response contains 'I'll assume X' and the next user message contradicts X, strip the assumption and dependent code"
- "On math tasks, preserving equation setup but removing numerical computation is better than keeping the full response"
- "When the assistant generates >N tokens on the first turn, the response almost always contains incorrect assumptions that should be pruned"

This makes the editing operation adaptive and improvable rather than hardcoded. The editor builds up domain-specific knowledge about what kinds of assistant content are harmful versus helpful.

**(b) Memory on the assistant.** The assistant itself accumulates task-level insights across conversations — for example, learning that on incrementally-specified coding tasks, it should resist committing to a full implementation until enough constraints are provided. This is a more ambitious target with a bootstrapping challenge (the assistant needs to fail first to learn), but could eventually produce models that natively avoid the "lost in conversation" failure mode.

### 3.2 Summary of Differentiators

| Dimension | ERGO | Huang et al. | Ours |
|---|---|---|---|
| When to intervene | Entropy threshold (hardcoded) | Logistic regression on embeddings (statistical) | LLM-driven reasoning (semantic) |
| What to do | Summarize user msgs, discard assistant msgs, restart | Binary: keep all or omit all assistant msgs per-turn | Surgically edit assistant msgs to remove harmful content |
| API requirements | Logprob access | Embedding model + judge training data | Black-box LLM access only |
| Evaluation setting | LiC synthetic only | LiC synthetic + real-world (WildChat, ShareLM) | LiC synthetic (primary) |
| Learning | None (static threshold) | None (static classifier) | Memory-based continuous improvement |
| LiC exploit risk | High (recovers Concat) | High (recovers Concat) | Low (preserves edited assistant content) |
