# T2c — Is the analyzer auditing, or re-solving the task? (Reviewer 5YHP)

**Source artifact for every number below:** `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/`
(the paper's phase-1 LiC replay matrix, DeepSeek-V4-Flash; extracted from
`~/ac3/blob_staging/snapshot.tar.gz` — only `winners.json` survives at `outputs/post_neurips_ac3_phase1/`).
Pairing is per sample on `(task, conv_prefix, sample_id)`; the replay design guarantees the
baseline and AC3 arms see identical samples and identical conversation prefixes.
Statistic: exact two-sided McNemar (binomial on discordant pairs); CI is Wilson on the
discordant proportion, rescaled to the accuracy difference.
Method, prompts, dead ends and hand-validation: [`worklog.md`](worklog.md).

**One-line answer:** on `code` and `database` the analyzer verifiably never supplies the correct
answer (0/106 and 1/147), yet AC3 gains +30.2pp and +26.5pp there; across math+code+database the
gain on the 329 conversations with no verified leak is **+20.7pp (p<0.0001)**. `math` is the
exception — 38-40% of its analyzer outputs contain the derived gold answer and its entire gain
sits on that subset.

### Table 1 — How often does the analyzer hand the assistant the answer?

Rates over every analyzer invocation in the AC3-Reset arm (one per conversation; LiC replay matrix, DeepSeek-V4-Flash).

| task | n | judge says LEAKS/PARTIAL<br>(upper bound) | answer verified correct<br>(**strict leak rate**) | model-free numeric probe<br>(math only) |
|---|---|---|---|---|
| math | 144 | 110 (76%) | **54 (38%)** | 57 (40%) |
| code | 106 | 33 (31%) | **0 (0%)** | n/a |
| database | 147 | 25 (17%) | **1 (1%)** | n/a |
| actions | 150 | 14 (9%) | **3 (2%)** | n/a |
| **all** | **547** | **182 (33%)** | **58 (11%)** | — |


### Table 2 — AC3 vs full-context Baseline, paired per sample, split by leakage (primary — union: analyzer output verified to contain the correct answer OR the math-only model-free numeric probe fires)

| subset | n | Baseline | AC3 | Δ (pp) | 95% CI | W/L | McNemar p |
|---|---|---|---|---|---|---|---|
| **AC3-Reset, math+code+database** | 397 | 43.1% | 64.5% | **+21.4** | [+16.4, +25.3] | 110/25 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 329 | 36.5% | 57.1% | **+20.7** | [+14.8, +25.3] | 93/25 | <0.0001 |
| &nbsp;&nbsp;LEAK | 68 | 75.0% | 100.0% | **+25.0** | [+15.8, +25.0] | 17/0 | <0.0001 |
| **AC3-Reset, math** | 144 | 72.2% | 81.9% | **+9.7** | [+1.8, +15.7] | 24/10 | 0.024 |
| &nbsp;&nbsp;NO_LEAK | 77 | 68.8% | 66.2% | **-2.6** | [-11.9, +7.6] | 8/10 | 0.815 |
| &nbsp;&nbsp;LEAK | 67 | 76.1% | 100.0% | **+23.9** | [+14.6, +23.9] | 16/0 | <0.0001 |
| **AC3-Reset, code** | 106 | 32.1% | 62.3% | **+30.2** | [+20.3, +34.7] | 36/4 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 106 | 32.1% | 62.3% | **+30.2** | [+20.3, +34.7] | 36/4 | <0.0001 |
| **AC3-Reset, database** | 147 | 22.4% | 49.0% | **+26.5** | [+17.0, +32.9] | 50/11 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 146 | 22.6% | 48.6% | **+26.0** | [+16.5, +32.4] | 49/11 | <0.0001 |
| &nbsp;&nbsp;LEAK | 1 | 0.0% | 100.0% | **+100.0** | [-58.7, +100.0] | 1/0 | 1.000 |
| **AC3-Reset, actions** | 150 | 76.0% | 83.3% | **+7.3** | [+0.1, +13.0] | 21/10 | 0.071 |
| &nbsp;&nbsp;NO_LEAK | 147 | 76.2% | 83.0% | **+6.8** | [-0.5, +12.6] | 20/10 | 0.099 |
| &nbsp;&nbsp;LEAK | 3 | 66.7% | 100.0% | **+33.3** | [-19.6, +33.3] | 1/0 | 1.000 |
| | | | | | | | |
| **AC3-Gated-Reset, math+code+database** | 382 | 41.9% | 62.8% | **+20.9** | [+16.0, +24.6] | 101/21 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 311 | 35.0% | 54.7% | **+19.6** | [+13.8, +24.0] | 82/21 | <0.0001 |
| &nbsp;&nbsp;LEAK | 71 | 71.8% | 98.6% | **+26.8** | [+17.8, +26.8] | 19/0 | <0.0001 |
| **AC3-Gated-Reset, actions** | 150 | 76.0% | 85.3% | **+9.3** | [+2.2, +14.3] | 22/8 | 0.016 |
| &nbsp;&nbsp;NO_LEAK | 145 | 76.6% | 84.8% | **+8.3** | [+1.1, +13.4] | 20/8 | 0.036 |
| &nbsp;&nbsp;LEAK | 5 | 60.0% | 100.0% | **+40.0** | [-12.6, +40.0] | 2/0 | 0.500 |


