## AC3 Phase 1 — DeepSeek-V4-Flash, last-turn replay (n=3 prefixes)

Mean accuracy across prefix replicates (typically n=3). For each cell the table shows mean ± std (pp).

| Strategy | math_v2 | code_v2 | database_v2 | actions_v2 | Δ vs Baseline (avg pp) |
|---|---|---|---|---|---|
| Baseline | 72.2% ± 14.2pp (n=3) | 34.7% ± 6.2pp (n=3) | 22.4% ± 10.8pp (n=3) | 76.0% ± 13.1pp (n=3) | +0.0pp |
| AO | 86.1% ± 5.2pp (n=3) | 60.3% ± 11.1pp (n=3) | 45.6% ± 7.2pp (n=3) | 86.0% ± 8.7pp (n=3) | +18.1pp |
| Augment | 84.0% ± 9.8pp (n=3) | 58.7% ± 11.4pp (n=3) | 41.5% ± 12.0pp (n=3) | 84.0% ± 4.0pp (n=3) | +15.7pp |
| Reset | 81.9% ± 7.9pp (n=3) | 59.5% ± 10.2pp (n=3) | 49.0% ± 5.4pp (n=3) | 83.3% ± 3.1pp (n=3) | +17.1pp |
| Gated-Reset | 82.6% ± 10.7pp (n=3) | 55.9% ± 7.9pp (n=3) | 49.7% ± 5.1pp (n=3) | 85.3% ± 4.2pp (n=3) | +17.0pp |
| Rewrite | 73.6% ± 13.4pp (n=3) | 28.6% ± 9.5pp (n=3) | 27.9% ± 11.2pp (n=3) | 74.0% ± 13.1pp (n=3) | -0.3pp |

### Per-cell detail

