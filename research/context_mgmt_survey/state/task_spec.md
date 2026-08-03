# Task spec — Context-management / context-pollution literature survey

**Owner:** Matthew (away ~2 days on intern project; autonomous run).
**Started:** 2026-08-03. **Parent effort:** `research/entanglement/` (Philippe's entanglement-knob eval).

## Goal

Survey the landscape of **context-management** methods that fight **context pollution**
(secondarily context rot) in LLM agents/conversations, so our custom eval targets the *important*
incumbents rather than a strawman. Our eval exposes **entanglement** (user turns depend on/refer to
assistant turns) and **statefulness** (persistent environment state, e.g. τ²-bench) as **independent
variables (knobs)**. Thesis: each incumbent method breaks along one of these axes; our
decontextualize-then-edit survives.

## Why this matters (the strawman worry)

Assistant-omit (Huang et al., MIT) is *one basic method*. If the paper only beats that, it reads as a
strawman. We need to (a) enumerate the real method families, (b) name each one's failure axis
(the "entanglement-analog" weakness), (c) check nobody has already built an entanglement/statefulness
knob (scooping), and (d) decide which incumbent to foreground (hypothesis: **summarization/compaction**,
since that's what production systems actually ship).

## Success criteria

- [ ] ≥5 method clusters covered; each with mechanism + weakness-on-entanglement + weakness-on-statefulness.
- [ ] **Every cited paper has a verified real URL / arXiv id** (no fabrication — deli §9.4). Unverifiable → tagged `[UNVERIFIED]`.
- [ ] Explicit **scooping analysis**: closest prior eval to ours + precisely how we differ.
- [ ] **Positioning recommendation**: which incumbent(s) to foreground and why.
- [ ] Synthesis doc `notes/context_mgmt_survey.md` + `related_work.bib` for the paper's related work.

## Milestones

- **M1 — breadth** (wave 1): 5 clusters surveyed in parallel. → `findings/cluster*.md`
- **M2 — synthesis v1**: merge clusters → `notes/context_mgmt_survey.md` with method×axis matrix + gap/scooping analysis.
- **M3 — verification**: citation-check pass (real URLs); adversarial "is this a strawman?" refutation.
- **M4 — depth**: deep dives on top-2 incumbents; positioning writeup + integration note for the entanglement paper.
- **M5 — deliverable**: `related_work.bib` + a one-page recommendation for Matthew/Philippe.

## Method clusters (initial partition — may be revised on pivot)

1. Summarization / compaction (Memento-intra-trace, recursive summ., LLMLingua, production auto-compact)
2. Memory-augmented agents (MemGPT/Letta, Memento-episodic 2508, Generative Agents, A-MEM)
3. Retrieval-over-history / conversational RAG + its failure modes
4. KV-cache eviction / token pruning / selective context (H2O, StreamingLLM, SnapKV, Huang assistant-omit)
5. Statefulness & multi-turn eval landscape + **scooping check** (τ²/τ-bench, LiC, MT-Bench-101)

## Stopping / anti-runaway rule (deli §6)

When all milestones are done AND 2 consecutive orchestrator iterations yield 0 new substantive
findings → set `status="complete-awaiting-matthew"`, stop launching heavy subagent waves, log and
idle. Do not burn tokens re-surveying a saturated space. `stale_count>=4` → flag for human.
