# T2A — Tier-A pollution detection (constructed pollution, no judge)

Conversations in manifest: **145**; complete across all four run cells: **145**; of those, **126** pass the mechanical probe-admissibility check and form the primary analysis set.

Excluded 19 conversation(s) whose anchor is not a reliable probe: {'harmful_anchor_not_unique': 1, 'useful_anchor_too_short_numeric': 16, 'harmful_anchor_too_short_numeric': 5, 'useful_anchor_not_unique': 2}. The check is mechanical and applied identically to the harmful and the useful side, so it cannot bias the 2x2 in either direction.

> Missing run cells: [('base', 'harm_only', 'code_v2', 'conv0'), ('base', 'harm_only', 'code_v2', 'conv1'), ('base', 'harm_only', 'database_v2', 'conv1'), ('base', 'use_only', 'code_v2', 'conv0'), ('base', 'use_only', 'code_v2', 'conv1'), ('base', 'use_only', 'database_v2', 'conv0'), ('base', 'use_only', 'database_v2', 'conv1'), ('rw', 'clean', 'code_v2', 'conv0'), ('rw', 'clean', 'code_v2', 'conv1'), ('rw', 'clean', 'database_v2', 'conv0'), ('rw', 'clean', 'database_v2', 'conv1'), ('rw', 'injected', 'code_v2', 'conv0'), ('rw', 'injected', 'code_v2', 'conv1'), ('rw', 'injected', 'database_v2', 'conv0'), ('rw', 'injected', 'database_v2', 'conv1')]

`metrics.json` and `run_summary.json` agree on accuracy in every run cell (trap 5 check).

## 0. Positive controls (offline, no API, run over all injected conversations)

| control editor | n | removal rate | preservation rate | expected removal | expected preservation | pass |
|---|---|---|---|---|---|---|
| PC1 identity (no edit at all) | 126 | 0.000 | 1.000 | 0.0 | 1.0 | PASS |
| PC2 oracle (harmful span deleted by hand) | 126 | 1.000 | 1.000 | 1.0 | 1.0 | PASS |
| PC3 nuke (empty context) | 126 | 1.000 | 0.000 | 1.0 | 0.0 | PASS |
| PC4 delete-both | 126 | 1.000 | 0.000 | 1.0 | 0.0 | PASS |

**All controls pass: True.** PC1 proves the probe fires when the span is present (so a 0% removal rate is reachable); PC2 proves a hand-removed span scores as removed *and* that removal is separable from preservation; PC3/PC4 prove a delete-everything editor scores 100% removal and 0% preservation — i.e. removal rate alone is gameable and preservation rate is what stops it.

## 1. The 2x2


### All tasks (primary: probe-admissible conversations)  (n = 126 conversations = 126 harmful + 126 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 123 | 121 |
| **AC3 kept** | 3 | 5 |

- **Pollution removal rate** = 97.6% (123/126)  [95% CI 93.2–99.2%]
- **Preservation rate** = 4.0% (5/126)  [95% CI 1.7–9.0%]
- **Edit precision** = 50.4% (123/244)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 4.0%
- harmful span named explicitly in the analyzer's `issues` section: 78.6% (99/126); useful span named there (a false alarm): 42.1% (53/126)

### Robustness: every complete conversation, including inadmissible probes  (n = 145 conversations = 145 harmful + 145 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 142 | 135 |
| **AC3 kept** | 3 | 10 |

- **Pollution removal rate** = 97.9% (142/145)  [95% CI 94.1–99.3%]
- **Preservation rate** = 6.9% (10/145)  [95% CI 3.8–12.2%]
- **Edit precision** = 51.3% (142/277)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 2.1%
- base-rate-attributable preservation = 4.9%
- harmful span named explicitly in the analyzer's `issues` section: 79.3% (115/145); useful span named there (a false alarm): 42.1% (61/145)

### database  (n = 80 conversations = 80 harmful + 80 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 77 | 78 |
| **AC3 kept** | 3 | 2 |

- **Pollution removal rate** = 96.2% (77/80)  [95% CI 89.5–98.7%]
- **Preservation rate** = 2.5% (2/80)  [95% CI 0.7–8.7%]
- **Edit precision** = 49.7% (77/155)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 2.5%
- harmful span named explicitly in the analyzer's `issues` section: 82.5% (66/80); useful span named there (a false alarm): 37.5% (30/80)