| Strategy | Task | Conv | Accuracy | Errors | Cost | Avg Turns | Output Dir |
|---|---|---|---|---|---|---|---|
| AO | actions_v2 | 0 | 96.0% (48/50) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/omit_assistant_actions_v2_conv0_1779010018` |
| AO | actions_v2 | 1 | 82.0% (41/50) | 0 | $0.01 | 5.1 | `outputs/post_neurips_ac3_phase1/omit_assistant_actions_v2_conv1_1779010625` |
| AO | actions_v2 | 2 | 80.0% (40/50) | 0 | $0.01 | 5.0 | `outputs/post_neurips_ac3_phase1/omit_assistant_actions_v2_conv2_1779011068` |
| AO | code_v2 | 0 | 55.0% (22/40) | 0 | $0.01 | 5.6 | `outputs/post_neurips_ac3_phase1/omit_assistant_code_v2_conv0_1779001884` |
| AO | code_v2 | 1 | 73.0% (27/37) | 0 | $0.01 | 5.4 | `outputs/post_neurips_ac3_phase1/omit_assistant_code_v2_conv1_1779003449` |
| AO | code_v2 | 2 | 52.8% (19/36) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/omit_assistant_code_v2_conv2_1779004471` |
| AO | database_v2 | 0 | 53.1% (26/49) | 0 | $0.01 | 4.4 | `outputs/post_neurips_ac3_phase1/omit_assistant_database_v2_conv0_1779006171` |
| AO | database_v2 | 1 | 38.8% (19/49) | 0 | $0.01 | 4.3 | `outputs/post_neurips_ac3_phase1/omit_assistant_database_v2_conv1_1779007730` |
| AO | database_v2 | 2 | 44.9% (22/49) | 0 | $0.01 | 4.0 | `outputs/post_neurips_ac3_phase1/omit_assistant_database_v2_conv2_1779009069` |
| AO | math_v2 | 0 | 81.2% (39/48) | 0 | $0.01 | 5.6 | `outputs/post_neurips_ac3_phase1/omit_assistant_math_v2_conv0_1779000126` |
| AO | math_v2 | 1 | 91.7% (44/48) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/omit_assistant_math_v2_conv1_1779000791` |
| AO | math_v2 | 2 | 85.4% (41/48) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/omit_assistant_math_v2_conv2_1779001183` |
| Augment | actions_v2 | 0 | 80.0% (40/50) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/append_analysis_actions_v2_conv0_1779010051` |
| Augment | actions_v2 | 1 | 84.0% (42/50) | 0 | $0.01 | 5.1 | `outputs/post_neurips_ac3_phase1/append_analysis_actions_v2_conv1_1779010683` |
| Augment | actions_v2 | 2 | 88.0% (44/50) | 0 | $0.01 | 5.0 | `outputs/post_neurips_ac3_phase1/append_analysis_actions_v2_conv2_1779011142` |
| Augment | code_v2 | 0 | 47.5% (19/40) | 0 | $0.02 | 5.6 | `outputs/post_neurips_ac3_phase1/append_analysis_code_v2_conv0_1779002091` |
| Augment | code_v2 | 1 | 70.3% (26/37) | 0 | $0.02 | 5.4 | `outputs/post_neurips_ac3_phase1/append_analysis_code_v2_conv1_1779003582` |
| Augment | code_v2 | 2 | 58.3% (21/36) | 0 | $0.02 | 5.2 | `outputs/post_neurips_ac3_phase1/append_analysis_code_v2_conv2_1779004701` |
| Augment | database_v2 | 0 | 36.7% (18/49) | 0 | $0.02 | 4.4 | `outputs/post_neurips_ac3_phase1/append_analysis_database_v2_conv0_1779006599` |
| Augment | database_v2 | 1 | 32.7% (16/49) | 0 | $0.02 | 4.3 | `outputs/post_neurips_ac3_phase1/append_analysis_database_v2_conv1_1779007881` |
| Augment | database_v2 | 2 | 55.1% (27/49) | 0 | $0.02 | 4.0 | `outputs/post_neurips_ac3_phase1/append_analysis_database_v2_conv2_1779009221` |
| Augment | math_v2 | 0 | 72.9% (35/48) | 0 | $0.01 | 5.6 | `outputs/post_neurips_ac3_phase1/append_analysis_math_v2_conv0_1779000201` |
| Augment | math_v2 | 1 | 91.7% (44/48) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/append_analysis_math_v2_conv1_1779000856` |
| Augment | math_v2 | 2 | 87.5% (42/48) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/append_analysis_math_v2_conv2_1779001246` |
| Baseline | actions_v2 | 0 | 64.0% (32/50) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/baseline_actions_v2_conv0_1779009873` |
| Baseline | actions_v2 | 1 | 74.0% (37/50) | 0 | $0.01 | 5.1 | `outputs/post_neurips_ac3_phase1/baseline_actions_v2_conv1_1779010519` |
| Baseline | actions_v2 | 2 | 90.0% (45/50) | 0 | $0.01 | 5.0 | `outputs/post_neurips_ac3_phase1/baseline_actions_v2_conv2_1779011007` |
| Baseline | code_v2 | 0 | 30.0% (12/40) | 0 | $0.01 | 5.6 | `outputs/post_neurips_ac3_phase1/baseline_code_v2_conv0_1779001554` |
| Baseline | code_v2 | 1 | 32.4% (12/37) | 0 | $0.01 | 5.4 | `outputs/post_neurips_ac3_phase1/baseline_code_v2_conv1_1779003186` |
| Baseline | code_v2 | 2 | 41.7% (15/36) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/baseline_code_v2_conv2_1779004279` |
| Baseline | database_v2 | 0 | 14.3% (7/49) | 0 | $0.01 | 4.4 | `outputs/post_neurips_ac3_phase1/baseline_database_v2_conv0_1779005931` |
| Baseline | database_v2 | 1 | 18.4% (9/49) | 0 | $0.01 | 4.3 | `outputs/post_neurips_ac3_phase1/baseline_database_v2_conv1_1779007505` |
| Baseline | database_v2 | 2 | 34.7% (17/49) | 0 | $0.01 | 4.0 | `outputs/post_neurips_ac3_phase1/baseline_database_v2_conv2_1779008908` |
| Baseline | math_v2 | 0 | 56.2% (27/48) | 0 | $0.01 | 5.6 | `outputs/post_neurips_ac3_phase1/baseline_math_v2_conv0_1778999994` |
| Baseline | math_v2 | 1 | 77.1% (37/48) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/baseline_math_v2_conv1_1779000710` |
| Baseline | math_v2 | 2 | 83.3% (40/48) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/baseline_math_v2_conv2_1779001107` |
| Gated-Reset | actions_v2 | 0 | 82.0% (41/50) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_accumulate_actions_v2_conv0_1779010239` |
| Gated-Reset | actions_v2 | 1 | 90.0% (45/50) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_accumulate_actions_v2_conv1_1779010832` |
| Gated-Reset | actions_v2 | 2 | 84.0% (42/50) | 0 | $0.01 | 6.0 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_accumulate_actions_v2_conv2_1779011274` |
| Gated-Reset | code_v2 | 0 | 50.0% (20/40) | 0 | $0.01 | 6.5 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_code_v2_conv0_1779002639` |
| Gated-Reset | code_v2 | 1 | 64.9% (24/37) | 0 | $0.01 | 6.2 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_code_v2_conv1_1779003851` |
| Gated-Reset | code_v2 | 2 | 52.8% (19/36) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_code_v2_conv2_1779005537` |
| Gated-Reset | database_v2 | 0 | 44.9% (22/49) | 0 | $0.01 | 5.4 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_database_v2_conv0_1779006988` |
| Gated-Reset | database_v2 | 1 | 49.0% (24/49) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_database_v2_conv1_1779008436` |
| Gated-Reset | database_v2 | 2 | 55.1% (27/49) | 0 | $0.01 | 4.9 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_database_v2_conv2_1779009513` |
| Gated-Reset | math_v2 | 0 | 70.8% (34/48) | 0 | $0.01 | 6.6 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_math_v2_conv0_1779000428` |
| Gated-Reset | math_v2 | 1 | 91.7% (44/48) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_math_v2_conv1_1779000977` |
| Gated-Reset | math_v2 | 2 | 85.4% (41/48) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/context_edit_v2_gated_math_v2_conv2_1779001382` |
| Reset | actions_v2 | 0 | 80.0% (40/50) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_accumulate_actions_v2_conv0_1779010142` |
| Reset | actions_v2 | 1 | 84.0% (42/50) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_accumulate_actions_v2_conv1_1779010755` |
| Reset | actions_v2 | 2 | 86.0% (43/50) | 0 | $0.01 | 6.0 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_accumulate_actions_v2_conv2_1779011212` |
| Reset | code_v2 | 0 | 50.0% (20/40) | 0 | $0.01 | 6.5 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_code_v2_conv0_1779002333` |
| Reset | code_v2 | 1 | 70.3% (26/37) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_code_v2_conv1_1779003730` |
| Reset | code_v2 | 2 | 58.3% (21/36) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_code_v2_conv2_1779004910` |
| Reset | database_v2 | 0 | 51.0% (25/49) | 0 | $0.01 | 5.4 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_database_v2_conv0_1779006776` |
| Reset | database_v2 | 1 | 42.9% (21/49) | 0 | $0.01 | 5.2 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_database_v2_conv1_1779008238` |
| Reset | database_v2 | 2 | 53.1% (26/49) | 0 | $0.01 | 5.0 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_database_v2_conv2_1779009358` |
| Reset | math_v2 | 0 | 72.9% (35/48) | 0 | $0.01 | 6.6 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_math_v2_conv0_1779000319` |
| Reset | math_v2 | 1 | 87.5% (42/48) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_math_v2_conv1_1779000919` |
| Reset | math_v2 | 2 | 85.4% (41/48) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate_math_v2_conv2_1779001321` |
| Rewrite | actions_v2 | 0 | 60.0% (30/50) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_actions_v2_conv0_1779010325` |
| Rewrite | actions_v2 | 1 | 76.0% (38/50) | 0 | $0.01 | 6.1 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_actions_v2_conv1_1779010885` |
| Rewrite | actions_v2 | 2 | 86.0% (43/50) | 0 | $0.01 | 6.0 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_actions_v2_conv2_1779011346` |
| Rewrite | code_v2 | 0 | 20.0% (8/40) | 0 | $0.01 | 6.5 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_code_v2_conv0_1779002836` |
| Rewrite | code_v2 | 1 | 27.0% (10/37) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_code_v2_conv1_1779004033` |
| Rewrite | code_v2 | 2 | 38.9% (14/36) | 0 | $0.01 | 6.2 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_code_v2_conv2_1779005726` |
| Rewrite | database_v2 | 0 | 16.3% (8/49) | 0 | $0.01 | 5.4 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_database_v2_conv0_1779007192` |
| Rewrite | database_v2 | 1 | 28.6% (14/49) | 0 | $0.01 | 5.3 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_database_v2_conv1_1779008632` |
| Rewrite | database_v2 | 2 | 38.8% (19/49) | 0 | $0.01 | 5.0 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_database_v2_conv2_1779009661` |
| Rewrite | math_v2 | 0 | 58.3% (28/48) | 0 | $0.01 | 6.6 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_math_v2_conv0_1779000522` |
| Rewrite | math_v2 | 1 | 83.3% (40/48) | 0 | $0.01 | 6.3 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_math_v2_conv1_1779001013` |
| Rewrite | math_v2 | 2 | 79.2% (38/48) | 0 | $0.01 | 6.2 | `outputs/post_neurips_ac3_phase1/ac3_rewrite_lic_math_v2_conv2_1779001443` |
