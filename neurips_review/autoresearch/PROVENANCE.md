# Provenance Graph — AC3 Experimentation

What was run, in what order, why, and what each run's numbers were used for. This is the "how did we get here" map; the running narrative is in [`WORKLOG.md`](WORKLOG.md).

Conventions: `[done]` result in hand · `[run]` executing · `[todo]` planned · `[blocked]` waiting on a dependency · `[dead]` abandoned, with reason.

---

## Lineage

```mermaid
graph TD
  subgraph PAPER["NeurIPS submission 27902 (submitted)"]
    P0["LiC main matrix<br/>n=18-25/cell"]
    P1["tau2 sweep<br/>seed 42, N=1"]
    P2["WildChat judge<br/>N=3"]
    P3["CollabLLM<br/>N=1, weak user sim"]
  end

  R["Reviews: 3x borderline reject<br/>Vg97 / 5YHP / iNYK + AC"]
  PAPER --> R

  subgraph S1["Session 1 - 2026-07-27"]
    T3["T3 paired significance<br/>Reset +15.9pp, 33/36, p&lt;1e-4<br/>[done] zero API cost"]
    T4["T4 random unbiased subset<br/>N=3 end-to-end<br/>Baseline 87.5+/-2.0, Reset 100.0+/-0.0<br/>[done]"]
    T5["T5 equal-budget control<br/>near-ceiling math, non-discriminating<br/>[done, inconclusive]"]
  end
  R --> S1

  subgraph S2["Session 2 - 2026-07-29 (this session)"]
    BLK["BLOCK-spider<br/>Spider SQLite DBs recovered<br/>17/17 db_ids, test-suite semantics<br/>[done]"]
    RC["RECON<br/>harness map + operator naming<br/>[done] — found inert-seed bug"]
    T8["T8 CollabLLM N=3 replicates<br/>math-hard 100% DOES NOT replicate<br/>bigcodebench +15pp 3/3 survives<br/>[done]"]
    T9["T9 analyzer-model sensitivity<br/>graceful degradation, all 5 positive<br/>non-gpt takes top rung<br/>[done]"]
    T2A["T2A Tier-A constructed pollution<br/>removal 97.6%, precision 50.4% (=chance)<br/>Reset not surgical<br/>[done]"]
    T2C["T2c auditing vs re-solving<br/>+20.7pp on NO_LEAK subset<br/>math conceded<br/>[done]"]
    T1["T1 condensation baseline<br/>summarisation does NOT close gap<br/>over-budget and still loses<br/>[done]"]
    T11["T11 WildChat judge checks<br/>position bias real but pre-randomised<br/>headline survives, -2.0/-0.9pp<br/>[done]"]
    T12["T12-13 memory order / split<br/>order NOT distinguished; learner noise ~6pp<br/>contamination = zero<br/>[done]"]
    T6["T6 multi-replicate tau2<br/>[run] — fork cloned outside tree"]
    T2B["T2B counterfactual span ablation<br/>[run] — natural spans, causal labels"]
    T15["T15 claims audit -> replies/v5<br/>64 claims: 24 unchanged, 14 corrected,<br/>6 struck, 11 added, 5 unverified<br/>[done]"]
    T16["T16 verify gate stats<br/>claim exact; wording wrong<br/>firing rate != detection rate<br/>[done]"]
    T14["⚠ T14 FN-adjustment audit<br/>adjusted_accuracy inflates our own<br/>numbers 89.0 -> 77.1<br/>[run]"]
    SEED["⚠ inert-seed finding<br/>LiC + CollabLLM reps are<br/>temperature-only, not seeded"]
  end
  S1 --> S2

  RC --> SEED
  SEED -.->|"invalidates 'seeds' wording"| T4
  SEED --> T8
  RC --> T8
  RC --> T9
  RC --> T6
  RC --> T11
  BLK --> T1
  BLK --> T2A
  T5 -.->|"non-discriminating on math;<br/>re-run on high-pollution task"| T1
  T2A --> T2B
  T2C --> T2B
  T1 --> T14
  T14 -.->|"LiC figures provisional"| T15
  T6 -.->|"⚠ baselines may not replicate"| T15
  T15 --> T16
  T14 -.->|"corrects magnitudes in"| P0

  P3 -->|"N=1 claim we already<br/>assert in replies/v4"| T8
  P1 -->|"N=1 claim"| T6
```

---

## Run ledger

