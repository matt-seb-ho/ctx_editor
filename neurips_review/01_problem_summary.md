# Problem Summary — AC3 NeurIPS Reviews (Sub. 27902)

Distilled from the three reviews + AC meta. Deduplicated into distinct **problems**, each tagged with who raised it and what would actually resolve it. Ordered by how decisive it is to the decision (the AC meta named three: generalizability, theoretical-assumption validity, and experimental weakness).

The AC framed rejection around **three pillars**. Every reviewer concern below maps into one of them:

- **P (Pillar) — Generalizability:** "the method changes for each setting."
- **P — Assumptions:** structural exclusion / hard-attention only works when user turns self-specify the task.
- **P — Evidence:** limited benchmarks, no statistics, mixed results.

---

## A. Generalizability — "AC3 is not one method" (AC + Vg97 + 5YHP)

**The single most decisive concern.** The AC led with it. Reviewers observe the pipeline is reconfigured per benchmark:

- LiC → two-stage, **user-only hard-attention** spec extraction + Reset/Gated-Reset.
- CollabLLM → **single-pass Rewrite, no structural exclusion** (intent weaves through assistant turns).
- WildChat → several operators evaluated.
- tau2 → analyzer reframed as **"strategic reflection,"** tracks environment state, caps resets.

**Reviewer ask:** "Which components are essential vs. task-specific?" (Vg97 Q4, 5YHP W2). Is this one algorithm, a family of prompt patterns, or several task-specific variants?

**What resolves it:** a single unified algorithm statement with a small, principled set of knobs whose settings are *derived from* a measurable property of the setting (referentiality/statefulness), not hand-tuned per benchmark. Post-NeurIPS standardization work is exactly aimed here.

---

## B. Statistical reliability (AC + all three reviewers)

The most universally raised concern.

- LiC cells have **18–25 samples**; only **Gated-Reset replicated 3×** (std ~5–7pp) → several-point gaps are within noise.
- Main table reports **best-of-3**; reviewers want **mean ± std / CIs / paired tests / bootstrap** (iNYK Q2, Vg97 Q2).
- Specific challenged numbers:
  - "Exceeds oracle on database, 48% vs 32%" = **single Reset run**; replicated Gated-Reset averages **38.7%** (iNYK).
  - tau2 best-of-3 (60 vs 65) **masks a negative mean** (see D).

**What resolves it:** report mean ± std over ≥3 seeds on every headline cell; add paired significance / bootstrap CIs; state explicitly whether AC3's *mean* clears baseline. Scale-up (more samples per cell) directly shrinks the CIs.

---

## C. Hard-subset selection bias — Table 2 (AC-adjacent + iNYK + 5YHP)

- Table 2 "hard subset" = **20 hardest items by baseline failure rate**, and runs **replay GPT-5.2 trajectories**, not each model's own generations.
- Selection-on-trajectory + **regression to the mean** → almost any intervention looks strong. The setup measures "recovery from a fixed polluted history," not native multi-turn behavior → the **+20–42pp** headline is inflated.

**Reviewer ask (iNYK Q1):** re-report Reset vs Baseline on a **random / independently-selected subset**. If gains survive → argument holds; if they vanish → drop the generalization claim.

**What resolves it:** run on a random (unbiased) subset and report the delta honestly. This is a concrete, runnable experiment.

---

## D. tau2 overclaim — "robust across the spectrum" (all three + AC)

- Appendix B.6 per-trial: **Baseline 53.3%**, **Gated-Reset 48.3%** → ~5pp *below* baseline on the mean.
- Table 1d best-of-3 (60 vs 65) hides this.
- "Robust" currently means "did not collapse (like AO)," not "better," and it still costs ~20%/turn.

**What resolves it:** (a) soften the universal "only method robust across the spectrum" claim to the defensible version ("the only method that does not catastrophically collapse in stateful settings"); (b) report tau2 as mean ± std; (c) if scale-up/standardized tau2 now clears baseline, show it.

---

## E. Weak / missing baselines (Vg97 + AC "limited benchmarks")

- Current baselines: full context, AO, concat-user, ERGO — diagnostic but not strong.
- Wants **≥1 strong context-condensation baseline** (MT-OSC [arXiv:2604.08782]) on LiC-style benchmarks, and **≥1 context-folding baseline** (U-Fold) on tau2 — or a clear justification why they can't be adapted.
- Also **equal-compute baselines** (Vg97 Q3): repeated generation, self-reflection, strong summarizer at the same call budget; plus **latency**, not just API cost.

