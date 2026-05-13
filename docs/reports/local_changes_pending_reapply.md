# Local changes pending re-verification against the new infra

Written **2026-05-12** during the cleanup that reset local `main` to
`origin/main` after pulling the experiment-infrastructure refactor (AC3
rename, analyzer prompt registry, Hydra-ified Huang eval, tau2 hybrid, …).

Three small local fixes were dropped during that reset because the files
they touched were heavily rewritten upstream. The fixes may already be
incorporated, no longer relevant, or still missing — they should each be
checked once before we trust the new pipeline.

The full pre-reset state is preserved on branch `backup/pre-infra-pull`
(commit `ed800ca`). Specific commit SHAs referenced below are on that
branch.

## 1. `turn_results.jsonl` response truncation (was: commit `be5b32a`)

**Symptom that motivated the fix.** Assistant responses were being sliced to
`[:1000]` before being written to `turn_results.jsonl`. Phase 2 judged the
full response inline before truncation, so the original-run scores were
fine, but any **re-judge run** that re-read `turn_results.jsonl` was scoring
incomplete responses. This was the root cause of the apparent "judge
sensitivity" finding for DeepSeek+gpt-5 — once truncation was removed,
gpt-5-as-judge agreed S1.5 beat AO 70.6% / 72.5% (baseline / +memory) and
FC 68.6% / 76.5%. The "judge disagreement" was a truncation artifact.

**Pre-reset patch (paraphrase).** In the wildchat memory and Huang eval
phase-2 runners, drop the `response[:1000]` slice when constructing the
record that gets written to `turn_results.jsonl`. Store the full string.

**What to verify against the new infra.**

1. After the Hydra-ified Huang eval refactor (commit `8d141b6` on
   `origin/main`), find the equivalent of the old
   `src/ctx_editor/huang_eval/run_phase2.py` write-path and confirm it
   stores full responses, not truncated ones.
2. Same for `scripts/run_wildchat_memory.py` (or whatever replaced it
   under the new launcher layout).
3. If truncation is still present, re-port the fix: just remove `[:1000]`
   (or equivalent slice/clip) on the response field at write time.
4. If re-judge tooling has its own response store, audit that too — the
   bug class is "store-then-rejudge with a lossy store."

## 2. `run_phase2.py` result-dict newline bug (uncommitted, pre-reset)

Two physical lines in the pre-reset `run_phase2.py` had been mashed
together so that `result["..._response"]` and `result["..._analysis"]`
shared a line:

```python
result["s15_response"] = s15_response            result["s15_analysis"] = s15_analysis
```

This was almost certainly a merge/edit accident — Python would parse this
as a `SyntaxError`. Same bug for the `s2_` variants. The uncommitted local
diff inserted the missing newlines.

**What to verify.** Just confirm the post-refactor equivalent file does
not have the same mash-together. The Hydra-ified rewrite probably wrote
this section from scratch, so the bug almost certainly does not exist
anymore — but eyeball it once to be sure.

## 3. `process_failure_turn` kwarg ordering (uncommitted, pre-reset)

Cosmetic: `memory=None` had been declared before the required-positional
parameters that followed it (`run_s2`, `regenerate_baselines`,
`results_file`, `rng`), which Python rejects at function-definition time
on stricter interpreters. The local diff moved `memory=None` to the end of
the parameter list.

**What to verify.** The Hydra rewrite likely reorganized this signature
entirely. If `memory` is still a kwarg in the new entry-point, just
confirm it comes after all required positionals.

## How to dig up the original diffs verbatim

```bash
# response-truncation fix
git show backup/pre-infra-pull~3   # commit be5b32a in old order; check log

# OR look it up by message:
git log backup/pre-infra-pull --oneline | grep truncation

# uncommitted-at-snapshot-time pieces (newline + kwarg reorder)
git show backup/pre-infra-pull -- src/ctx_editor/huang_eval/run_phase2.py
```
