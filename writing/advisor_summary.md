# Paper Summary: Externalized Executive Function via Self-Aware Context Curation

## The Problem

LLMs degrade in multi-turn conversations as their own prior outputs accumulate in context. Multiple recent works have documented this (Laban et al. "Lost in Conversation," Huang et al. "context pollution," Khalid et al. ERGO). The key observation is that this is primarily a *reliability* failure, not a capability failure: the model can still solve the problem, it just can't reliably access that capability when its own prior (often wrong) reasoning is sitting in context.

## Our Framing

We frame this as a failure of **executive function**: models can't inhibit attention to their own prior reasoning, can't flexibly update their understanding when new information contradicts earlier assumptions, and can't shift strategy when an approach isn't working. We propose **self-aware context curation**: an external agent re-reads the conversation, identifies where the assistant diverged from user intent, and rewrites the context to preserve correct work while removing anchoring content.

## Hypotheses

1. **Context curation > context removal.** Prior work's solution (throw away all assistant messages) works only when rederivation is cheap. In realistic settings where the assistant's prior work matters (tool-use agents, collaborative coding, real conversations), blanket removal should fail. Intelligent curation that preserves correct work while removing harmful content should generalize across settings.

2. **Decomposed analysis is necessary.** A single-pass "review the conversation" approach should underperform decomposing the analysis into (a) extracting a clean task spec from user messages alone, then (b) comparing that spec against the assistant's work. This is because of hypothesis 3:

3. **Assistant messages are a cognitive hazard.** Prior assistant messages don't just pollute the conversational assistant; they should also impair any model analyzing the same context, including an independent reviewer. This means the problem is recursive, and structural attention control (excluding assistant messages from certain analysis steps) is required.

4. **Context curation is learnable.** The quality of the analysis should improve with experience (via accumulated principles from prior trajectories).

## Results

### Controlled study: Lost in Conversation (LiC)

- **Setting:** Simulated multi-turn conversations where simple problems are deliberately fragmented across turns to induce over-anchoring. Tasks: math, code, database, actions.
- **Key finding:** Blanket assistant omission (AO) is a near-optimal upper bound here because the tasks are self-contained and removing assistant messages effectively recovers the single-turn setting. Our methods close most of the gap (e.g., 60%→90% on math with memory, 16%→72% on code) but generally do not exceed AO.
- **Value of this setting:** Controlled environment for ablation. Confirmed the cognitive hazard (hypothesis 3): even an independent reviewer produces degraded analysis when exposed to assistant messages. Also showed that Reset > Augment (removing polluted context helps beyond just appending corrective analysis) and that memory improves analysis quality.

### Real conversations: WildChat (Huang et al. reproduction)

- **Setting:** 30 real human-AI conversations from WildChat-1M. We reproduce Huang et al.'s evaluation, which specifically identified turn types where AO *hurts* (stateful continuations where the user implicitly references prior assistant output).
- **Key finding:** All three of our strategies (Reset, Gated Reset, Rewrite) achieve 82-86% quality win rates against *both* full context and assistant omission across all turn types. Gated Reset is best (86.1% vs AO, 83.8% vs FC) while intervening on only 72% of turns. On the specific turns Huang identified as AO failure cases, our methods are even stronger (up to 93.3%).
- **Why this matters:** This is the sweet spot finding. Our method outperforms both doing nothing *and* the strongest prior baseline, on real conversations where context pollution occurs naturally (not through simulation).

### Real conversations: CollabLLM

- **Setting:** Genuinely collaborative multi-turn interactions (MATH-Hard, BigCodeBench) where user and assistant build on each other's work.
- **Key finding:** Rewrite improves over baseline (+5pp on math, +20pp on code). No AO comparison run here.

### Agentic tool use: tau2-bench

- **Setting:** Complex agentic conversations with tool calls, API lookups, and state tracking (telecom customer service).
- **Key finding:** AO catastrophically fails (0% vs 55% baseline) because removing assistant messages also removes all tool results the agent depends on. Our Gated Reset maintains or improves (55-60%). However, diagnostic analysis reveals context pollution is not the dominant failure mode in this subset; the improvement comes more from strategic reflection (redirecting the agent to try new approaches) than from removing anchoring.
- **Additional finding:** The Rewrite variant (LLM-generated context) underperforms (25-40%) because the LLM rewrite step loses structured tool data. Programmatic templates preserve data fidelity better in this setting.

### Cognitive hazard (ablation)

- **Finding:** When the analyzer sees assistant messages during task spec extraction ("soft attention"), analysis quality collapses to baseline or worse. This is not a prompting failure. It demonstrates that context pollution is contagious: it impairs any model processing the same context, not just the original conversational assistant.
- **Partial mitigation:** Memory-based decontamination (Dynamic Cheatsheet applied to soft-attention analysis) closes up to 65% of the gap to hard-attention oracles on structured tasks, showing that resistance to the cognitive hazard can be partially learned.

## Conclusions / Story

1. **Context curation works where it's needed most.** The value of curation over removal scales with setting complexity. On simple benchmarks, removal is a fine upper bound. On real conversations, curation wins across the board. On agentic settings, removal is catastrophically destructive while curation maintains performance.

2. **Gated Reset is a robust default.** The same strategy (analyze, intervene only when issues found, use programmatic templates) is the best or joint-best performer across all settings. Conservative intervention that avoids unnecessary disruption beats both unconditional intervention and LLM-mediated rewriting.

3. **The cognitive hazard is real and underappreciated.** Assistant messages degrade even independent reviewers. This has implications beyond our specific method: any multi-stage LLM system where a downstream model processes outputs from an upstream model may be susceptible.

4. **The framework is flexible.** The shared analytical core (decomposed analysis with structural attention control) is the contribution; the intervention strategy (Augment/Reset/Rewrite, gated or unconditional) is a design choice practitioners tune to their setting.
