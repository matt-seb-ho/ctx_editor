```

● Here's a structured list of every report / log / markdown file created in this mega-table line.

  Plans (docs/)

  ┌────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
  │                    File                    │                             Purpose                              │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_r3_followups.md            │ R3 follow-up backlog (where the mega-table got first envisioned) │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_r5_analyzer_parity_plan.md │ Refactor plan after the analyzer-parity bug                      │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_r6_plan.md                 │ R6 plan: A1-A4 + B-stage decision rules                          │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_r6_design_iterations.md    │ v8/v9/v10 prompt design log + warts                              │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_tau2_plan.md               │ Original tau2 scoping doc                                        │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_tau2_overnight_plan.md     │ Tau2 overnight execution plan + sign-offs                        │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/post_may18_tau2_followups.md          │ Tau2 Phase 0-1 findings (venv + analyzer parity audit)           │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/tau2_absorption_decision.md           │ Federated-vs-absorb decision for the tau2 fork                   │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/analyzer_parity_finding.md            │ The smoking-gun architectural bug writeup                        │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/global_todos.md                       │ Cross-batch TODOs (sys-prompt preprocessing, etc.)               │
  ├────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ docs/next_todos_post_may18.md              │ Working TODO list                                                │
  └────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

  Reports (docs/reports/)

  ┌───────────────────────────────────────┬────────────┬──────────────────────────────────────────────────────────────────────────┐
  │                 File                  │   Round    │                                 Purpose                                  │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r3_summary.md              │ R3         │ Hierarchical-analysis methodology + 63% hallucination finding            │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r3_mega_table.md           │ R3         │ Initial mega-table snapshot (LiC/CollabLLM/WildChat × 3 models)          │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r3_rewrite_examples.md     │ R3         │ Per-sample case studies from the 48-pair diagnostic                      │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r4_summary.md              │ R4         │ v5 Reset-like + v6 GEPA results (pre-parity)                             │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r4_resume.md               │ R4         │ Post-mortem (GEPA bias + parity bug discovery)                           │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r5_resume.md               │ R5         │ Parity refactor wrap-up                                                  │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r6_overnight_progress.md   │ R6         │ Running narrative of the R6 overnight execution                          │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_r6_summary.md              │ R6         │ R6 winner declaration (v8) + handoff contract to tau2                    │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may18_tau2_summary.md            │ tau2 v1    │ Initial tau2 sweep using OpenRouter substitutes                          │
  ├───────────────────────────────────────┼────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ post_may26_megatable_round_summary.md │ this round │ Foundry-canonical tau2 + WildChat × gpt-5.4 + Gated-Reset reconstruction │
  └───────────────────────────────────────┴────────────┴──────────────────────────────────────────────────────────────────────────┘

  Mega-table & talk artifacts (docs/reports/)

  ┌─────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────┐
  │                    File                     │                                       Purpose                                        │
  ├─────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ post_may18_progress_update.html             │ First combined HTML (v2; has tau2 OpenRouter substitutes)                            │
  ├─────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ post_may18_progress_update_pre_tau2_v2.html │ Snapshot before tau2 row added                                                       │
  ├─────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ post_may18_progress_update_v3_clean.html    │ Current mega-table for the mentor talk (Foundry-canonical, Gated-Reset row restored) │
  └─────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────┘

  Aggregator + diagnostic data (scripts/analysis_rewrite_v_reset/data/)

  ┌────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
  │                  File                  │                             Purpose                              │
  ├────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ rewrite_versions_compared.md           │ Cross-variant LiC table (Baseline / Reset / AO / Rewrite v1-v10) │
  ├────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ diagnosis_summary.md                   │ R3 48-pair attribution (63% hallucination)                       │
  ├────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ pairs.jsonl, diagnoses.jsonl           │ R3 raw data                                                      │
  ├────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ pairs_v8.jsonl, diagnoses_v8.jsonl     │ Post-parity (v8) 43-pair re-diagnostic                           │
  ├────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ gated_reset_reconstructed_lic.md       │ LiC reconstruction (97.3% gate-open → ≈ Reset)                   │
  ├────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ gated_reset_reconstructed_collabllm.md │ CollabLLM reconstruction (98.3% gate-open)                       │
  └────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

  Driver / sweep logs

  ctx_editor side (outputs/):

  ┌───────────────────────────────────────┬──────────────────────────┐
  │                 File                  │          Sweep           │
  ├───────────────────────────────────────┼──────────────────────────┤
  │ post_may18_r6_a_stage_driver.log      │ A1+A2+A3 parallel sweep  │
  ├───────────────────────────────────────┼──────────────────────────┤
  │ post_may18_r6_b1_v10_dsv4f_driver.log │ A4 GEPA validation       │
  ├───────────────────────────────────────┼──────────────────────────┤
  │ post_may18_r6_b2_v8_gpt54_driver.log  │ B2 cross-model (gpt-5.4) │
  ├───────────────────────────────────────┼──────────────────────────┤
  │ post_may18_r6_b2_v8_kimi_driver.log   │ B2 cross-model (Kimi)    │
  ├───────────────────────────────────────┼──────────────────────────┤
  │ post_may26_wildchat_gpt54_driver.log  │ WildChat × gpt-5.4 sweep │
  └───────────────────────────────────────┴──────────────────────────┘

  Plus per-cell logs under outputs/post_may18_r6_b3_wildchat/logs/ (2 files), outputs/post_may18_r6_b3_collabllm/logs/ (6),
  outputs/post_may26_wildchat_gpt54/logs/ (4).

  tau2 side (/home/v-homatthew/tau2_ctxe/ctx_edit/outputs/):

  ┌───────────────────────────────────────────────┬─────────────────────────────────────────────────────┐
  │                     File                      │                        Sweep                        │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ post_may18_tau2_sweep_driver.log              │ First tau2 sweep (gpt-5.4 + OpenRouter substitutes) │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ post_may18_tau2_retry_driver.log              │ DSV4F+Kimi OpenRouter retry with corrected IDs      │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ post_may18_tau2_foundry_driver.log            │ Canonical Azure Foundry sweep (DSV4F + Kimi-K2.6)   │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
  │ post_may18_tau2_foundry_kimi_retry_driver.log │ Kimi workers=4 rate-limit-safe retry                │
  └───────────────────────────────────────────────┴─────────────────────────────────────────────────────┘

  Plus per-cell _logs/ subdirs: 15 logs for post_may18_tau2_sweep, 10 each for post_may18_tau2_retry + post_may18_tau2_foundry, 5 for
  post_may18_tau2_foundry_kimi_retry.

  The two files to share with anyone reading cold are docs/reports/post_may26_megatable_round_summary.md (text) and
  docs/reports/post_may18_progress_update_v3_clean.html (talk-ready mega-table).

```
