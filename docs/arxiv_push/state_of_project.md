# AC3 — State of the Project (2026-07-09)

A get-back-up-to-speed overview after time away, written at the start of the post-NeurIPS → arXiv push. Companion docs: [`arxiv_revision_plan.md`](arxiv_revision_plan.md) (the plan), [`worklog.md`](worklog.md) (what was done this session), [`../jun1_megatable_findings.md`](../jun1_megatable_findings.md) (paper-change punch list).

---

## 1. What the project is (one paragraph)

**AC3 = Agentic Conversation Context Curation** (paper title: *Agentic Context Management for Multi-Turn Human–AI Conversations*). LLMs degrade in multi-turn use because their own earlier outputs accumulate and anchor later turns — "context pollution" (Laban et al. LiC; Huang et al.). Prior fixes just **omit all assistant messages (AO)**, which works only when user turns are self-contained. AC3 instead runs a **separate analyzer** between turns that (1) consolidates a clean spec from *user messages alone* (structurally shielded from assistant text), (2) audits the assistant's work against it, and (3) edits the context via one of three operators — **Augment / Reset (+Gated) / Rewrite** — keeping verified work and removing invalidated reasoning. Headline non-obvious finding: **pollution is contagious** — if the analyzer sees assistant reasoning while building the spec, downstream accuracy drops *below* doing nothing.

## 2. Where the paper stands

- **Live draft:** `writing/overleaf_repo/neurips/neurips_2026_conference.tex` (816 lines, ~9pp + appendices). Recovered this session from the Azure blob snapshot (see §5). Inner-repo HEAD `d211637`.
- A version was **submitted to NeurIPS**; this is the **post-NeurIPS revision** headed for arXiv to plant the flag before the work goes stale.
- **Three result tables:**
  - Table 1 `tab:main` — per-task LiC, GPT-5-mini headline (math/code/database/actions).
  - Table 2 `tab:megatable` — **the new mega-table**: 3 respondents (GPT-5.4 / DSV4F / Kimi-K2.6) × {LiC, CollabLLM, tau2-bench}.
  - Table 3 `tab:wildchat` — WildChat pairwise win-rates × the same respondents + GPT-5-mini.
- **The mega-table numbers are already baked into the draft** (Tables 2/3, §5.3–§5.4, and a §6 "appropriate intensity" paragraph). So the big integration work from the post-NeurIPS scale-up is *done*. What remains is reconciliation + polish (§4 below).

## 3. What the post-NeurIPS scale-up added (the "mega-table" story)

The scramble before submission meant each benchmark used slightly different prompts/orchestration. The post-NeurIPS rounds (R2–R6 + tau2-canonical, see `docs/reports/post_may18_*` and `post_may26_megatable_round_summary.md`) unified the analyzer (v8 on text, v11 port on tau2) and scaled to 3 extra respondent models across all 4 benchmarks. New load-bearing findings:

1. **AO collapses to 0% on tau2-bench across *all* respondents** — strongest form of "blanket omission destroys tool-call state."
2. **Every AC3 operator beats Baseline on tau2**, by **+15.8 to +47.4pp** — and the *winning operator scales with respondent strength*: strongest model (gpt-5.4) → lightest operator (Augment); weakest (Kimi) → heaviest (Rewrite). This grounds the "appropriate intensity: one analyzer, many operators" framing in cross-model data.
3. **Rewrite already wins on the open-ended/referential end** (WildChat×Kimi 91.5%, tau2×Kimi 73.7%) — undercuts the draft's "forward-looking, we expect it to win eventually" hedge.
4. **Gated-Reset vs always-on Reset is asymmetric**: on strong respondents (WildChat×gpt-5.4) gating *underperforms* always-on Reset by 14.5pp (false-negative gate-closes). Qualifies the "Gated-Reset is the safe default" recommendation.
5. **LiC generalization is now multi-model** on the *default* subset (not just the harder GPT-5.2 subset in the appendix).

## 4. What's left for the arXiv version

**Priority 1 — reconcile stale claims with the new results (claim–evidence bug).** The Results section (§5.4) was updated to the multi-model tau2 story, but the **Abstract (l.110), Figure 1 caption (l.122), Introduction (l.139), and Conclusion (l.405)** still describe tau2 as AC3 merely *"remains viable / stays within trial noise of baseline."* That now **contradicts Table 2** (AC3 beats Baseline +15.8–47.4pp). These four spots must be upgraded to the "substantially beats Baseline, AO→0%" framing. (The "within trial noise" language is only correct for the *gpt-5-mini* cell at l.360/l.558 — keep it scoped there.)

**Priority 2 — apply the remaining `jun1_megatable_findings.md` items** not yet in the draft: soften the §3.2 Rewrite "we expect… as capabilities improve" hedge (2c); make the Abstract "~60%→0%" respondent-agnostic (2d); land the two-point Conclusion (curation>omission **and** match intensity to respondent) (3a); add a Table 2 pointer in §3.2 (3b); expand the one-liner §5.2 CollabLLM into a proper paragraph (3c).

**Priority 3 — writing polish for arXiv first impression** (abstract readability, flow, terminology consistency), guided by the `research-paper-writing` skill and the adversarial subagent debate in `debate/`.

**Not in scope for this pass** (logged in [`followup_experiments.md`](followup_experiments.md)): new experiments — tau2 Kimi baseline at workers=2, WildChat Gated-Reset for DSV4F/Kimi, multi-seed tau2, CollabLLM Reset content-filter refix.

## 5. Data / recovery status (do we need the blob?)

- **Mega-table data: fully in-repo** — no blob needed for numbers. Canonical: `docs/reports/post_may18_progress_update_v4_bandaid_tau2.html`; provenance `post_may26_megatable_round_summary.md`.
- **Live paper:** was the one gap (gitignored, not in the GitHub backup). Recovered from `ctx_editor_full_snapshot_2026-06-12.tar.gz` on the blob, with full `.git`.
- **Claude Code sessions from the old server:** never backed up — unavailable.
- **tau2_ctxe / collabmem / lic code + raw outputs:** on GitHub (`matt-seb-ho/tau2_ctxe`, `collabmem`) or in the 289 MB supplementary tarball (downloaded to `ac3/blob_staging/`). Only needed if we re-run experiments.
- ⚠ **The Overleaf-connected remote (`mgalley/AgenticContextManagement-for-Multi-Turn-LLM-Conversations`) is unreachable from this machine.** So paper edits are committed to the local inner repo but can't yet be pushed to Overleaf — you'll need to sort access, or pull from Overleaf into a repo we can push to, or hand-copy the `.tex`.

## 6. Where things live (quick map)

| Thing | Path |
|---|---|
| Live paper | `writing/overleaf_repo/neurips/neurips_2026_conference.tex` |
| Paper backup (pre-edit, SHA d211637) | `docs/arxiv_push/backups/neurips_2026_conference.d211637.tex` |
| Mega-table (canonical) | `docs/reports/post_may18_progress_update_v4_bandaid_tau2.html` |
| Paper-change punch list | `docs/jun1_megatable_findings.md` |
| This arxiv push (plan/debate/worklog) | `docs/arxiv_push/` |
| Downloaded blob tarballs | `/home/t-matthewho/ac3/blob_staging/` |
| Doc index | `docs/index.md` |
