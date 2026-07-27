# Triage — AC3 NeurIPS Rebuttal (Sub. 27902)

Each problem (labels from `01_problem_summary.md`) scored on three axes:

- **Severity** — how much it drives the reject decision (the AC's three pillars weigh most). High / Med / Low.
- **Addressability in the rebuttal window** — can we move it now? **Data** (already have evidence in post-NeurIPS docs) · **Cheap-exp** (small gpt-5.4-mini run, feasible now) · **Reframe** (writing/claim change, no experiment) · **Hard** (needs work beyond the window → concede + roadmap).
- **Effort** — S / M / L.

Priority tiers below sort by (severity × addressability): fix the high-severity, movable ones first.

---

## Tier 1 — Decisive AND movable (win the rebuttal here)

| ID | Problem | Sev | Addressability | Effort | Rebuttal move |
|---|---|:--:|---|:--:|---|
| **A** | Method not unified across settings | **High** | Reframe + Data | M | State ONE algorithm; frame per-benchmark knobs as *settings of one parameter* (how much assistant history is referential/stateful), derived not hand-tuned. Add a "what's essential vs. adaptive" table. Use standardized post-NeurIPS runs as proof the same pipeline runs everywhere. |
| **B** | Statistics: best-of-3, no CIs, tiny N | **High** | Data + Cheap-exp | M | Replace best-of-3 with **mean ± std over ≥3 seeds** on every headline cell; add paired test / bootstrap CI. Scale-up shrinks CIs. Report from the big matrix. Fill any missing seeds with gpt-5.4-mini. |
| **C** | Table 2 hard-subset selection bias | **High** | Cheap-exp | S | Run Reset vs Baseline on a **random subset** (iNYK Q1). Report honestly. This is a direct, cheap, credibility-restoring experiment. |
| **D** | tau2 "robust across spectrum" overclaim | **High** | Reframe + Data | S | Soften universal claim → "only method that does not *collapse* in stateful tool use." Report tau2 **mean ± std**. If standardized/scaled tau2 now clears baseline, lead with it; if not, own it. |

**Tier 1 is the rebuttal's spine.** These are exactly the AC's three pillars (A=generalizability, B/C/D=evidence) and all are movable now.

---

## Tier 2 — Important, partially movable

| ID | Problem | Sev | Addressability | Effort | Rebuttal move |
|---|---|:--:|---|:--:|---|
| **E** | Missing strong baselines (MT-OSC, U-Fold, equal-budget) | **Med-High** | Cheap-exp + Reframe | M–L | Add an **equal-compute self-reflection / summarizer** baseline (cheap, directly answers Vg97 Q3) + latency numbers. For MT-OSC/U-Fold: adapt at least one where feasible; where not, give a precise adaptation-barrier justification. Don't leave it at "they're different." |
| **F** | CollabLLM ≤ AO; BigCodeBench judge | **Med** | Data + Reframe | M | Show post-NeurIPS CollabLLM re-runs (user-sim swap: math-hard 30→95%). If standardized numbers now beat AO, present them. Defend the GPT-5 judge (report agreement if available) or note execution-harness limitation honestly. |
| **G** | Replay ≠ end-to-end | **Med** | Reframe (+ optional exp) | S–L | Rescope claim to "final-turn recovery from polluted context" as the *controlled* protocol, and argue why replay is the fair apples-to-apples design. Optionally add one end-to-end run as proof-of-persistence (full tau2 end-to-end = ~2 dev-days, defer). |

---

## Tier 3 — Real but conceddable / camera-ready

| ID | Problem | Sev | Addressability | Effort | Rebuttal move |
|---|---|:--:|---|:--:|---|
| **H** | Analyzer never evaluated as a detector (precision/recall) | **Med** | Cheap-exp | M | Offer a small **span-annotation study** (precision/recall of pollution detection + gating accuracy on N conversations). Feasible small-scale now or commit for camera-ready with a pilot in the rebuttal. |
| **I** | Memory mixed / under-characterized | **Low-Med** | Reframe | S | Demote memory to an **optional ablated add-on** with honest per-setting deltas; add order-sensitivity + train/eval-split note. Do not headline it. |
| **F′** | Soft-attention gap (Appendix D) | **Med** | Reframe | S | Concede as a **scoped limitation**: structural exclusion is provably best where user turns self-specify; soft-attention + memory is the partial answer for deeply referential turns; name it as future work. Honesty here buys credibility for Tier 1. |

---

## Tier 4 — Presentation (do regardless, near-zero cost)

| ID | Problem | Sev | Effort | Move |
|---|---|:--:|:--:|---|
| **J1** | Move structural-exclusion ablation to main body | Low | S | Do it — a reviewer explicitly requested it and calls it a strength. |
| **J2** | Clarity (5YHP scored 2) | Low | S | Tighten narrative so scoped conclusion matches headline. |
| **J3** | Abstract/Fig 1 universal-language fix | Low | S | Align wording with D. |

---

## New experiments to run (gpt-5.4-mini via TRAPI) — ranked

Only run what changes a Tier-1/2 verdict. Ranked by rebuttal ROI:

1. **[C] Random-subset Reset vs Baseline** (LiC, ≥1 task, ideally all four). Directly answers iNYK Q1. *Highest ROI — small, decisive.*
2. **[B] Fill missing seeds** to give mean ± std on every headline LiC cell (esp. the database 48%-vs-oracle cell → replace single-run with N≥3). Directly answers iNYK Q2 / Vg97 Q2.
3. **[E] Equal-budget self-reflection / summarizer baseline** at matched call count + latency logging. Answers Vg97 Q3.
4. **[D] tau2 mean ± std** at scaled N (confirm above/below baseline honestly).
5. **[H] pilot** span-annotation precision/recall (optional, small).

> Gate each run on the evidence-digest result: if the big matrix + scale-up docs already contain the numbers (mean±std, random subset, standardized pipeline), cite them and **skip re-running**. Only spend gpt-5.4-mini calls on genuinely missing cells.

---

## Decision-theoretic read

The AC explicitly invited rebuttal "if the reservations have been made in error." Two of the three pillars are **evidence quality** (B/C/D), which scale-up + honest mean±std can *materially* move within the window. The third (generalizability, A) is **reframing + already-collected standardization data**, not new science. So the rebuttable path is real — but it hinges on (1) landing the unified-method story credibly and (2) not overclaiming again. The fastest way to lose is to defend the "robust across the spectrum" line verbatim; the fastest way to win is to concede D/F′/G honestly while converting A/B/C into hard, scaled numbers.
