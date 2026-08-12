# Per-Reviewer Concerns → Status (Sub. 27902, AC3)
**2026-08-03.** Maps every reviewer weakness/question to its status after the **v4** posted replies, and what remains. Companion to `RESULTS_SUMMARY_2026-08-03.md` (new evidence) and `PLAN_2026-08-03.md` (response strategy).

Legend: ✅ addressed in v4 · 🟡 partial / promised-only · ❌ not addressed / open

---

## Reviewer iNYK — Rating 3, conf. 3

| # | Concern | Status | Where it stands |
|---|---|:--:|---|
| W1 / Q2 | Small N, thin replication; "exceeds oracle 48% on database" is a **single** Reset run | ✅ | Scaled ~6× to 113–150/cell; mean±std; database single-run corrected to **38.7 ± 6.1** |
| W2 / Q1 | Table 2 **hard-subset selection bias** (20 hardest by baseline failure, GPT-5.2 replay) | ✅ | Reported full-pool **+13–17pp** + a random, end-to-end, off-baseline subset |
| W3 | **"robust across the spectrum" overclaim** on tau2 (Baseline 53.3 > Gated-Reset 48.3; best-of-3 hides negative mean) | ✅ | Universal phrasing removed → "does not collapse"; tau2 now per-model |
| — | *(defect Vg97 later surfaced)* random-subset AC3-Reset was posted as **100.0 ± 0.0** | ❌ | FN-adjusted metric dropped 1/2/5 items from AC3's denominator, none from baseline's. Raw: **87.5 / 93.3 / 95.0**. Must correct. |

## Reviewer Vg97 — Rating 3, conf. 4 (the swing vote)

| # | Concern | Status | Where it stands |
|---|---|:--:|---|
| W1 / Q1 | Baselines too weak; wants **MT-OSC**, **U-Fold**, equal-budget | 🟡 → partly ✅ | v4 only *promised*. Since v4: matched-compute **condensation ✅** and **MT-OSC ✅** done. **U-Fold ❌ still not run** |
| W2 / Q2 | Statistics — CIs, paired tests, mean±std not best-of-3 | ✅ | Paired sign test, scaled N. Vg97 concedes "largely addressed" |
| W3 / Q4 | One method vs. family of task-specific variants | 🟡 | Component table given; Vg97 calls it "only partially resolved" — wants a selection *rule* |
| Q3 | Equal-budget baseline + **latency** | 🟡 | v4 gave near-ceiling-math reflection (non-discriminating) + 13% latency. Matched-budget condensation now ✅; **reflection-at-high-pollution ❌** |

## Reviewer 5YHP — Rating 3, conf. 3

| # | Concern | Status | Where it stands |
|---|---|:--:|---|
| W1 | Soft-attention gap (App. D) on deeply-referential turns | 🟡 conceded | Scoped as an open problem (inherent limitation) |
| W2 | Not a single fixed method | 🟡 | Same as Vg97 W3 |
| W3 | Small N, replay, single runs | ✅ | Scaled + paired |
| W4 | CollabLLM ≤ AO; BigCodeBench GPT-5 judge; WildChat judge checks | 🟡 | CollabLLM withdrawn as user-sim artifact; position-bias/judge-agreement partially added |
| W5 | **Analyzer never evaluated as a detector** (precision/recall, gating) | 🟡 → ✅ | v4 promised for CR. Since v4: **entire Section B** (Tier A/B + auditing-vs-solving) delivers it — and *revised* the "preserve what's correct" claim |
| W6 | Memory mixed / under-characterized | ✅ | Demoted to optional ablated add-on; contamination measured at zero |

## Area Chair PfEt — meta-review

| Pillar | Status | Where it stands |
|---|:--:|---|
| Generalizability (method changes per setting) | 🟡 | Component table + one-code-path; AC/Vg97 want a deploy-time selection rule |
| Validity of theoretical assumptions | 🟡 | Answered in `04_response_to_AC` (pollution characterized empirically, à la Laban/Huang) |
| Experimental evidence (limited benchmarks, no stats, mixed) | ✅ | Largely: scaled N, paired tests, baselines, detector eval |

---

## What is genuinely still open after v4

1. **U-Fold** — named twice by Vg97 (esp. tau2); not run.
2. **Reflection-at-high-pollution** — named by Vg97; the only reflection data is near-ceiling math (non-discriminating); a database/code arm is not run.
3. **tau2 Kimi rate-limit-clipped baseline** — improperly handled; re-measurement withdraws the tau2 claim.
4. **Random-subset 100.0 ± 0.0** — inflated by an FN-adjusted denominator; correct to 87.5/93.3/95.0.
5. **Unit-of-analysis** — sign test is over 36 aggregate conditions; item-level McNemar + clustered CIs needed.
6. **Gated-Reset = 12 comparisons** — ✅ **VERIFIED.** Not a `min_turns` subset (STATE's guess was wrong). Per `experiments/paired_analysis_results.txt`, Gated-Reset was run on **only one respondent model (DeepSeek-V4-Flash)**: 4 tasks × 3 prefixes = 12. Within that model it has the full 12 (matching Reset's +17.1pp there with +17.0pp). Honest answer = incomplete model coverage for the arm, not filtering/cherry-picking. Offer to complete the matrix for camera-ready.
7. **WildChat** — conversation-level CIs and the vs-full-context comparison not done (only vs-AO).
8. **Deploy-time selection rule** — no rule from observable conversation features for structural-exclusion on/off or operator intensity.
