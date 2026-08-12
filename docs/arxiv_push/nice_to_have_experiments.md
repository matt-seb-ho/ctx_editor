# arXiv v1 — nice-to-have experiments & pre-publication checklist

**Written:** 2026-08-12, at the close of the arXiv-update pass (the pass that folded all
rebuttal-period work into `writing/overleaf_repo/arxiv/neurips_2026_conference.tex`).
**Purpose:** the arXiv draft is internally consistent and honest *as written* — nothing below
blocks posting a v1. This is the discussion list Matthew asked for: what would make a v2
stronger, plus the small correctness/hygiene items that should be cleared before or shortly
after the first arXiv post.

The draft already stands on its own without any of these. They are ranked by leverage.

---

## A. Pre-publication hygiene (cheap, do before or immediately after v1 post)

These are not experiments; they are finishing touches the writing pass could not complete alone.

1. **Author block.** The `.tex` is switched to `\usepackage[preprint]{neurips_2026}` (de-anon),
   but `\author{}` is a `TODO` placeholder ("Anonymous Authors"). Fill in the real author list,
   order, and affiliations before posting. This is the one hard blocker for a public arXiv post.
2. **Figure 1 art vs. corrected tau2 caption.** `assets/ctxe_story.drawio.png` still draws
   AC3 ≥ vanilla at the tau2 (stateful) end of the spectrum. The corrected caption now says AC3
   *remains viable but does not exceed full context* there. The schematic must be redrawn so the
   tau2 bar shows parity/slightly-below, not a win. The `.drawio` source is missing from the repo;
   needs a co-author who has it (or a redraw from scratch). **Correctness item, not cosmetic.**
3. **Hyphenation sweep.** "Gated Reset" vs "Gated-Reset" is mixed throughout. One-pass copyedit.
4. **Redundant `arxiv/assets/prompts/`.** The duplicate carries a per-folder copy of the prompt
   `.txt` files; Overleaf resolves `assets/` from the project root anyway (same as `neurips/`).
   Harmless, but could be deleted to avoid drift if the root prompts are ever edited.

## B. Provenance / number-confirmation items (flagged during the evidence fold-in)

Small verifications; the numbers are posted publicly already, but the underlying counters were
flagged as not-fully-pinned when the new-evidence subsections were drafted.

5. **MT-OSC "6 of 107 conversations" counter (FLAG-1).** The posted v6 reply and the new
   §"Matched-compute baselines" print "edits context in only 6 of 107 conversations." T30 worklog
   flags this as the one figure it "would not post without resolving": instrumentation elsewhere
   records ~30 firings across 107 (0.3/conv) and 0.62 log-events/conv at w=4. All are mutually
   consistent (multiple firings per edited conversation), but confirm a single artifact that says
   "6 of 107 conversations edited," or fall back to the call-based "~30 firings across 107 (0.3/conv)".
6. **LiC per-cell floor "n≈113–150" (FLAG-2).** The draft prints "up to 150 conversations per cell"
   (fully sourced). The lower bound 113 was asserted only in a handoff summary, not traced to a
   per-cell RESULTS count. If you want to print a range rather than a ceiling, verify the 113 floor.

## C. Experiments that would materially strengthen a v2 (ranked)

7. **Root-cause the unexplained gpt-5.4 tau2 cell.** On gpt-5.4 the re-measured baseline reproduced
   exactly (68.4 vs 68.4) yet every AC3 arm fell 10–37pp below its originally reported value; model
   substitution, gating failure, degenerate termination, and rate limits were ruled out. The paper
   discloses this honestly as unexplained. Resolving it (harness diff bisect against the original
   run config; per-rollout trace diffing) would remove the one "we don't know why" in the results.
8. **Real-user (non-simulated) evaluation.** All four benchmarks use simulated users. Even a small
   human-in-the-loop study on WildChat-style referential turns would answer the standing
   "simulated-user" limitation and the reviewers' external-validity concern more directly than any
   additional simulated result.
9. **tau2 beyond `telecom_small`, and longer horizon.** Current agentic evidence is one subset. A
   second tau2 domain (e.g. `airline`, `retail`) and/or a longer-horizon task would test whether the
   AO-collapse / selective-editing-viable finding is domain-general or a `telecom_small` artifact,
   and would let the agentic claim carry more than "viability."
10. **CollabLLM & WildChat replication (N>1).** Both are currently single-run and flagged
    "preliminary in this respect" in the checklist. Running ≥3 reruns and reporting mean±std (as LiC
    and tau2 now do) would let these columns carry paired significance instead of point estimates.
11. **U-Fold experiment.** Committed for camera-ready, never run. (Referentiality-vs-editing-benefit
    curve.) Present as future work in v1; running it would make the "spectrum" narrative empirical
    rather than schematic (it is currently Figure 1's qualitative claim).
12. **High-pollution self-reflection arm.** Committed for camera-ready, never run. Tests whether the
    contagious-pollution result holds under an explicit self-reflection editor at high pollution.
13. **MT-OSC on its native long-horizon regime.** The current comparison is scoped-and-fair for LiC
    length (where MT-OSC is a near no-op by design). A comparison on the long conversations MT-OSC
    was built for would make the baseline comparison two-sided rather than "it doesn't fire on short
    inputs." Frame carefully: this is testing *our* method out-of-regime, not just theirs.
14. **Analyzer self-distillation feasibility probe.** The discussion floats folding the analyzer's
    plain-text reasoning into the base model via self-distillation (no extra inference call), citing
    recent methods but with zero experiments. A single feasibility probe (does a distilled analyzer
    retain any of the +12.9–39.9pp analyzer-robustness gain?) would upgrade this from speculation to
    a preliminary result — potentially the strongest v2 headline given the cost objection.
15. **Long-horizon coding (multi-file / iterative design).** Named in Limitations as untested. The
    most natural "does this scale to real agentic work" extension.

## D. Explicitly out of scope for v1 (do not present as done)

- Anything in C above — all are future work in the current draft. Do not let a v2 draft quietly
  upgrade a C-item to "done" without the run behind it (this was the v5 posting-failure mode).
- Any tau2 *improvement* claim over full context — permanently withdrawn (re-measured baselines).
- Any "every operator beats baseline" or "surgical span preservation" framing — retired.
