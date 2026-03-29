# Paper Summary (Short)

**Title:** Externalized Executive Function via Self-Aware Context Curation

**Problem:** LLMs degrade in multi-turn conversations because they anchor on their own prior (often wrong) outputs. Prior fix: throw away all assistant messages. Works on simple benchmarks but breaks in realistic settings.

**Our approach:** An external agent analyzes the conversation in two steps (extract user intent without seeing assistant messages, then compare against assistant's work), and rewrites the context to keep what's correct and remove what's harmful.

**Key finding:** Assistant messages are a "cognitive hazard" -- they degrade even an independent reviewer's analysis, not just the original assistant. This is why the two-step decomposition (shielding intent extraction from assistant messages) is necessary, not just nice-to-have.

## Results across 4 settings (escalating complexity)

| Setting | Blanket removal (AO) | Our method | Takeaway |
|---------|---------------------|------------|----------|
| LiC (controlled) | ~80% (upper bound) | 44-90% (closes gap) | AO trivially wins here; we use this for ablation |
| CollabLLM (collaborative) | not tested | +5-20pp over baseline | Method helps in collaborative settings |
| WildChat (real conversations) | loses on stateful turns | **84-86% win rate vs both AO and full context** | Strongest finding: beats both baselines on real data |
| tau2-bench (agentic/tool-use) | **0%** (catastrophic) | 55-60% (maintains/improves) | AO is destructive; curation is necessary |

## LiC ablations

- **Cognitive hazard:** Letting the analyzer see assistant messages during intent extraction collapses performance to baseline or worse (e.g., math 80%→40%). Even an independent reviewer anchors on the assistant's reasoning. This is the empirical motivation for the two-step decomposition.
- **Contamination compounds across chained calls:** Two-step soft-attention (contaminated spec → contaminated eval) performs *worse* than single-pass soft-attention. Pipeline chaining amplifies errors when early stages are contaminated.
- **Augment vs Reset:** Appending analysis without removing polluted context (Augment) underperforms replacing the context entirely (Reset) on code (+13pp), database (+8pp), actions (+8pp). The anchoring effect of polluted context is measurable and separable from intent fragmentation.
- **Memory (Dynamic Cheatsheet):** Improves analysis quality (math 80%→90%), showing curation is learnable. In the soft-attention setting, memory closes up to 65% of the gap to hard-attention oracles on database. Not a novel method (we apply an existing technique), but evidence that the curation capability can be improved.

## Core claims

1. Context curation > context removal, with the gap growing as conversations become more stateful
2. The cognitive hazard (assistant messages impairing analysis) requires structural attention control, not better prompting
3. Gated intervention (only intervene when issues detected) is the best default across all settings
