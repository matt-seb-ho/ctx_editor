## AC3 Phase 2 — scale-up to gpt-5.4 / Kimi-K2.6 / gpt-5.5

Mean accuracy across prefix replicates (typically n=3). For each cell the table shows mean ± std (pp).

| Strategy | math_v2 | code_v2 | database_v2 | actions_v2 | Δ vs Baseline (avg pp) |
|---|---|---|---|---|---|
| Baseline | 77.0% ± 9.4pp (n=6) | 58.0% ± 9.9pp (n=6) | 19.0% ± 7.1pp (n=6) | 88.0% ± 4.0pp (n=6) | +0.0pp |
| AO | 88.1% ± 4.1pp (n=6) | 75.4% ± 12.6pp (n=6) | 29.3% ± 4.9pp (n=6) | 92.7% ± 2.4pp (n=6) | +10.8pp |
| Augment | 86.3% ± 3.8pp (n=6) | 70.4% ± 7.7pp (n=6) | 53.7% ± 3.8pp (n=6) | 91.3% ± 2.4pp (n=6) | +14.9pp |
| Reset | 85.6% ± 4.4pp (n=6) | 70.1% ± 10.0pp (n=6) | 55.7% ± 5.8pp (n=6) | 92.0% ± 1.8pp (n=6) | +15.3pp |

### Per-cell detail

