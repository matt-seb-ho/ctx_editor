# docs/ Index

Map of every Markdown file under `docs/`. Use the **Topical** section to find docs by purpose; use the **Chronological log** to reconstruct what was written when (useful when an older note references "the analysis from last Tuesday").

Files are auto-discoverable via `find docs -name "*.md"`, but new docs accumulate fast — please add an entry here when you create one.

---

## Topical

### Start here
- [`README.md`](README.md) — Quickstart, CLI examples, code map.
- [`benchmarks_index.md`](benchmarks_index.md) — One-stop reference for the four benchmarks (LiC, CollabLLM, WildChat/Huang, Tau2).
- [`index.md`](index.md) — This file.

### Core method & architecture
- [`simulation.md`](simulation.md) — `ConversationSimulator`, `ConversationTrace`, shared dataclasses.
- [`context_strategies.md`](context_strategies.md) — Strategy protocol, AC3 lineup, analyzer integration.
- [`memory_learning.md`](memory_learning.md) — `CheatsheetMemory`, `CheatsheetUpdater`, renderers, pipeline integration.
- [`strategy_name_history.md`](strategy_name_history.md) — Old class names ↔ new AC3 names + the S0/S1/S2/S3 decoder.
- [`newleaf_refactor.md`](newleaf_refactor.md) — Option 2 rendering + S0/S1/S2 introduction.
- [`newer_leaf_refactor.md`](newer_leaf_refactor.md) — Two-query analyzer (v6) + `AnalysisResult` redesign.

### Cleanup pass — May 2026 (Phases 0/1/2)
- [`ac3_variants_per_benchmark.md`](ac3_variants_per_benchmark.md) — Which AC3 variants each benchmark actually implements.
- [`experiment_organization_audit.md`](experiment_organization_audit.md) — Code-organization audit + phased refactor plan.
- [`paper_experiments_provenance.md`](paper_experiments_provenance.md) — `(strategy, prompt version, config)` for every paper result.

### Per-benchmark
- [`lost_in_conversation_paper.md`](lost_in_conversation_paper.md) — LiC paper summary.
- [`lic_log_format.md`](lic_log_format.md) — LiC log structure for downstream tooling.
- [`lic_dev_set_provenance.md`](lic_dev_set_provenance.md) — How the LiC dev set was built.
- [`lic_failure_mode_report.md`](lic_failure_mode_report.md) — LiC failure-mode breakdown.
- [`collabllm.md`](collabllm.md) — CollabLLM benchmark overview.
- [`collabllm_eval_loop.md`](collabllm_eval_loop.md) — CollabLLM evaluation loop details.
- [`tau.md`](tau.md) — τ-bench overview.
- [`tau2.md`](tau2.md) — τ²-bench (`telecom_small`) overview.

### Motivation, related work
- [`project_motivation.md`](project_motivation.md) — Research motivation, comparisons to ERGO / Huang et al.
- [`do_llms_benefit_from_their_own_words.md`](do_llms_benefit_from_their_own_words.md) — Background on whether assistant turns help or hurt.
- [`ergo_entropy_guided_resetting.md`](ergo_entropy_guided_resetting.md) — ERGO paper summary.
- [`tree_of_thought_reference.md`](tree_of_thought_reference.md) — Tree of Thoughts paper summary.
- [`related_work_papers/memobrain_2601.08079.md`](related_work_papers/memobrain_2601.08079.md) — MemoBrain summary.
- [`related_work_papers/ufold_2601.18285.md`](related_work_papers/ufold_2601.18285.md) — U-Fold context-folding summary.

### Experimental utilities
- [`replay_mode.md`](replay_mode.md) — Replay-mode evaluation protocol.
- [`concat_baseline.md`](concat_baseline.md) — Concat-User single-turn upper bound.
- [`false_negatives_and_test_subset.md`](false_negatives_and_test_subset.md) — Identifying user-sim false negatives, building test subsets.

