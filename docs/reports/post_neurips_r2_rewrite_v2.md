## AC3 phase results — post_neurips_r2_rewrite_v2

Mean accuracy across prefix replicates (typically n=3). For each cell the table shows mean ± std (pp).

| Strategy | math_v2 | code_v2 | database_v2 | actions_v2 | Δ vs Baseline (avg pp) |
|---|---|---|---|---|---|
| Rewrite-v2 | 70.8% ± 14.4pp (n=3) | 36.6% ± 9.9pp (n=3) | 21.8% ± 5.1pp (n=3) | 70.0% ± 7.2pp (n=3) | — |

### Per-cell detail

| Strategy | Task | Conv | Accuracy | Errors | Cost | Avg Turns | Output Dir |
|---|---|---|---|---|---|---|---|
| Rewrite-v2 | actions_v2 | 0 | 68.0% (34/50) | 0 | $0.01 | 6.3 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_actions_v2_conv0_1779092554` |
| Rewrite-v2 | actions_v2 | 1 | 64.0% (32/50) | 0 | $0.01 | 6.1 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_actions_v2_conv1_1779092554` |
| Rewrite-v2 | actions_v2 | 2 | 78.0% (39/50) | 0 | $0.01 | 6.0 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_actions_v2_conv2_1779092554` |
| Rewrite-v2 | code_v2 | 0 | 27.5% (11/40) | 0 | $0.01 | 6.5 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_code_v2_conv0_1779092554` |
| Rewrite-v2 | code_v2 | 1 | 35.1% (13/37) | 0 | $0.01 | 6.3 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_code_v2_conv1_1779092554` |
| Rewrite-v2 | code_v2 | 2 | 47.2% (17/36) | 0 | $0.01 | 6.2 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_code_v2_conv2_1779092554` |
| Rewrite-v2 | database_v2 | 0 | 16.3% (8/49) | 0 | $0.01 | 5.4 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_database_v2_conv0_1779092554` |
| Rewrite-v2 | database_v2 | 1 | 22.4% (11/49) | 0 | $0.01 | 5.3 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_database_v2_conv1_1779092554` |
| Rewrite-v2 | database_v2 | 2 | 26.5% (13/49) | 0 | $0.01 | 5.0 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_database_v2_conv2_1779092554` |
| Rewrite-v2 | math_v2 | 0 | 54.2% (26/48) | 0 | $0.01 | 6.6 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_math_v2_conv0_1779092554` |
| Rewrite-v2 | math_v2 | 1 | 79.2% (38/48) | 0 | $0.01 | 6.3 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_math_v2_conv1_1779092554` |
| Rewrite-v2 | math_v2 | 2 | 79.2% (38/48) | 0 | $0.01 | 6.2 | `outputs/post_neurips_r2_rewrite_v2/ac3_rewrite_v2_lic_math_v2_conv2_1779092554` |
