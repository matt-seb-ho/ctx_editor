# WORKLOG — Context-management literature survey

Newest entries at the bottom. `[DECISION]` tags mark autonomous choices (deli zero-interaction).

---

## 2026-08-03 — Kickoff (iteration 0)

**Context.** Matthew asked (after reviewing the entanglement-knob deliverable) whether we're
over-indexing on the MIT Huang "assistant-omit" baseline — i.e. beating a strawman. He wants a
literature survey of context-management / context-pollution methods to (a) verify we target real
incumbents, (b) map each method's failure axis vs our entanglement+statefulness knobs, (c)
scooping-check. He's away ~2 days on his intern project; run autonomously per deli principles.

**Memento reality-check (done before kickoff).** The MSR Memento at arXiv 2604.09852 ("Teaching LLMs
to Manage Their Own Context", Kontonis et al.) is *intra-trace KV-cache compression* (segments CoT
into blocks, compresses each to a dense "memento", evicts KV) — reported wins are efficiency
(~2.5× KV cache, ~1.75× throughput) with accuracy preserved on AIME/math/sci/code, NOT a
Terminal-Bench task-accuracy jump. No evidence it evaluates on Terminal-Bench. A *different* Memento
(2508.16153, "Fine-tuning LLM Agents without Fine-tuning LLMs", episodic case-memory) may be
conflated. `[DECISION]` Treat Memento as an instance of *learned summarization/compaction*, relevant
as a method family but not the headline; log the correction for Matthew.

`[DECISION]` **Dedicated effort dir** `research/context_mgmt_survey/` (not buried under
entanglement/notes) with full deli scaffolding (state/, logs/, findings/, WORKLOG) so it can run
continuously and be orchestrated by a cron. Synthesis output still feeds the entanglement paper.

`[DECISION]` **Wave-1 breadth agents run on `sonnet`**, not opus — web search + summarization is well
within sonnet, and this is a 2-day multi-iteration run where cost compounds. Synthesis, citation
verification, and positioning (higher-judgment steps) done by me (opus) in the orchestrator.

`[DECISION]` **Orchestrator = durable cron every ~2h** (deli L1 pattern) that re-invokes a fresh
session to: read state, pick a NEW direction (diversity rule), launch work subagent(s), verify
citations periodically, write back. Anti-runaway stop rule baked into task_spec (§ stopping rule).
Caveat logged: cron fires only while this REPL is idle and alive; if the session is closed the loop
halts (deli L1 depends on a living session). Recurring cron auto-expires after 7 days (> our 2-day need).

**Launched wave 1:** 5 parallel background subagents (one per cluster). Deliverable each:
`findings/clusterN_<name>.md` (method × {mechanism, entanglement-weakness, statefulness-weakness,
verified-URL} table + positioning note) and a returned structured summary + BibTeX. Citation-honesty
required: only papers with a real retrieved URL; unverifiable → `[UNVERIFIED]`.

---

## 2026-08-03 — Wave 1 complete + M2 synthesis (iteration 1)

All 5 breadth agents returned (each wrote its `findings/cluster*.md` + BibTeX; all URLs retrieved
live, zero fabrications reported). Highlights:

- **Exact baseline pinned:** Huang et al., *"Do LLMs Benefit From Their Own Words?"* (arXiv 2602.24287,
  Feb 2026). Coins "context pollution." Crucially it *itself* names its failure case "Follow-up without
  Feedback" (~33% of turns = the entanglement failure) and *explicitly scopes out* stateful tasks and
  calls blind omit "too coarse" (future work: "preserve only the relevant assistant responses").
- **Scooping = CLEAR** (cluster 5). Closest prior: StructFlowBench (categorical inter-turn relationship
  types, but instruction-following compliance, no statefulness, no faithfulness gate); LiC (our base;
  shards self-contained ⇒ entanglement≈0 by design; the concat/omit exploit is exactly what an
  entanglement knob closes); MT-Eval (fixed taxonomy, user→prior-user). Novelty wording captured.