**What resolves it:** add at least one strong recent baseline where adaptable; add an equal-budget self-reflection/summarizer control; report latency. Where a method genuinely can't be adapted, say precisely why.

---

## F. Referential settings underdeliver — CollabLLM + soft-attention (5YHP + Vg97)

- CollabLLM: AC3-Rewrite **below AO on MATH-Hard**, **tied on BigCodeBench** → beats full-context, not blanket omission.
- BigCodeBench uses a **GPT-5 judge** instead of executable tests (simulator doesn't pass function signatures) → changes interpretation, adds judge noise.
- **Appendix D:** realistic **soft-attention** variant (must see full conversation) is substantially worse than hard-attention on math/code/database; memory only partially closes it, barely helps code. → The method's strength is exactly where the task is self-contained; the harder referential problem is unsolved.

**What resolves it:** post-NeurIPS CollabLLM re-runs (user-sim swap moved math-hard 30→95% per docs) may flip the AO comparison; if so, show the standardized numbers. Frame soft-attention honestly as a scoped limitation + partial memory mitigation.

---

## G. Replay ≠ end-to-end (iNYK + 5YHP)

- LiC uses **replay mode**: all methods share one pre-generated trajectory, only the final response is regenerated. Isolates recovery from a fixed polluted context but doesn't measure end-to-end deployment (early rewrites would change later turns, user-sim responses, state accumulation).
- Should be read as **final-turn recovery**, not end-to-end multi-turn improvement.

**What resolves it:** either (a) add a genuine end-to-end (non-replay) run on at least one benchmark to show gains persist, or (b) explicitly rescope the claim to "recovery from polluted context" and defend replay as a controlled, apples-to-apples protocol. (Full end-to-end tau2 replay was scoped at ~2 dev-days — see notes.)

---

## H. Analyzer never evaluated as a detector (5YHP W5)

- Method motivated as "identify invalidated reasoning, preserve useful work," but only downstream accuracy is measured — never **precision/recall of pollution detection**, state-preservation, or gating correctness.
- WildChat Gated-Reset edits **~72%** of turns with no false-positive / missed-pollution breakdown.
- Direct span annotations would separate genuine auditing from the analyzer simply re-solving the task.

**What resolves it:** a small annotation study (label stale vs useful vs must-preserve spans on N conversations; report analyzer precision/recall + gating accuracy). Feasible at small scale for the rebuttal or camera-ready.

---

## I. Memory mixed / under-characterized (5YHP W6 + AC "mixed results")

- Cheatsheet helps in some settings, neutral/harmful in others → can inject stale/over-general priors (analyzer-level pollution).
- Wants order-sensitivity, train/eval separation, failure-case analysis before memory is presented as generally beneficial.

**What resolves it:** present memory as an **optional, ablated** component with honest per-setting deltas; add order-sensitivity + train/eval-split checks; do not headline it.

---

## J. Presentation asks (low-cost, do regardless)

- Move the **hard-attention / structural-exclusion ablation** from appendix to main body (Vg97 — it's a highlighted strength).
- Clarity flagged by 5YHP (score 2): tighten the narrative so the scoped conclusion and the headline match.
- Fix figure/abstract language that overstates universality (ties to D).

---

## One-paragraph gestalt

The reviewers largely *like the idea* (self-contained vs. referential framing, the contagious-pollution/structural-exclusion result — all three call it compelling). They reject on **execution + overclaiming**: the method reads as per-benchmark-tuned rather than unified (A), the statistics are too thin to trust the deltas (B, C, D), the strongest baselines are missing (E), and the headline "robust across the spectrum" is contradicted by the paper's own tau2 and soft-attention/CollabLLM numbers (D, F). Crucially, the AC explicitly left the door open ("rebut if the reservations are in error"). The rebuttable core is: **(1) show one standardized method, (2) show scaled-up mean±std that keeps the deltas significant, (3) correct the unbiased-subset and tau2-mean numbers honestly, (4) add a strong baseline, and (5) rescope the universal claim.** Post-NeurIPS work (standardization, big matrix, scale-up) targets 1–3 directly.
