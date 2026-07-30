# Entanglement knob — overnight summary (read this first)

**Date:** 2026-07-30 (autonomous overnight).  **Full detail:** `WORKLOG.md` + `docs/entanglement_knob_findings.md`.

## TL;DR (the one thing to tell Philippe)

**Entanglement is a knob on task *structure*, not on phrasing.** You cannot expose it by rephrasing
the independent shards of an existing LiC benchmark — I built that, measured it, and it produces a
*difficulty confound*, not entanglement. The faithful knob requires a task where later user turns
carry their intent *through* something the assistant introduced (a selection, a callback, a
correction on a shared artifact). When you build it that way, everything Philippe predicted falls
out cleanly.

## What I built

1. **`EntanglementUserAgent`** — a user simulator with an ordinal entanglement level (0–3), wired
   into Hydra (`user_mode=entangled user_mode.entanglement_level=N`). `src/ctx_editor/agents/`.
2. **A recoverability instrument** — the key idea. For each entangled turn it measures whether an
   independent LLM can reconstruct the user's intent **with** vs **without** the assistant turns:
   - *informed* recoverability = faithfulness (should stay HIGH);
   - *blinded* recoverability = independence (should FALL as entanglement rises);
   - the gap = how genuinely entangled the turn is. `research/entanglement/src/recoverability.py`.

## What I found

- **Retrofit onto LiC math AND code → difficulty confound.** informed and blinded fall *together*,
  gap ≈ 0. Reason: LiC shards are independent pieces of the problem spec; cranking the knob just
  makes them vaguer (destroys info), it can't make them depend on the assistant (the assistant's
  turn holds nothing the next shard needs). The instrument *caught this* — validation of the knob.
- **Referent construction → the real signature.** When intent routes through an assistant-introduced
  referent, informed stays high & flat while blinded falls monotonically; gap grows to **+0.42**.
  Faithful entanglement is constructible.
- **Philippe's method figure, measured.** On that referent regime: drop-assistant (Huang/ERGO)
  **collapses** as entanglement rises (1.0 → 0.33); **decontextualize-then-edit (ours) holds**
  (→ 0.88), because it relocates the referent content into the user turn *before* dropping the
  assistant. Exactly the predicted matrix.

Figures: `artifacts/recoverability/recoverability_figure.png` (3-panel: math/code/referent) and
`artifacts/referent_methods/figure.png` (the method comparison).

## Honest caveats

- Recoverability isolates the **drop-assistant** failure only. It does *not* price accumulation's
  pollution — that's why accumulate looks fine on this axis. The *full* method comparison
  (including accumulation's cost) needs a **task-accuracy sweep on a gradable artifact-refinement
  benchmark**, which doesn't exist yet (spec in `docs/entanglement_knob_findings.md` §6).
- The referent construction is a controlled set of templated seeds (12, then re-checked at 28 for
  robustness). It's an *existence proof* that the knob is real, not a full benchmark.
- All accuracy numbers from the LiC validation pilots are N=5 — directional only.
- **The gap (informed − blinded) is judge-sensitive; faithfulness (informed staying high) is the
  judge-robust discriminator.** Re-scored with a second judge family (gpt-4o): math informed decays
  0.81 → 0.35 while referent informed stays 0.91 → 0.82 — both judges agree on that contrast, even
  though the raw gap numbers shift. Use *informed recoverability* as the certificate, not the gap.
  Figure: `artifacts/recoverability/judge_invariance_figure.png`.

## The recommendation / next step

Build the gradable **artifact-refinement / propose-then-select benchmark** (assistant proposes
non-recomputable content; later user turns reference it; gold depends on the references). That's the
substrate where the *complete* method sweep — accumulate vs drop-assistant vs summarize vs
decontextualize-then-edit, across entanglement levels — measures what Philippe wants on real task
accuracy. `run_sweep.sh` + `aggregate.py` are already built and waiting for that task.

## Where everything lives

```
research/entanglement/
  SUMMARY.md            <- you are here
  WORKLOG.md            <- chronological decisions + results (newest at bottom)
  state/progress.json   <- machine-readable state
  notes/                <- concept_exploration.md, impl_map.md, PLAN.md (from exploration agents)
  src/                  <- recoverability.py, referent_demo.py, referent_methods.py,
                           recoverability_figure.py, aggregate.py, run_validation.sh, run_sweep.sh
  artifacts/            <- all metrics.json, recoverability/*.json, *_figure.png, traces
docs/entanglement_knob_findings.md   <- the full writeup (proposal -> instrument -> results -> plan)
```