### code  (n = 46 conversations = 46 harmful + 46 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 46 | 43 |
| **AC3 kept** | 0 | 3 |

- **Pollution removal rate** = 100.0% (46/46)  [95% CI 92.3–100.0%]
- **Preservation rate** = 6.5% (3/46)  [95% CI 2.2–17.5%]
- **Edit precision** = 51.7% (46/89)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 6.5%
- harmful span named explicitly in the analyzer's `issues` section: 71.7% (33/46); useful span named there (a false alarm): 50.0% (23/46)

### pair design = MATCHED  (n = 29 conversations = 29 harmful + 29 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 29 | 29 |
| **AC3 kept** | 0 | 0 |

- **Pollution removal rate** = 100.0% (29/29)  [95% CI 88.3–100.0%]
- **Preservation rate** = 0.0% (0/29)  [95% CI 0.0–11.7%]
- **Edit precision** = 50.0% (29/58)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 0.0%
- harmful span named explicitly in the analyzer's `issues` section: 41.4% (12/29); useful span named there (a false alarm): 44.8% (13/29)

### pair design = MIXED  (n = 97 conversations = 97 harmful + 97 useful spans)

| | harmful (injected, false by construction) | useful (injected, true by construction) |
|---|---|---|
| **AC3 removed** | 94 | 92 |
| **AC3 kept** | 3 | 5 |

- **Pollution removal rate** = 96.9% (94/97)  [95% CI 91.3–98.9%]
- **Preservation rate** = 5.2% (5/97)  [95% CI 2.2–11.5%]
- **Edit precision** = 50.5% (94/186)
- clean-arm spontaneous base rate: harmful anchor 0.0%, useful anchor 0.0%
- base-rate-attributable preservation = 5.2%
- harmful span named explicitly in the analyzer's `issues` section: 89.7% (87/97); useful span named there (a false alarm): 41.2% (40/97)

- removal by harmful type `H_PHANTOM_COL`: 95.5% (63/66)

- removal by harmful type `H_PHANTOM_PARAM`: 100.0% (31/31)

- removal by harmful type `H_WRONG_EXEC_FACT`: 100.0% (14/14)

- removal by harmful type `H_WRONG_TEST`: 100.0% (15/15)
- preservation by useful type `U_EXEC_FACT`: 2.5% (2/80)
- preservation by useful type `U_TRUE_SIG`: 9.1% (2/22)
- preservation by useful type `U_TRUE_TEST`: 4.2% (1/24)

## 2. Gate accuracy (turn level)

| arm | n | gate opened (analyzer chose to edit) |
|---|---|---|
| injected | 126 | 98.4% (124/126) |
| clean | 126 | 96.8% (122/126) |

On the injected arm there was *always* something to remove (one false span per conversation, by construction), so every closed gate is a miss: **gate sensitivity = 98.4% (124/126)**. Closed-gate conversations retain the harmful span by definition (2 of them).

The clean-arm figure is a *reference base rate*, **not** a false-positive rate: these are real LiC conversations that already contain natural pollution, so an open gate there may be correct. Split by whether the recorded baseline answer was right:
- clean arm, baseline correct: gate opened 94.3% (33/35)
- clean arm, baseline wrong: gate opened 97.8% (89/91)

## 3. Does removal predict accuracy?

| arm | Baseline (full context) | AC3-Reset | delta |
|---|---|---|---|
| clean | 27.8% (35/126) | 65.1% (82/126) | +37.3pp |
| injected | 36.5% (46/126) | 65.1% (82/126) | +28.6pp |

- Injecting one false span costs the **Baseline** +8.7pp (35/126 -> 46/126).
- It costs **AC3** +0.0pp (82/126 -> 82/126).
- Difference-in-differences (AC3's protection against the injected pollution): **-8.7pp**.

Per-conversation split by whether AC3 actually removed the injected span:

| AC3 removed the harmful span? | n | Baseline acc | AC3 acc | delta |
|---|---|---|---|---|
| yes | 123 | 36.6% | 65.9% | +29.3pp |
| no | 3 | 33.3% | 33.3% | +0.0pp |