### Experiment reports — chronological clusters

Newleaf-era (mid-March 2026), pre-paper:
- [`reports/dev_set_strategy_comparison.md`](reports/dev_set_strategy_comparison.md)
- [`reports/code_task_analysis.md`](reports/code_task_analysis.md)
- [`reports/database_actions_analysis.md`](reports/database_actions_analysis.md)
- [`reports/dev_set_round2_content_filter_fix.md`](reports/dev_set_round2_content_filter_fix.md)
- [`reports/feedback_deliberation_batch1.md`](reports/feedback_deliberation_batch1.md)
- [`reports/replay_results_batch1.md`](reports/replay_results_batch1.md)
- [`reports/pre_sunday_update.md`](reports/pre_sunday_update.md)
- [`reports/user_simulator_comparison.md`](reports/user_simulator_comparison.md)
- [`reports/run_index.md`](reports/run_index.md)
- [`dev_set_error_analysis.md`](dev_set_error_analysis.md)
- [`code_experiment_analysis.md`](code_experiment_analysis.md), [`code_v2b_trace_analysis.md`](code_v2b_trace_analysis.md), [`error_attribution_code_v3.md`](error_attribution_code_v3.md)
- [`feedback_on_newleaf2_batch1.md`](feedback_on_newleaf2_batch1.md)
- [`ctxe_oldleaf_latest.md`](ctxe_oldleaf_latest.md) — Snapshot of context-edit+memory state.

V8/V9 analyzer (late March 2026), main paper push:
- [`reports/v8_trace_analysis.md`](reports/v8_trace_analysis.md)
- [`reports/v8_batch_results.md`](reports/v8_batch_results.md)
- [`reports/v8_2turn_replay_results.md`](reports/v8_2turn_replay_results.md)
- [`reports/v9_experiments.md`](reports/v9_experiments.md)
- [`reports/v10_paper_updates.md`](reports/v10_paper_updates.md)
- [`reports/memory_error_analysis.md`](reports/memory_error_analysis.md)
- [`reports/prior_work_baselines.md`](reports/prior_work_baselines.md)
- [`sans_issue_injection_redux.md`](sans_issue_injection_redux.md)
- [`mar21_bug_discovery.md`](mar21_bug_discovery.md) — `<context_edit_notes>` injection bug.

Ablations:
- [`reports/ablations/single_query_hard_attention.md`](reports/ablations/single_query_hard_attention.md)
- [`reports/ablations/soft_attention_context_editing.md`](reports/ablations/soft_attention_context_editing.md)
- [`reports/ablations/spec_curation_memory.md`](reports/ablations/spec_curation_memory.md)

CollabLLM:
- [`reports/collabllm_initial_experiments.md`](reports/collabllm_initial_experiments.md)
- [`reports/collabllm_baseline_comparison.md`](reports/collabllm_baseline_comparison.md)

Huang / WildChat:
- [`reports/huang_eval_30conv.md`](reports/huang_eval_30conv.md)
- [`reports/huang_eval_consolidated.md`](reports/huang_eval_consolidated.md)
- [`reports/huang_eval_example_trajectory.md`](reports/huang_eval_example_trajectory.md) — Maven debugging trace used in paper appendix.

Hard subset / multi-model:
- [`htn20_52_subset.md`](htn20_52_subset.md)
- [`reports/htn20_52_experiment_results.md`](reports/htn20_52_experiment_results.md)
- [`reports/htn20_52_multi_model_results.md`](reports/htn20_52_multi_model_results.md)
- [`reports/multi_model_generalization.md`](reports/multi_model_generalization.md)

Variance:
- [`multi_run_variance_2026-05-07.md`](multi_run_variance_2026-05-07.md) — N=3 Gated-Reset replay reruns (paper variance row).

