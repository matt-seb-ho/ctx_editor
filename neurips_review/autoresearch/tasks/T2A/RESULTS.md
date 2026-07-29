# T2A — Tier-A pollution detection (constructed pollution, no judge)

Conversations in manifest: **145**; complete across all four run cells: **0**; of those, **0** pass the mechanical probe-admissibility check and form the primary analysis set.

Excluded 19 conversation(s) whose anchor is not a reliable probe: {'harmful_anchor_not_unique': 1, 'useful_anchor_too_short_numeric': 16, 'harmful_anchor_too_short_numeric': 5, 'useful_anchor_not_unique': 2}. The check is mechanical and applied identically to the harmful and the useful side, so it cannot bias the 2x2 in either direction.

> Missing run cells: [('ac3', 'clean', 'code_v2', 'conv0'), ('ac3', 'clean', 'code_v2', 'conv1'), ('ac3', 'clean', 'database_v2', 'conv0'), ('ac3', 'clean', 'database_v2', 'conv1'), ('ac3', 'injected', 'code_v2', 'conv0'), ('ac3', 'injected', 'code_v2', 'conv1'), ('base', 'clean', 'code_v2', 'conv0'), ('base', 'clean', 'code_v2', 'conv1'), ('base', 'clean', 'database_v2', 'conv0'), ('base', 'clean', 'database_v2', 'conv1'), ('base', 'injected', 'code_v2', 'conv0'), ('base', 'injected', 'code_v2', 'conv1'), ('base', 'injected', 'database_v2', 'conv0'), ('base', 'injected', 'database_v2', 'conv1')]

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


## 2. Gate accuracy (turn level)

| arm | n | gate opened (analyzer chose to edit) |
|---|---|---|
| injected | 0 | n/a |
| clean | 0 | n/a |

On the injected arm there was *always* something to remove (one false span per conversation, by construction), so every closed gate is a miss: **gate sensitivity = n/a (0)**. Closed-gate conversations retain the harmful span by definition (0 of them).

The clean-arm figure is a *reference base rate*, **not** a false-positive rate: these are real LiC conversations that already contain natural pollution, so an open gate there may be correct. Split by whether the recorded baseline answer was right:
- clean arm, baseline correct: gate opened n/a (0)
- clean arm, baseline wrong: gate opened n/a (0)

## 3. Does removal predict accuracy?