| Strategy | Task | Conv | Accuracy | Errors | Cost | Avg Turns | Output Dir |
|---|---|---|---|---|---|---|---|
| AO | actions_v2 | 0 | 94.0% (47/50) | 0 | $0.18 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_actions_v2_conv0_1779017639` |
| AO | actions_v2 | 0 | 96.0% (48/50) | 0 | $0.19 | 5.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_actions_v2_conv0_1779025839` |
| AO | actions_v2 | 1 | 94.0% (47/50) | 0 | $0.20 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_actions_v2_conv1_1779017852` |
| AO | actions_v2 | 1 | 90.0% (45/50) | 0 | $0.18 | 5.1 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_actions_v2_conv1_1779026730` |
| AO | actions_v2 | 2 | 90.0% (45/50) | 0 | $0.19 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_actions_v2_conv2_1779018083` |
| AO | actions_v2 | 2 | 92.0% (46/50) | 0 | $0.16 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_actions_v2_conv2_1779027609` |
| AO | code_v2 | 0 | 78.6% (33/42) | 0 | $0.47 | 4.0 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_code_v2_conv0_1779013057` |
| AO | code_v2 | 0 | 62.8% (27/43) | 0 | $0.73 | 3.9 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_code_v2_conv0_1779015588` |
| AO | code_v2 | 1 | 92.5% (37/40) | 0 | $0.42 | 4.0 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_code_v2_conv1_1779013925` |
| AO | code_v2 | 1 | 61.9% (26/42) | 0 | $0.79 | 3.5 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_code_v2_conv1_1779017592` |
| AO | code_v2 | 2 | 86.5% (32/37) | 0 | $0.34 | 3.8 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_code_v2_conv2_1779014517` |
| AO | code_v2 | 2 | 70.0% (28/40) | 0 | $0.74 | 3.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_code_v2_conv2_1779019616` |
| AO | database_v2 | 0 | 24.5% (12/49) | 0 | $0.29 | 4.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_database_v2_conv0_1779015128` |
| AO | database_v2 | 0 | 30.6% (15/49) | 0 | $0.29 | 4.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_database_v2_conv0_1779021447` |
| AO | database_v2 | 1 | 26.5% (13/49) | 0 | $0.26 | 4.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_database_v2_conv1_1779016038` |
| AO | database_v2 | 1 | 24.5% (12/49) | 0 | $0.28 | 4.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_database_v2_conv1_1779022883` |
| AO | database_v2 | 2 | 32.7% (16/49) | 0 | $0.27 | 4.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_database_v2_conv2_1779016882` |
| AO | database_v2 | 2 | 36.7% (18/49) | 0 | $0.26 | 4.2 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_database_v2_conv2_1779024389` |
| AO | math_v2 | 0 | 89.6% (43/48) | 0 | $0.25 | 5.4 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_math_v2_conv0_1779011656` |
| AO | math_v2 | 0 | 83.3% (40/48) | 0 | $0.44 | 5.5 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_math_v2_conv0_1779011763` |
| AO | math_v2 | 1 | 91.7% (44/48) | 0 | $0.26 | 5.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_math_v2_conv1_1779012155` |
| AO | math_v2 | 1 | 85.4% (41/48) | 0 | $0.33 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_math_v2_conv1_1779012745` |
| AO | math_v2 | 2 | 93.6% (44/47) | 0 | $0.24 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/omit_assistant_math_v2_conv2_1779012506` |
| AO | math_v2 | 2 | 85.1% (40/47) | 0 | $0.39 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/omit_assistant_math_v2_conv2_1779013961` |
| Augment | actions_v2 | 0 | 92.0% (46/50) | 0 | $0.23 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_actions_v2_conv0_1779017674` |
| Augment | actions_v2 | 0 | 94.0% (47/50) | 0 | $0.12 | 5.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_actions_v2_conv0_1779026017` |
| Augment | actions_v2 | 1 | 90.0% (45/50) | 0 | $0.22 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_actions_v2_conv1_1779017896` |
| Augment | actions_v2 | 1 | 90.0% (45/50) | 0 | $0.14 | 5.1 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_actions_v2_conv1_1779026895` |
| Augment | actions_v2 | 2 | 88.0% (44/50) | 0 | $0.23 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_actions_v2_conv2_1779018149` |
| Augment | actions_v2 | 2 | 94.0% (47/50) | 0 | $0.15 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_actions_v2_conv2_1779027760` |
| Augment | code_v2 | 0 | 69.0% (29/42) | 0 | $0.43 | 4.0 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_code_v2_conv0_1779013213` |
| Augment | code_v2 | 0 | 60.5% (26/43) | 0 | $0.77 | 3.9 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_code_v2_conv0_1779016122` |
| Augment | code_v2 | 1 | 72.5% (29/40) | 0 | $0.47 | 4.0 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_code_v2_conv1_1779013998` |
| Augment | code_v2 | 1 | 69.0% (29/42) | 0 | $0.64 | 3.5 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_code_v2_conv1_1779018120` |
| Augment | code_v2 | 2 | 83.8% (31/37) | 0 | $0.39 | 3.8 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_code_v2_conv2_1779014622` |
| Augment | code_v2 | 2 | 67.5% (27/40) | 0 | $0.55 | 3.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_code_v2_conv2_1779020082` |
| Augment | database_v2 | 0 | 53.1% (26/49) | 0 | $0.32 | 4.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_database_v2_conv0_1779015380` |
| Augment | database_v2 | 0 | 51.0% (25/49) | 0 | $0.23 | 4.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_database_v2_conv0_1779021772` |
| Augment | database_v2 | 1 | 59.2% (29/49) | 0 | $0.29 | 4.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_database_v2_conv1_1779016286` |
| Augment | database_v2 | 1 | 53.1% (26/49) | 0 | $0.23 | 4.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_database_v2_conv1_1779023242` |
| Augment | database_v2 | 2 | 57.1% (28/49) | 0 | $0.31 | 4.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_database_v2_conv2_1779017136` |
| Augment | database_v2 | 2 | 49.0% (24/49) | 0 | $0.21 | 4.2 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_database_v2_conv2_1779024700` |
| Augment | math_v2 | 0 | 83.3% (40/48) | 0 | $0.33 | 5.4 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_math_v2_conv0_1779011732` |
| Augment | math_v2 | 0 | 87.2% (34/39) | 9 | $0.19 | 5.0 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_math_v2_conv0_1779011955` |
| Augment | math_v2 | 1 | 85.4% (41/48) | 0 | $0.33 | 5.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_math_v2_conv1_1779012204` |
| Augment | math_v2 | 1 | 81.2% (39/48) | 0 | $0.28 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_math_v2_conv1_1779013009` |
| Augment | math_v2 | 2 | 91.5% (43/47) | 0 | $0.33 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/append_analysis_math_v2_conv2_1779012562` |
| Augment | math_v2 | 2 | 89.4% (42/47) | 0 | $0.21 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/append_analysis_math_v2_conv2_1779014170` |
| Baseline | actions_v2 | 0 | 86.0% (43/50) | 0 | $0.19 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_actions_v2_conv0_1779017575` |
| Baseline | actions_v2 | 0 | 82.0% (41/50) | 0 | $0.19 | 5.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_actions_v2_conv0_1779025649` |
| Baseline | actions_v2 | 1 | 88.0% (44/50) | 0 | $0.20 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_actions_v2_conv1_1779017791` |
| Baseline | actions_v2 | 1 | 90.0% (45/50) | 0 | $0.14 | 5.1 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_actions_v2_conv1_1779026613` |
| Baseline | actions_v2 | 2 | 88.0% (44/50) | 0 | $0.20 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_actions_v2_conv2_1779018026` |
| Baseline | actions_v2 | 2 | 94.0% (47/50) | 0 | $0.14 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_actions_v2_conv2_1779027510` |
| Baseline | code_v2 | 0 | 52.4% (22/42) | 0 | $0.52 | 4.0 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_code_v2_conv0_1779012749` |
| Baseline | code_v2 | 0 | 44.2% (19/43) | 0 | $0.74 | 3.9 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_code_v2_conv0_1779014996` |
| Baseline | code_v2 | 1 | 52.5% (21/40) | 0 | $0.44 | 4.0 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_code_v2_conv1_1779013639` |
| Baseline | code_v2 | 1 | 69.0% (29/42) | 0 | $0.66 | 3.5 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_code_v2_conv1_1779017190` |
| Baseline | code_v2 | 2 | 67.6% (25/37) | 0 | $0.40 | 3.8 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_code_v2_conv2_1779014329` |
| Baseline | code_v2 | 2 | 62.5% (25/40) | 0 | $0.60 | 3.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_code_v2_conv2_1779019169` |
| Baseline | database_v2 | 0 | 10.2% (5/49) | 0 | $0.27 | 4.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_database_v2_conv0_1779014862` |
| Baseline | database_v2 | 0 | 16.3% (8/49) | 0 | $0.26 | 4.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_database_v2_conv0_1779021052` |
| Baseline | database_v2 | 1 | 18.4% (9/49) | 0 | $0.26 | 4.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_database_v2_conv1_1779015771` |
| Baseline | database_v2 | 1 | 14.3% (7/49) | 0 | $0.24 | 4.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_database_v2_conv1_1779022563` |
| Baseline | database_v2 | 2 | 28.6% (14/49) | 0 | $0.25 | 4.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_database_v2_conv2_1779016660` |
| Baseline | database_v2 | 2 | 26.5% (13/49) | 0 | $0.28 | 4.2 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_database_v2_conv2_1779024062` |
| Baseline | math_v2 | 0 | 72.9% (35/48) | 0 | $0.29 | 5.4 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_math_v2_conv0_1779011485` |
| Baseline | math_v2 | 0 | 60.4% (29/48) | 0 | $0.31 | 5.5 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_math_v2_conv0_1779011485` |
| Baseline | math_v2 | 1 | 79.2% (38/48) | 0 | $0.27 | 5.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_math_v2_conv1_1779011999` |
| Baseline | math_v2 | 1 | 79.2% (38/48) | 0 | $0.34 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_math_v2_conv1_1779012519` |
| Baseline | math_v2 | 2 | 83.0% (39/47) | 0 | $0.30 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/baseline_math_v2_conv2_1779012392` |
| Baseline | math_v2 | 2 | 87.2% (41/47) | 0 | $0.34 | 5.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/baseline_math_v2_conv2_1779013654` |
| Reset | actions_v2 | 0 | 94.0% (47/50) | 0 | $0.19 | 6.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_accumulate_actions_v2_conv0_1779017744` |
| Reset | actions_v2 | 0 | 90.0% (45/50) | 0 | $0.12 | 6.2 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_accumulate_actions_v2_conv0_1779026466` |
| Reset | actions_v2 | 1 | 92.0% (46/50) | 0 | $0.18 | 6.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_accumulate_actions_v2_conv1_1779017964` |
| Reset | actions_v2 | 1 | 92.0% (46/50) | 0 | $0.10 | 6.1 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_accumulate_actions_v2_conv1_1779027399` |
| Reset | actions_v2 | 2 | 90.0% (45/50) | 0 | $0.18 | 6.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_accumulate_actions_v2_conv2_1779018231` |
| Reset | actions_v2 | 2 | 94.0% (47/50) | 0 | $0.11 | 6.4 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_accumulate_actions_v2_conv2_1779028278` |
| Reset | code_v2 | 0 | 61.9% (26/42) | 0 | $0.36 | 4.8 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_code_v2_conv0_1779013413` |
| Reset | code_v2 | 0 | 55.8% (24/43) | 0 | $0.78 | 4.5 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_code_v2_conv0_1779016698` |
| Reset | code_v2 | 1 | 75.0% (30/40) | 0 | $0.37 | 4.7 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_code_v2_conv1_1779014170` |
| Reset | code_v2 | 1 | 73.8% (31/42) | 0 | $0.54 | 4.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_code_v2_conv1_1779018776` |
| Reset | code_v2 | 2 | 83.8% (31/37) | 0 | $0.42 | 4.6 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_code_v2_conv2_1779014745` |
| Reset | code_v2 | 2 | 70.0% (28/40) | 0 | $0.52 | 4.1 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_code_v2_conv2_1779020664` |
| Reset | database_v2 | 0 | 51.0% (25/49) | 0 | $0.25 | 5.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_database_v2_conv0_1779015566` |
| Reset | database_v2 | 0 | 49.0% (24/49) | 0 | $0.20 | 5.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_database_v2_conv0_1779022237` |
| Reset | database_v2 | 1 | 53.1% (26/49) | 0 | $0.21 | 5.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_database_v2_conv1_1779016462` |
| Reset | database_v2 | 1 | 57.1% (28/49) | 0 | $0.22 | 5.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_database_v2_conv1_1779023742` |
| Reset | database_v2 | 2 | 64.6% (31/48) | 1 | $0.23 | 5.1 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_database_v2_conv2_1779017360` |
| Reset | database_v2 | 2 | 59.2% (29/49) | 0 | $0.19 | 5.2 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_database_v2_conv2_1779025353` |
| Reset | math_v2 | 0 | 81.2% (39/48) | 0 | $0.26 | 6.4 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_math_v2_conv0_1779011900` |
| Reset | math_v2 | 0 | 87.2% (34/39) | 9 | $0.27 | 5.9 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_math_v2_conv0_1779012370` |
| Reset | math_v2 | 1 | 89.6% (43/48) | 0 | $0.24 | 6.3 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_math_v2_conv1_1779012338` |
| Reset | math_v2 | 1 | 81.2% (39/48) | 0 | $0.34 | 6.2 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_math_v2_conv1_1779013486` |
| Reset | math_v2 | 2 | 91.5% (43/47) | 0 | $0.24 | 6.2 | `outputs/post_neurips_ac3_phase2/gpt5_4/context_edit_v2_no_gate_math_v2_conv2_1779012692` |
| Reset | math_v2 | 2 | 83.0% (39/47) | 0 | $0.34 | 6.3 | `outputs/post_neurips_ac3_phase2/kimi_k2_6_foundry/context_edit_v2_no_gate_math_v2_conv2_1779014690` |