| ID | Run | Date | Config / artifact | Feeds |
|----|-----|------|-------------------|-------|
| T3 | Paired significance across LiC matrix | 2026-07-27 | `neurips_review/experiments/paired_analysis.py`, `paired_analysis_results.txt` | General Response; AC reply |
| T4 | Random unbiased subset, end-to-end N=3 | 2026-07-27 | `neurips_review/experiments/exp1_reps_results.txt`; `data/rebuttal_random_math40.json`; `outputs/rebuttal_random/` | iNYK Q1 |
| T5 | Equal-budget reflection control | 2026-07-27 | `neurips_review/experiments/exp2_results.txt` | Vg97 Q3 (compute half) |
| BLOCK-spider | Spider DB acquisition | 2026-07-29 | `tasks/BLOCK-spider/worklog.md`; `data/spider/databases/` (4.9 GB, gitignored) | T1, T2A, T5-redo |
| RECON | Harness / naming map | 2026-07-29 | `tasks/RECON/worklog.md` | T8, T9, T6, T11 |
| T2c | Auditing vs. re-solving | 2026-07-29 | `tasks/T2c/worklog.md`, `tasks/T2c/RESULTS.md`; source traces `~/ac3/recovered_t2c/` | 5YHP mechanism challenge — **+20.7pp on leak-free subset**, math conceded |
| T9 | Analyzer-model sensitivity | 2026-07-29 | `tasks/T9/worklog.md` | Vg97 Q3 (unanswered half) |
| T12/T13 | Memory order-sensitivity + split | 2026-07-29 | `tasks/T12-T13/worklog.md` §9 | 5YHP W6 — **contamination zero (helps)**; memory gains below noise floor (hurts) |
| T1 | Condensation baseline | 2026-07-29 | `tasks/T1/worklog.md` | Vg97 W1/Q1 + **AC "limited baselines"** |
| T8 | CollabLLM 3 replicates | 2026-07-29 | `tasks/T8/worklog.md` | 5YHP — **math-hard 100% struck**; bigcodebench +15pp 3/3 + disjoint draw |
| T2A | Tier-A constructed pollution | 2026-07-29 | `tasks/T2A/worklog.md` | 5YHP W5 detector story |
| T9 | Analyzer-model sensitivity | 2026-07-29 | `tasks/T9/worklog.md` (`1f4f32d`) | Vg97 Q3 — **graceful degradation, +12.9 to +39.9 pp across 5 analyzers** |
| T6 | Multi-replicate tau2 | 2026-07-29 | `tasks/T6/worklog.md`; fork at `~/ac3/tau2_ctxe` | iNYK — largest remaining statistical hole |
| T2A | Tier-A constructed pollution | 2026-07-29 | `tasks/T2A/{RESULTS.md,inject.py,measure.py}` (`88cacb3`); `outputs/T2A/` | 5YHP W5 — **detection 97.6% / naming 78.6%; selectivity at chance for Reset** |
| T11 | WildChat judge checks | 2026-07-29 | `tasks/T11/worklog.md` | 5YHP W4 (promised in replies/v4) |
| T1 | Condensation baseline | 2026-07-29 | `tasks/T1/{worklog.md,RESULTS.md,analyze.py}`; `outputs/T1/` | Vg97 W1/Q1 + AC — **summarisation −2.8 to −8.4 pp vs AC3-Reset +19.6 pp** |
| T14 | FN-adjustment audit | 2026-07-29 | `tasks/T14/worklog.md` | **Corrects the paper's headline LiC magnitudes** |
| T11 | WildChat judge checks | 2026-07-29 | `tasks/T11/{worklog.md,out/}` | 5YHP W4 — bias real but pre-randomised; corrected 87.8 / 91.2 |
| T15 | Claims audit → `replies/v5/` | 2026-07-29 | `replies/v5/{CHANGES.md,README.md}` (`5775f71`); `tasks/T15/worklog.md` | Lands F1–F33 in the submitted text; **found F34/F36/F37** |
| T16 | Verify gate statistics | 2026-07-29 | `tasks/T16/{worklog.md,gate_stats.py,report.md}` (`8d545ff`) | F38/F39 — claim exact, wording corrected in v5 (`e889c17`) |
| T2B | Counterfactual span ablation | 2026-07-29 | `tasks/T2B/worklog.md` | Upgrades T2A's synthetic injections to **natural** spans |

---

## Dead ends and why

| Direction | Verdict | Reason |
|---|---|---|
| "BigCodeBench cannot be evaluated with executable tests" | `[dead]` | Factually wrong — T8 §5 shows that path runs real `untrusted_check` execution. We conceded a limitation that does not exist; struck along with the dependent judge-discrimination figures. |
| Rebuttal end-to-end "AC3-Reset 100.0 ± 0.0" | `[dead]` | FN-adjusted with asymmetric exclusions (Reset 1/2/5 items, baseline 0). Raw: 87.5 ± 2.0 / 93.3 ± 4.2 / 95.0 ± 0.0. Claim survives; the perfect score does not. |
| MT-OSC as a fair pollution baseline | `[dead]` | T1: at published w=4 it fired 0.3×/conversation — it cannot touch context before turn 6 and LiC conversations average 4.1 turns. Report as *structurally inapplicable*, which supports our scoping argument, rather than as a beaten baseline. |
| End-to-end tau2 replay | `[dead]` | ~2 dev-days; out of window. Defend replay as causal-attribution design instead; T4 supplies fresh end-to-end evidence on LiC. |
| Full human eval on WildChat | `[dead]` | Out of window. Defend with N=3 seeds + tight intervals; T11 supplies judge-side checks. |
| T5 on math | `[dead]` as a discriminating control | Near-ceiling accuracy compressed all arms to ~97.5%. Needs a high-pollution venue → folded into T1. |
| Quoting single-trial memory gains (+10/+12 pp) | `[dead]` | T12: below the learner's own ~6 pp noise floor; N=4 remeasure gives −5.0/−8.0 pp. Lead with T13's zero-contamination result instead (D7). |
| "We preserve what's correct and remove what's harmful" (as a claim about **Reset**) | `[dead]` | T2A: edit precision 50.4% vs 50% chance, preservation 4.0%. Reset discards the assistant side wholesale and re-derives from the user side. The selectivity claim belongs to **Rewrite** (27.0 / 38.9). Attribute, don't retract. |
| `analysis_cache` as a T9 confound | `[dead]` | Resolved, not worked around: `make_key()` includes analyzer model identity (`analysis_cache.py:92`); call site passes live model (`analyzer.py:587`). Cache disabled anyway + per-trace audit. |
| CollabLLM math-hard "100%" claim | `[dead]` | T8 N=3: 91.7 ± 7.6 vs Baseline 91.7 ± 5.8, identical 55/60 totals. Near-ceiling decoding noise. Say "matches Baseline" — still refutes the regression. |
| "Memory is order-robust" framing | `[dead]` | T12 variance controls: across-ordering std (6.5) does not exceed same-ordering std (6.1). Ordering is not a distinguished factor; the learner is just noisy. |