### Paper writing & revisions
- [`paper_framing.md`](paper_framing.md) — Paper framing notes.
- [`paper_revision_workflow.md`](paper_revision_workflow.md) — Local revision workflow.
- [`writing_changelog.md`](writing_changelog.md) — Rolling log of paper edits.
- [`neurips_revision_changelog.md`](neurips_revision_changelog.md) — NeurIPS revision pass log.
- [`figure1_candidates.md`](figure1_candidates.md) — Figure 1 design options.
- [`changelog_v2_v3_memory.md`](changelog_v2_v3_memory.md) — V2/V3 prompt + memory fix changelog.

### Advisor & collaborator feedback
- [`lianhui_feedback_analysis.md`](lianhui_feedback_analysis.md) — Analysis of Lianhui's abstract/intro feedback.
- [`lianhui_feedback_changelog.md`](lianhui_feedback_changelog.md) — Round 1 changes responding to feedback.
- [`lianhui_feedback_changelog_r2.md`](lianhui_feedback_changelog_r2.md) — Round 2 changes.
- [`lic_author_meeting_plan.md`](lic_author_meeting_plan.md) — Talking-points for LiC lead-author meeting.

### Self-reviews (2026-05-01)
- [`reviews/2026-05-01_vanilla.md`](reviews/2026-05-01_vanilla.md) — Adversarial peer-review simulation.
- [`reviews/2026-05-01_esl.md`](reviews/2026-05-01_esl.md) — ESL-reviewer prose/flow check.
- [`reviews/2026-05-01_lazy.md`](reviews/2026-05-01_lazy.md) — Skim-only reviewer check.
- [`reviews/2026-05-01_action_plan.md`](reviews/2026-05-01_action_plan.md) — Action items distilled from the three reviews above.

### Plans (active + completed)
- [`plans/new_branch_refactor.md`](plans/new_branch_refactor.md)
- [`plans/experiment_runs_math_code.md`](plans/experiment_runs_math_code.md)
- [`plans/v7_multi_query_analysis.md`](plans/v7_multi_query_analysis.md)
- [`plans/prompt_changes_v8.md`](plans/prompt_changes_v8.md)
- [`plans/resume_state.md`](plans/resume_state.md)
- [`plans/completed/cheatsheet_to_mem_refactor.md`](plans/completed/cheatsheet_to_mem_refactor.md)
- [`plans/completed/memory_features_plan.md`](plans/completed/memory_features_plan.md)

### Scratch
- [`temp.md`](temp.md) — Raw results table from a sweep (LiC S0/S1/S1.5/S2 × {with,without memory} × 4 tasks). Used while drafting paper Table 1.

---

## Chronological log

Date is **first-commit date** (or file mtime for never-committed files). Newest first.

