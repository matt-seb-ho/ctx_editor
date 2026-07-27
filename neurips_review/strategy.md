# Strategy — NeurIPS Rebuttal vs. Withdraw-for-ICLR

**Status: proceeding with the NeurIPS rebuttal** (per your instruction). This note records the honest rebut-vs-withdraw analysis so the decision is deliberate, not default. Read it, then decide whether to keep going or pivot; nothing here blocks the rebuttal draft, which is ready either way.

## The hard truth about the starting position
- **All three reviewers: 3 (Borderline reject).** Confidences 3/4/3.
- **AC meta actively leans reject** and — unusually — pre-empts the rebuttal: *"if the reservations are correct, then the concerns are too large to be dealt with in the rebuttal process and the authors are encouraged to submit the revised work elsewhere."*
- No champion. No 4+ in the pile. Quality scores are 2/2/3.

Moving this to accept in one rebuttal round is a genuine long shot. Score-raising in rebuttal usually needs at least one reviewer already at/near borderline-accept who can be converted; here the whole panel sits at borderline-reject and the AC has signalled the outcome. Realistic p(accept | strong rebuttal) is low — order of **15–25%**, and that may be generous given the AC framing.

## But the concerns are unusually addressable
This is not a case where the reviewers found a fatal flaw. They liked the idea (all three praise the framing and the structural-exclusion result). They rejected on **execution + overclaiming**, and since submission we have materially moved the exact things they named:
- Generalizability → one-analyzer/one-knob reframing + essential-vs-adaptive table.
- Statistics → LiC scaled ~6× (to n≈113–150), mean±std replaces best-of-3, WildChat tight CIs.
- Hard-subset bias → gains survive at +13–17pp on the unbiased full pool; **new** random-subset end-to-end run on gpt-5.4-mini (this session) to answer iNYK Q1 in its exact terms.
- tau2 overclaim → retired; replaced with the true multi-model AO→0% / AC3 double-digit story.
- Equal-budget (Vg97 Q3) → **new** reflection control this session.

So the delta between "the paper they reviewed" and "the paper we can describe now" is large. That is precisely the situation where a rebuttal is worth filing even if the base rate is low.

## Recommendation
**File the rebuttal, but treat its artifacts as the ICLR revision spine.** Rationale:

1. **The rebuttal is nearly free and the AC invited it.** The response is drafted; the two new experiments are running. Cost is hours, not weeks. Upside is a real (if small) shot plus authoritative reviewer signal on what still doesn't land.
2. **Withdrawing forfeits the option with no compensating benefit.** You can revise for ICLR whether or not you rebut; rebutting first gives you the reviewers' reaction to the *revised* framing, which sharpens the ICLR version.
3. **The EV-maximizing mindset is "rebut → almost certainly revise for ICLR."** Don't spend rhetorical capital pretending the submitted version was fine; spend it showing the revised version answers each concern. Every hour spent on this rebuttal is an hour spent on the ICLR paper.

**Do NOT** invest in things that only pay off if NeurIPS accepts (e.g. camera-ready-only polish). **DO** invest in things that are also the ICLR spine: unified-method section, mega-table with mean±std, the new baselines, honest scoping, the analyzer-as-detector study.

## What would change the recommendation to "withdraw now"
- If filing the rebuttal required claims we can't support honestly (it doesn't — we have the evidence).
- If the ICLR deadline were so close that rebuttal hours materially cost the ICLR submission (check the date — see below).
- If a reviewer response indicated the AC had already finalized (then stop spending on NeurIPS and shift fully to ICLR).

## Concrete ICLR-facing work items (the durable investment)
These are the rebuttal moves that are *also* the paper's next version:
1. **§ "The AC3 algorithm" unified statement** + essential-vs-adaptive table (kills the #1 concern permanently).
2. **Mega-table with mean±std + paired tests** on headline cells; move structural-exclusion ablation to main body.
3. **One strong external baseline** actually run (equal-budget reflection is done; add MT-OSC or U-Fold where adaptable).
4. **Analyzer-as-detector** precision/recall study (5YHP W5) — the one genuinely new experiment that would most raise *Quality*.
5. **End-to-end (non-replay) results** on ≥1 benchmark (the gpt-5.4-mini random-subset run is a first instance).
6. **Scope the claims** in abstract/intro/conclusion to match evidence (mostly done in the revision).

## Deadlines / logistics to confirm (not verifiable from here)
- **ICLR submission deadline** — confirm the exact date; if it's tight, front-load items 1–2 (writing) over item 4 (new experiment).
- Whether NeurIPS allows paper revision upload during the author-response period (some years yes) — if so, upload the revised PDF alongside the response.
- Coordinate with co-authors (Lianhui, Michel) before posting the rebuttal, since it commits to claims and camera-ready promises.

**Bottom line:** proceed with the NeurIPS rebuttal as planned; internally treat NeurIPS as the low-probability shot and ICLR as the real target, and make sure 100% of the rebuttal work doubles as ICLR revision work. Revisit if a reviewer reply or the ICLR calendar changes the math.
