# T16 — analyzer gate-open rate, re-derived from traces

LiC root:       /home/t-matthewho/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1
CollabLLM root: /home/t-matthewho/ac3/t14_snapshot/ctx_editor/outputs/post_neurips_ac3_phase3_collabllm

## LiC

**Headline arm** (`context_edit_v2_no_gate`, the arm the original reconstruction was built from):

- gate-open, **invocation (turn) denominator**: 539/547 = **98.5%**
- gate-open, **per-sample verdict, corrected denominator**: 539/547 = **98.5%**
- gate-open, **conversation level** (gate opened on >=1 turn): 539/547 = **98.5%**
- gate-open, LEGACY per-sample verdict / all-traces denominator: 539/554 = 97.3%  (7 samples the analyzer never ran on, silently scored as gate-closed)

### LiC — context_edit_v2_no_gate by task

| task | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|
| actions | 150 | 0 | 150 | 149 | **99.3%** | 149 | 99.3% |
| code | 113 | 7 | 106 | 103 | **97.2%** | 103 | 91.2% |
| database | 147 | 0 | 147 | 144 | **98.0%** | 144 | 98.0% |
| math | 144 | 0 | 144 | 143 | **99.3%** | 143 | 99.3% |

### LiC — context_edit_v2_no_gate by task x cell

| task | cell | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|---|
| actions | 0 | 50 | 0 | 50 | 49 | **98.0%** | 49 | 98.0% |
| actions | 1 | 50 | 0 | 50 | 50 | **100.0%** | 50 | 100.0% |
| actions | 2 | 50 | 0 | 50 | 50 | **100.0%** | 50 | 100.0% |
| code | 0 | 40 | 3 | 37 | 37 | **100.0%** | 37 | 92.5% |
| code | 1 | 37 | 2 | 35 | 33 | **94.3%** | 33 | 89.2% |
| code | 2 | 36 | 2 | 34 | 33 | **97.1%** | 33 | 91.7% |
| database | 0 | 49 | 0 | 49 | 49 | **100.0%** | 49 | 100.0% |
| database | 1 | 49 | 0 | 49 | 48 | **98.0%** | 48 | 98.0% |
| database | 2 | 49 | 0 | 49 | 47 | **95.9%** | 47 | 95.9% |
| math | 0 | 48 | 0 | 48 | 48 | **100.0%** | 48 | 100.0% |
| math | 1 | 48 | 0 | 48 | 48 | **100.0%** | 48 | 100.0% |
| math | 2 | 48 | 0 | 48 | 47 | **97.9%** | 47 | 97.9% |

### LiC — all analyzer-bearing strategies

| strategy | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|
| ac3_rewrite_lic | 554 | 554 | 0 | 0 | **—** | 0 | 0.0% |
| append_analysis | 554 | 7 | 547 | 539 | **98.5%** | 539 | 97.3% |
| context_edit_v2_gated | 554 | 22 | 532 | 524 | **98.5%** | 524 | 94.6% |
| context_edit_v2_no_gate | 554 | 7 | 547 | 539 | **98.5%** | 539 | 97.3% |

### LiC — strategy x task

| strategy | task | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|---|
| ac3_rewrite_lic | actions | 150 | 150 | 0 | 0 | **—** | 0 | 0.0% |
| ac3_rewrite_lic | code | 113 | 113 | 0 | 0 | **—** | 0 | 0.0% |
| ac3_rewrite_lic | database | 147 | 147 | 0 | 0 | **—** | 0 | 0.0% |
| ac3_rewrite_lic | math | 144 | 144 | 0 | 0 | **—** | 0 | 0.0% |
| append_analysis | actions | 150 | 0 | 150 | 149 | **99.3%** | 149 | 99.3% |
| append_analysis | code | 113 | 7 | 106 | 103 | **97.2%** | 103 | 91.2% |
| append_analysis | database | 147 | 0 | 147 | 144 | **98.0%** | 144 | 98.0% |
| append_analysis | math | 144 | 0 | 144 | 143 | **99.3%** | 143 | 99.3% |
| context_edit_v2_gated | actions | 150 | 0 | 150 | 149 | **99.3%** | 149 | 99.3% |
| context_edit_v2_gated | code | 113 | 13 | 100 | 97 | **97.0%** | 97 | 85.8% |
| context_edit_v2_gated | database | 147 | 7 | 140 | 137 | **97.9%** | 137 | 93.2% |
| context_edit_v2_gated | math | 144 | 2 | 142 | 141 | **99.3%** | 141 | 97.9% |
| context_edit_v2_no_gate | actions | 150 | 0 | 150 | 149 | **99.3%** | 149 | 99.3% |
| context_edit_v2_no_gate | code | 113 | 7 | 106 | 103 | **97.2%** | 103 | 91.2% |
| context_edit_v2_no_gate | database | 147 | 0 | 147 | 144 | **98.0%** | 144 | 98.0% |
| context_edit_v2_no_gate | math | 144 | 0 | 144 | 143 | **99.3%** | 143 | 99.3% |

