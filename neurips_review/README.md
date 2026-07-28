# NeurIPS Review / Rebuttal Working Folder

Submission 27902 (AC3). Reviews came back 3x Borderline-reject with the AC leaning reject.

## Start here

| What you want | File |
|---|---|
| **The comments to actually post** | `replies/v3/` (post `00_general_response.md` first) |
| What experiments to run next | `experiment_todos.md` |
| Rebut vs withdraw-for-ICLR | `strategy.md` |
| Paper edits the rebuttal commits to | `paper_edits_needed.md` |
| Session decisions and results log | `worklog.md` |

## Reply versions

Comment drafts are versioned in folders. Each revision gets a new folder; the previous version is preserved unchanged.

* `replies/v1/` - first pass, concede-then-convert register. **Superseded.**
* `replies/v2/` - projects strength, leads with the post-submission matrix, adds paired significance. **Superseded.**
* `replies/v3/` - **current.** Restructured to the LaDiR house format recommended by the advisor: thematic Common Weakness sections, reviewer text quoted with W/Q labels, explicit revision commitments, closing summary post. See `replies/v3/README.md`.

`ladir_rebuttal.md` is the reference rebuttal the format is modelled on.

## Background documents (analysis, not for posting)

| File | Contents |
|---|---|
| `ac3_reviews_raw.md` | Original OpenReview paste |
| `ac3_reviews_clean.md` | Reformatted reviews plus a cross-review concern map |
| `01_problem_summary.md` | Distinct problems A-J, deduplicated, mapped to the AC's three pillars |
| `02_triage.md` | Severity x addressability tiers |
| `03_rebuttal_plan.md` | Per-concern battle plan |
| `04_rebuttal_response.md` | First-pass long-form response. **Superseded by `replies/v2/`**, kept for reference |

## Experiments

`experiments/` holds the harness and results.

| File | What |
|---|---|
| `paired_analysis.py` / `paired_analysis_results.txt` | Paired significance across the LiC matrix. Zero API cost, parses existing per-run tables |
| `run_exp1.sh`, `run_exp1_reps.sh` / `exp1_results.txt`, `exp1_reps_results.txt` | Random unbiased subset, end-to-end, N=3 |
| `run_exp2.sh` / `exp2_results.txt` | Equal-budget reflection control |
| `smoke_trapi.py` | TRAPI connectivity check |

Runs use gpt-5.4-mini via TRAPI (`redmond/interactive`). Repo configs added for this: `config/load_balancer/trapi.yaml`, `config/model/gpt5_4_mini_trapi.yaml`. Activate `.venv` first.

## Headline numbers the rebuttal rests on

* **Paired significance:** AC3-Reset improves over full context on 33 of 36 paired comparisons, mean +15.9pp, sign-test p < 0.0001. Beats the assistant-omission design-oracle (+13.3pp) on average.
* **Scale:** LiC now 50 problems per task x 3 prefixes, up to 150 conversations per cell, on 3 models. Submitted version had 18-25 on 1 model.
* **Unbiased subset, end-to-end, N=3:** full context 87.5 +/- 2.0, Reset 100.0 +/- 0.0, Gated-Reset 99.1 +/- 1.2.
* **Database, the contested "exceeds the oracle" claim:** replicates on all 3 models (Reset 49.0 / 56.2 / 55.1 vs AO 45.6 / 27.9 / 30.6).
* **tau2:** AO collapses to 0% on all 3 models; best AC3 operator beats full context on all 3.
