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
    T8["T8 CollabLLM N=3 replicates<br/>competent user sim<br/>[run]"]
    T9["T9 analyzer-model sensitivity<br/>[todo] — disable analysis_cache"]
    T2A["T2A Tier-A constructed pollution<br/>[todo]"]
    T2C["T2c auditing vs re-solving<br/>[run]"]
    T1["T1 condensation baseline<br/>[todo] — venue unblocked"]
    T11["T11 WildChat judge checks<br/>[todo]"]
    T12["T12-13 memory order / split<br/>[run]"]
    T6["T6 multi-seed tau2<br/>[todo] — harness is an off-machine fork"]
    T2B["T2B counterfactual span ablation<br/>[todo, gold standard]"]
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
| T2c | Auditing vs. re-solving | 2026-07-29 | `tasks/T2c/worklog.md` | 5YHP mechanism challenge |

---

## Dead ends and why

| Direction | Verdict | Reason |
|---|---|---|
| End-to-end tau2 replay | `[dead]` | ~2 dev-days; out of window. Defend replay as causal-attribution design instead; T4 supplies fresh end-to-end evidence on LiC. |
| Full human eval on WildChat | `[dead]` | Out of window. Defend with N=3 seeds + tight intervals; T11 supplies judge-side checks. |
| T5 on math | `[dead]` as a discriminating control | Near-ceiling accuracy compressed all arms to ~97.5%. Needs a high-pollution venue → folded into T1. |