### Diagnostic — `needs_edit` vs the analyzer's own `issues` field (LiC / context_edit_v2_no_gate)

| `issues` content | gate open | gate closed |
|---|---|---|
| issues_stated | 384 | 0 |
| issues_none | 155 | 1 |
| empty | 0 | 7 |

**155 / 539 (28.8%) of gate-OPEN records have the analyzer explicitly writing "None" under `issues`.** `needs_edit` is therefore only loosely coupled to the analyzer having found a problem — read the gate-open rate as a firing rate, not as a detection rate.

## CollabLLM

**Headline arm** (`ac3_reset_v8`, the arm the original reconstruction was built from):

- gate-open, **invocation (turn) denominator**: 628/659 = **95.3%**
- gate-open, **per-sample verdict, corrected denominator**: 112/118 = **94.9%**
- gate-open, **conversation level** (gate opened on >=1 turn): 118/118 = **100.0%**
- gate-open, LEGACY per-sample verdict / all-traces denominator: 112/120 = 93.3%  (2 samples the analyzer never ran on, silently scored as gate-closed)

### CollabLLM — ac3_reset_v8 by task

| task | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|
| bigcodebench | 60 | 0 | 374 | 352 | **94.1%** | 56 | 93.3% |
| math-hard | 60 | 2 | 285 | 276 | **96.8%** | 56 | 93.3% |

### CollabLLM — ac3_reset_v8 by task x cell

| task | cell | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|---|
| bigcodebench | 1 | 20 | 0 | 131 | 122 | **93.1%** | 17 | 85.0% |
| bigcodebench | 2 | 20 | 0 | 125 | 120 | **96.0%** | 20 | 100.0% |
| bigcodebench | 3 | 20 | 0 | 118 | 110 | **93.2%** | 19 | 95.0% |
| math-hard | 1 | 20 | 0 | 93 | 90 | **96.8%** | 19 | 95.0% |
| math-hard | 2 | 20 | 1 | 102 | 98 | **96.1%** | 18 | 90.0% |
| math-hard | 3 | 20 | 1 | 90 | 88 | **97.8%** | 19 | 95.0% |

### CollabLLM — all analyzer-bearing strategies

| strategy | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|
| ac3_augment_v8 | 120 | 26 | 894 | 857 | **95.9%** | 91 | 75.8% |
| ac3_reset_v8 | 120 | 2 | 659 | 628 | **95.3%** | 112 | 93.3% |

### CollabLLM — strategy x task

| strategy | task | n samples | analyzer never ran | n invocations | n gate-open | **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |
|---|---|---|---|---|---|---|---|---|
| ac3_augment_v8 | bigcodebench | 60 | 14 | 448 | 424 | **94.6%** | 43 | 71.7% |
| ac3_augment_v8 | math-hard | 60 | 12 | 446 | 433 | **97.1%** | 48 | 80.0% |
| ac3_reset_v8 | bigcodebench | 60 | 0 | 374 | 352 | **94.1%** | 56 | 93.3% |
| ac3_reset_v8 | math-hard | 60 | 2 | 285 | 276 | **96.8%** | 56 | 93.3% |

### Diagnostic — `needs_edit` vs the analyzer's own `issues` field (CollabLLM / ac3_reset_v8)

| `issues` content | gate open | gate closed |
|---|---|---|
| issues_stated | 167 | 0 |
| issues_none | 461 | 2 |
| empty | 0 | 29 |

**461 / 628 (73.4%) of gate-OPEN records have the analyzer explicitly writing "None" under `issues`.** `needs_edit` is therefore only loosely coupled to the analyzer having found a problem — read the gate-open rate as a firing rate, not as a detection rate.

## Positive controls

- **C1 independent regex parser**: raw-text scan finds 3087 true / 92 false = 3179 `needs_edit` fields; the JSON walk finds 3087 open / 3179 invocations. MATCH
- **C2 invocations per sample, by arm** (0 calls => excluded from the invocation denominator, NOT counted as gate-closed):
    - CollabLLM/ac3_augment_v8: n=120, calls-per-sample histogram {0: 26, 1: 7, 2: 3, 3: 3, 6: 2, 7: 1, 8: 1, 10: 2, 11: 75}
    - CollabLLM/ac3_reset_v8: n=120, calls-per-sample histogram {0: 2, 1: 8, 2: 14, 3: 7, 4: 4, 5: 4, 6: 5, 7: 72, 8: 4}
    - LiC/ac3_rewrite_lic: n=554, calls-per-sample histogram {0: 554}
    - LiC/append_analysis: n=554, calls-per-sample histogram {0: 7, 1: 547}
    - LiC/context_edit_v2_gated: n=554, calls-per-sample histogram {0: 22, 1: 532}
    - LiC/context_edit_v2_no_gate: n=554, calls-per-sample histogram {0: 7, 1: 547}
- **C3 cross-check against `edit_decision.should_edit`** (a different log record written by a different code path), restricted to the 1197 samples that emit any `edit_decision`: 0 disagree with `needs_edit`.

wrote neurips_review/autoresearch/tasks/T16/gate_stats.json