- **LiC = Laban et al.** (arXiv 2505.06120) — Philippe Laban is first author, i.e. the project's mentor
  line. Noted, not overclaimed.
- New finds beyond seed list: **ACON** (arXiv 2510.00615, MSR/ICML 2026) best-in-class *stateful*
  compressor — flagged as a candidate comparator; **ERGO** exact cite (2510.14077); the full
  decontextualization/query-rewrite lineage (Choi TACL'21, CANARD, QReCC, CONQRR, ConvGQR) as the
  closest prior art for our "decontextualize" step (they rewrite for *retrieval*; we rewrite for *safe
  pruning*).

`[DECISION]` **Positioning (answers Matthew's strawman worry):** NOT a strawman *if re-centered*. Lead
with **summarization/compaction** as the production incumbent (Anthropic Compaction API / Cline /
Cursor are shipped evidence), keep assistant-omit as the clean minimal baseline, frame the
contribution as the **entanglement × statefulness two-axis knob**. Unifying diagnosis across all
families: they commit a lossy op (drop/evict/summarize/retrieve-key/archive/reset) *before* resolving
inter-turn references — "prune-then-hope"; ours is **resolve-then-prune**. Wrote this up as
`notes/context_mgmt_survey.md` (cross-cluster matrix + scooping + positioning + method-axis for the
experiments) and `related_work.bib` (38 deduped entries; tau-bench author fix Wu→Yao; MemoryBank/
LLMLingua/Huang/ERGO de-duplicated across clusters).

`[DECISION]` **Method axis for the eventual accuracy sweep:** accumulate-all · assistant-omit ·
summarize (production-representative) · [optional retrieval] · decontextualize-then-edit (ours) ·
[optional ACON on the statefulness axis]. Recorded in progress.json.

**Next (M3):** batch citation-audit all ~38 URLs (deli §9.4); adversarial strawman-refutation pass
(strongest counter to pre-empt: "summarize with a state-preserving prompt already does both" — show it
collapses into a weak form of ours or fails the faithfulness gate). Then M4 depth-reads (Huang, ACON,
StructFlowBench), then M5 one-pager + related-work paragraph folded into the entanglement findings doc.

---

## 2026-08-04 — Orchestrator tick (iteration 2): M3 verify + strawman-refutation

Report-alive. M2 done last tick; advancing to M3. This tick: (a) launched a citation-audit subagent
(sonnet, background) to batch-verify all 38 `related_work.bib` URLs/arXiv ids exist and match
title/authors, writing `findings/citation_audit.md`; (b) writing the adversarial strawman-refutation
myself (opus) → `notes/strawman_refutation.md`. Direction is distinct from iters 0 (breadth) and 1
(synthesis).

`[DECISION]` **Strawman-refutation written** — 8 objections steelmanned + rebutted from survey evidence
(O1 summarize-with-state-prompt ★★★; O2 niche-baseline; O3 contrived-entanglement; O4 retrieval-solves-it;
O5 just-query-rewriting; O6 big-windows; O7 judge-artifact; O8 StructFlowBench-scoops). Verdict: **not a
strawman** — 7/8 answerable by citation today. **O1 is the only paper-threatening one that needs an
experiment, not an argument.** Defined **Experiment E1**: add a `summarize_guided` condition (summarizer
told to preserve referents + state) to the method axis — it either underperforms ours or collapses into
an un-instrumented version of our resolve-then-prune; both outcomes vindicate us. `[DECISION]` Folded
`summarize_guided` into `docs/plans/entanglement_benchmark_spec.md` METHODS list + predictions so it's
actionable when the gradable benchmark is built.

Citation-audit subagent (a9cf…) still running; its `findings/citation_audit.md` + fixes will be applied
next tick (flagged load-bearing cites: huang 2602.24287, laban/LiC 2505.06120, acon 2510.00615, memento
2604.09852, structflowbench 2502.14494, tau2 2506.07982; and `others` author lists to fill).
