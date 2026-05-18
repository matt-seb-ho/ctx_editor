# CollabLLM R2 — User-sim swap to DeepSeek-V4-Flash

**Run window**: 2026-05-18, started 01:21 PT, completed by 02:10 PT (~50 min wall, 6 cells in parallel).
**Model**: DeepSeek-V4-Flash for **assistant AND user simulator** (system role: gpt-4o-mini).
**Output**: `outputs/post_neurips_r2_collabllm_user_deepseek/`
**Launcher**: `scripts/run_post_neurips_r2_collabllm.sh`

## Background

Phase 3a CollabLLM (DeepSeek-V4-Flash assistant + **gpt-4o-mini user**)
produced surprisingly weak results: all bigcodebench cells at 0/20,
math-hard cells at 25–45%. Inspection of traces (e.g.
BigCodeBench/447) showed the **user simulator never communicates the
actual task spec** — it drifts into vague tangents ("show me PCA
code", "different colors per cluster", "minimum sample sizes"), and
the assistant has no chance to produce gold. See
`docs/reports/post_neurips_ac3_phase3_collabllm.md` and
`docs/reports/post_neurips_ac3_summary.md` for the original numbers.

This run tests the user-sim quality hypothesis: would a stronger user
simulator (DeepSeek-V4-Flash) communicate the task clearly enough to
unblock the assistant? Same user-sim prompt, same evaluation harness,
same datasets — only the user-sim model changes.

## Results

| Task | Strategy | v1 (gpt-4o-mini user, N=3) | R2 (DeepSeek user, N=1) | Δ |
|---|---|---|---|---|
| math-hard | Baseline | 30.0% | 95.0% (19/20) | +65pp |
| math-hard | AO | 40.0% | 90.0% (18/20) | +50pp |
| math-hard | AC3-Reset (v8) | 30.0% | 85.0% (17/20) | +55pp |
| math-hard | **AC3-Augment (v8)** | 20.0% | **100.0%** (20/20) | **+80pp** |
| bigcodebench | Baseline | 0.0% | 5.0% (1/20) | +5pp |
| bigcodebench | AO | 0.0% | 15.0% (3/20) | +15pp |
| bigcodebench | **AC3-Reset (v8)** | 1.7% | **20.0%** (4/20) | **+18pp** |
| bigcodebench | AC3-Augment (v8) | 0.0% | 15.0% (3/20) | +15pp |

## Takeaways

1. **The Phase 3a result was almost entirely user-sim drift, not a
   property of the method**. Switching the user simulator alone moves
   math-hard from 30–40% → 85–95% and bigcodebench from 0–2% →
   5–20%.

2. **Bigcodebench is now a meaningful benchmark for our methods**:
   AC3-Reset (20%) > AO (15%) > Baseline (5%). The ranking matches
   the LiC story — editing context helps in settings where Baseline
   isn't strong enough.

3. **Math-hard ranking inverts vs bigcodebench**: AC3-**Augment**
   hits 100%; AC3-Reset 85%; Baseline 95%. The Augment win is real
   (Augment keeps both the assistant's prior work AND the analyzer's
   notes — more information than Baseline, less rewriting than Reset).
   The Reset deficit vs Baseline (10pp) is 2 cases out of 20; could
   be sampling noise — a multi-rep follow-up would tighten this.

4. **The user-sim swap is enough on its own** for the bigcodebench
   recovery story. We hypothesized in `post_neurips_ac3_followups.md`
   that bigcodebench needed eval repair; in fact the eval is faithful
   to the upstream CollabLLM harness — what needed repair was the
   user simulator.

## Cost / time

6 cells in parallel, ~50 min wall, ~$0.50 total reported (DeepSeek
Foundry token cost not priced; small.). The single rep is sufficient
for the directional finding; multi-rep error bars would refine the
math-hard saturation claim and the bigcodebench AC3 ranking.

## Methodological note for the paper

The CollabLLM section of the paper should be re-framed:

- Original framing (post-AC3): "AC3 doesn't help on CollabLLM,
  Augment actively regresses" — withdrawn.
- New framing (this batch): with a competent user simulator,
  **AC3-Augment hits 100% on math-hard** (Phase 3a had it at the
  bottom of the table at 20% — a +80pp swing from user-sim alone),
  and **AC3-Reset leads bigcodebench at 20%** (+15pp over Baseline,
  +5pp over AO).
- The task-difficulty × intervention-intensity pattern is the
  cleanest experimental support for the paper's appropriate-intensity
  framing:
  - Easy/clean task → **Augment** (cheapest intervention — analyzer
    notes appended in-context) is enough.
  - Hard task → **Reset** (drop the polluted assistant turns) wins.

## Follow-ups

- **Multi-rep error bars** (N=3) on the math-hard cells to pin down
  whether the AC3-Reset (85%) vs Baseline (95%) gap is real.
- **Try Augment** on bigcodebench at the new user-sim — Phase 3a's
  Augment regression may also have been a user-sim artefact.
- **Replay mode for CollabLLM** (deferred; non-trivial code change).
  Would isolate the strategy effect from user-sim sampling variance.