| Date | File | One-liner |
|---|---|---|
| 2026-05-11 | `index.md` | This file. Topical + chronological doc map. |
| 2026-05-11 | `paper_experiments_provenance.md` | Paper Table 1 row → strategy/prompt/config mapping. (Phase 2 add) |
| 2026-05-11 | `experiment_organization_audit.md` | Cross-benchmark audit + phased refactor plan. (Phase 0 add) |
| 2026-05-11 | `ac3_variants_per_benchmark.md` | AC3 coverage matrix per benchmark. (Phase 0 add) |
| 2026-05-11 | `benchmarks_index.md` | One-stop benchmark entry-point reference. (Phase 0 add) |
| 2026-05-11 | `strategy_name_history.md` | Pre-rename → AC3 name decoder. (Phase 0 add) |
| 2026-05-07 | `multi_run_variance_2026-05-07.md` | N=3 Gated-Reset replay reruns; paper variance row. |
| 2026-05-01 | `reviews/2026-05-01_action_plan.md` | Action items from the three self-reviews. |
| 2026-05-01 | `reviews/2026-05-01_esl.md` | ESL reviewer simulation. |
| 2026-05-01 | `reviews/2026-05-01_lazy.md` | Lazy reviewer simulation. |
| 2026-05-01 | `reviews/2026-05-01_vanilla.md` | Adversarial reviewer simulation. |
| 2026-05-01 | `paper_revision_workflow.md` | Local revision workflow. |
| 2026-04-29 | `lic_author_meeting_plan.md` | Talking points for LiC lead-author meeting. |
| 2026-04-20 | `neurips_revision_changelog.md` | NeurIPS revision pass log. |
| 2026-04-13 | `lianhui_feedback_changelog_r2.md` | Round 2 of Lianhui-feedback changes. |
| 2026-04-07 | `lianhui_feedback_analysis.md` | Analysis of Lianhui's abstract/intro feedback. |
| 2026-04-07 | `lianhui_feedback_changelog.md` | Round 1 of Lianhui-feedback changes. |
| 2026-03-31 | `related_work_papers/memobrain_2601.08079.md` | MemoBrain paper summary. |
| 2026-03-31 | `related_work_papers/ufold_2601.18285.md` | U-Fold paper summary. |
| 2026-03-31 | `writing_changelog.md` | Rolling log of paper edits. |
| 2026-03-31 | `reports/huang_eval_example_trajectory.md` | Maven debugging trace for paper appendix. |
| 2026-03-29 | `collabllm.md` | CollabLLM benchmark overview. |
| 2026-03-29 | `figure1_candidates.md` | Figure 1 design options. |
| 2026-03-29 | `htn20_52_subset.md` | Hard test subset description. |
| 2026-03-29 | `lic_log_format.md` | LiC log file structure. |
| 2026-03-29 | `reports/htn20_52_experiment_results.md` | Hard-subset run results. |
| 2026-03-29 | `reports/htn20_52_multi_model_results.md` | Hard-subset multi-model results. |
| 2026-03-29 | `reports/multi_model_generalization.md` | Multi-model generalization writeup. |
| 2026-03-29 | `reports/v8_2turn_replay_results.md` | V8 replay-last-2-turns results. |
| 2026-03-26 | `tree_of_thought_reference.md` | Tree of Thoughts paper summary. |
| 2026-03-26 | `lic_dev_set_provenance.md` | Dev-set construction provenance. |
| 2026-03-26 | `reports/v10_paper_updates.md` | V10 paper-update summary. |
| 2026-03-26 | `reports/v9_experiments.md` | V9 LiC + actions-accumulate fairness check. |
| 2026-03-25 | `mar21_bug_discovery.md` | `<context_edit_notes>` injection bug write-up. |
| 2026-03-25 | `reports/huang_eval_30conv.md` | 30-conv Huang reproduction pilot. |
| 2026-03-25 | `reports/huang_eval_consolidated.md` | Consolidated Huang eval results. |
| 2026-03-25 | `reports/prior_work_baselines.md` | Omit-Assistant / Concat-User baselines writeup. |
| 2026-03-23 | `reports/collabllm_baseline_comparison.md` | CollabLLM baselines vs context compaction. |
| 2026-03-21 | `sans_issue_injection_redux.md` | "Sans issue injection" follow-up. |
| 2026-03-20 | `reports/ablations/spec_curation_memory.md` | Spec-curation memory ablation. |
| 2026-03-19 | `collabllm_eval_loop.md` | CollabLLM eval loop details. |
| 2026-03-18 | `reports/collabllm_initial_experiments.md` | First CollabLLM experiments. |
| 2026-03-17 | `feedback_on_newleaf2_batch1.md` | My feedback on the dev-set error analysis. |
| 2026-03-17 | `paper_framing.md` | Paper framing notes. |
| 2026-03-17 | `reports/ablations/single_query_hard_attention.md` | Single-query vs two-query hard-attention ablation. |
| 2026-03-17 | `reports/ablations/soft_attention_context_editing.md` | Soft-attention rescue experiment. |
| 2026-03-17 | `reports/memory_error_analysis.md` | Memory error analysis across S1/S1.5 variants. |
| 2026-03-17 | `reports/v8_batch_results.md` | V8 batch results. |
| 2026-03-17 | `tau.md` | τ-bench overview. |
| 2026-03-17 | `tau2.md` | τ²-bench overview. |
| 2026-03-17 | `temp.md` | Scratch results table. |
| 2026-03-16 | `plans/prompt_changes_v8.md` | V8 prompt changes plan. |
| 2026-03-16 | `reports/v8_trace_analysis.md` | V8 trace analysis. |
| 2026-03-15 | `plans/v7_multi_query_analysis.md` | V7 multi-query plan. |
| 2026-03-15 | `reports/database_actions_analysis.md` | Database & actions task diagnosis. |
| 2026-03-15 | `reports/pre_sunday_update.md` | Pre-Sunday status update. |
| 2026-03-15 | `reports/run_index.md` | Dev-set run index. |
| 2026-03-14 | `concat_baseline.md` | Concat-User single-turn upper bound. |
| 2026-03-14 | `dev_set_error_analysis.md` | Dev-set error analysis. |
| 2026-03-14 | `replay_mode.md` | Replay-mode protocol. |
| 2026-03-14 | `reports/code_task_analysis.md` | Code task spot-check analysis. |
| 2026-03-14 | `reports/dev_set_round2_content_filter_fix.md` | Round 2 dev-set after content-filter fix. |
| 2026-03-14 | `reports/feedback_deliberation_batch1.md` | Batch 1 feedback deliberation. |
| 2026-03-14 | `reports/replay_results_batch1.md` | Batch 1 replay results. |
| 2026-03-13 | `ctxe_oldleaf_latest.md` | Snapshot of context-edit + memory state. |
| 2026-03-13 | `do_llms_benefit_from_their_own_words.md` | Background note. |
| 2026-03-13 | `ergo_entropy_guided_resetting.md` | ERGO paper summary. |
| 2026-03-13 | `lic_failure_mode_report.md` | LiC failure-mode report. |
| 2026-03-13 | `lost_in_conversation_paper.md` | LiC paper summary. |
| 2026-03-13 | `newer_leaf_refactor.md` | Two-query analyzer (v6) redesign. |
| 2026-03-13 | `project_motivation.md` | Research motivation. |
| 2026-03-12 | `reports/dev_set_strategy_comparison.md` | First dev-set strategy comparison. |
| 2026-03-11 | `changelog_v2_v3_memory.md` | V2/V3 + memory changelog. |
| 2026-03-11 | `code_experiment_analysis.md` | Why context editing hurts code. |
| 2026-03-11 | `code_v2b_trace_analysis.md` | Context-edit V2b trace analysis. |
| 2026-03-11 | `error_attribution_code_v3.md` | Error attribution for V3 code experiments. |
| 2026-03-11 | `false_negatives_and_test_subset.md` | User-sim false-negative tooling. |
| 2026-03-11 | `newleaf_refactor.md` | Option 2 rendering + S0/S1/S2 introduction. |
| 2026-03-11 | `plans/experiment_runs_math_code.md` | Math+code experiment plan. |
| 2026-03-11 | `plans/new_branch_refactor.md` | New-branch refactor plan. |
| 2026-03-11 | `plans/resume_state.md` | Resume state for paused work. |
| 2026-03-11 | `reports/user_simulator_comparison.md` | User-simulator comparison. |
| 2026-03-09 | `README.md` | Quickstart + code map. |
| 2026-03-09 | `context_strategies.md` | Strategy protocol + AC3 lineup. |
| 2026-03-09 | `memory_learning.md` | Memory / Dynamic Cheatsheet. |
| 2026-03-09 | `plans/completed/cheatsheet_to_mem_refactor.md` | Cheatsheet → memory module refactor. |
| 2026-03-09 | `plans/completed/memory_features_plan.md` | Memory features plan. |
| 2026-03-09 | `simulation.md` | Simulator + trace + core types. |

---

When adding new docs, append an entry under both the topical section and the chronological log. Keep one-liners ≤ 12 words.