### Table 2 — AC3 vs full-context Baseline, paired per sample, split by leakage (conservative: LLM judge's 3-way label, LEAKS+PARTIAL vs NO_LEAK)

| subset | n | Baseline | AC3 | Δ (pp) | 95% CI | W/L | McNemar p |
|---|---|---|---|---|---|---|---|
| **AC3-Reset, math+code+database** | 397 | 43.1% | 64.5% | **+21.4** | [+16.4, +25.3] | 110/25 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 229 | 34.9% | 59.4% | **+24.5** | [+17.3, +29.6] | 72/16 | <0.0001 |
| &nbsp;&nbsp;LEAK | 168 | 54.2% | 71.4% | **+17.3** | [+9.8, +22.1] | 38/9 | <0.0001 |
| **AC3-Reset, math** | 144 | 72.2% | 81.9% | **+9.7** | [+1.8, +15.7] | 24/10 | 0.024 |
| &nbsp;&nbsp;NO_LEAK | 34 | 70.6% | 76.5% | **+5.9** | [-12.7, +21.7] | 7/5 | 0.774 |
| &nbsp;&nbsp;LEAK | 110 | 72.7% | 83.6% | **+10.9** | [+2.6, +16.0] | 17/5 | 0.017 |
| **AC3-Reset, code** | 106 | 32.1% | 62.3% | **+30.2** | [+20.3, +34.7] | 36/4 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 73 | 41.1% | 65.8% | **+24.7** | [+12.5, +30.0] | 21/3 | 0.000 |
| &nbsp;&nbsp;LEAK | 33 | 12.1% | 54.5% | **+42.4** | [+21.0, +47.4] | 15/1 | 0.001 |
| **AC3-Reset, database** | 147 | 22.4% | 49.0% | **+26.5** | [+17.0, +32.9] | 50/11 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 122 | 21.3% | 50.8% | **+29.5** | [+19.2, +35.8] | 44/8 | <0.0001 |
| &nbsp;&nbsp;LEAK | 25 | 28.0% | 40.0% | **+12.0** | [-10.5, +27.3] | 6/3 | 0.508 |
| **AC3-Reset, actions** | 150 | 76.0% | 83.3% | **+7.3** | [+0.1, +13.0] | 21/10 | 0.071 |
| &nbsp;&nbsp;NO_LEAK | 136 | 77.2% | 85.3% | **+8.1** | [+0.6, +13.6] | 19/8 | 0.052 |
| &nbsp;&nbsp;LEAK | 14 | 64.3% | 64.3% | **+0.0** | [-20.0, +20.0] | 2/2 | 1.000 |
| | | | | | | | |
| **AC3-Gated-Reset, math+code+database** | 382 | 41.9% | 62.8% | **+20.9** | [+16.0, +24.6] | 101/21 | <0.0001 |
| &nbsp;&nbsp;NO_LEAK | 210 | 35.7% | 58.1% | **+22.4** | [+15.4, +27.1] | 59/12 | <0.0001 |
| &nbsp;&nbsp;LEAK | 172 | 49.4% | 68.6% | **+19.2** | [+11.7, +24.0] | 42/9 | <0.0001 |
| **AC3-Gated-Reset, actions** | 150 | 76.0% | 85.3% | **+9.3** | [+2.2, +14.3] | 22/8 | 0.016 |
| &nbsp;&nbsp;NO_LEAK | 136 | 78.7% | 85.3% | **+6.6** | [-0.6, +12.1] | 17/8 | 0.108 |
| &nbsp;&nbsp;LEAK | 14 | 50.0% | 85.7% | **+35.7** | [+4.7, +35.7] | 5/0 | 0.062 |
