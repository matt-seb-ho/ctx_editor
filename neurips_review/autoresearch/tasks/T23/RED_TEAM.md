# T23 — Red team of `replies/v5/`

*2026-07-29. Adversarial read, not an accuracy audit.* The accuracy audit (T15/T19/T20/T21)
asked "is what we wrote true?" This asks "what does a reviewer who wants to reject do with
it?" Everything below is written from the chair of a reviewer who has the submitted PDF
open, a calculator, and three borderline-reject scores they would like to keep.

**Already known, not re-flagged:** (a) PAPER-7 must be applied before posting; (b) the five
`⚠ INTERNAL — HOLD` tau2 blocks are sealed pending T6. Both are at the top of `HANDOFF.md`.

**Read order.** H1–H10 are the ones that lose us the discussion period. M1–M12 are real but
survivable. L1–L5 are polish. The last section is my honest best shot at us.

---

# HIGH

## H1 — The same benchmark has three different full-context baselines across the paper and the rebuttal, 52 points apart, and nothing explains it

**Quoted text** (`00_general_response.md`, Common Weakness 5 table, L168):

> | database | Baseline (full context) | 56.1% | 60/107 | — | — |
> | code | Baseline (full context) | 83.0% | 83/100 | — | — |

**Against** (`01_reviewer_iNYK.md`, W1 table, L15–17):

> | DeepSeek-V4-Flash | 22.4 | 45.6 | **49.0** |
> | gpt-5.4 | 19.0 | 27.9 | **56.2** |
> | Kimi-K2.6 | 19.0 | 30.6 | **55.1** |

**And against the submitted paper** (`neurips_2026_conference.tex:261`, `tab:main`, GPT-5-mini):
database Baseline **4.0**, code Baseline **15.8**.

**The attack.** "Table 1 of the submission reports full-context accuracy of 4.0% on
LiC-database and 15.8% on LiC-code. The rebuttal's reply to iNYK reports 19.0–22.4% on the
same task. The rebuttal's answer to the Area Chair's baseline reservation reports **56.1%
and 83.0%** on those same two tasks. These differ by up to 52 points and the rebuttal never
says why. Either the evaluation changed — in which case the multi-turn gap the paper claims
to close is far smaller than reported and every headline number needs re-deriving — or the
three settings are not comparable, in which case the condensation baseline (the AC's central
request) was run in a regime with roughly *no* pollution damage and does not answer the
reservation. The authors should say which."

This is the worst item in the set because it is cheap to find (three tables, one document),
it lands on the AC's own reservation, and the honest answer requires disclosing that the
condensation experiment used a different respondent (gpt-5.4-mini), a different pool
(`sharded_instructions_600.json`, n=107/100 vs the paper's n=25/19) and, plausibly, a
different evaluator generation. `T1/RESULTS.md` line 3 has the protocol; the reviewer-facing
text has none of it.

**Severity: HIGH.**

**Suggested revision.** One clause per table, everywhere a new LiC number appears. In CW5,
after "we ran them on our two highest-pollution LiC tasks", add:

> (gpt-5.4-mini respondent on the full 600-instance LiC pool, n=107 database / 100 code, v2
> evaluators; absolute accuracies are therefore not comparable to Table 1's GPT-5-mini
> difficulty-matched cells — the paired Δ within each block is the quantity to read.)

And in CW2/01, state that the 3-model matrix is a different pool again. If any part of the
gap is the v2 evaluator rather than the model, **say so before a reviewer asks**, because
"our published baseline was depressed by an extraction bug" found by a reviewer is fatal and
disclosed by us is a footnote.

---

## H2 — AC3-Rewrite is silently missing from the paired-significance table, and its paired result is −0.3pp with 6 wins and 6 losses

**Quoted text** (`00_general_response.md` CW2 L75–82, repeated verbatim in `01` Q2 and `02` Q2):

> Across all **36 paired comparisons** (3 models x 4 tasks x 3 prefixes), on **raw accuracy**:
> | **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
> | **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
> | AC3-Gated-Reset | +17.0pp | 11 / 1 / 0 | 0.0063 |
> | Assistant omission (design-oracle on LiC) | +13.3pp | 31 / 4 / 1 | < 0.0001 |

The source (`neurips_review/experiments/paired_analysis_results.txt`) has a fifth row we did
not print: `Rewrite  12  −0.3pp  5.7  6/6/0  1.0000`.

**The attack.** "Common Weakness 1 says the post-submission matrix runs *the same four
operators*. The significance table lists three. The missing one is AC3-Rewrite, the operator
Reviewer 5YHP's W4 was specifically about, and by the authors' own analysis script it scores
−0.3pp on 6 wins and 6 losses. A rebuttal that claims four operators and reports the three
that win is not a statistical presentation I can rely on."

There *is* a defensible reason (per `README.md`: Rewrite's cells predate analyzer parity), but
it is nowhere in the reviewer-facing text. As `README.md` itself says: a weakness we surface
reads as rigour, the same weakness found reads as spin. This one is currently unsurfaced and
sits in a file a reviewer could plausibly be pointed at if we release the analysis.

**Severity: HIGH.**

**Suggested revision.** Add the row with its caveat, in the table:

> | AC3-Rewrite | −0.3pp | 6 / 6 / 0 | 1.00 |
>
> The Rewrite cells predate the analyzer-parity fix and cover one model (n=12); we print
> them for completeness rather than as a comparable measurement, and we do not claim Rewrite
> improves LiC accuracy. Rewrite's role is on referential settings (WildChat, CollabLLM),
> where it is our strongest operator — which is the same operator-by-regime story as the
> rest of the paper.

That converts a concealment into the paper's own thesis. Note this also *helps* H4 and the
strongest-objection section: Rewrite winning on WildChat and losing on LiC is direct
evidence that AC3 is not just AO-with-extra-steps.

---

## H3 — The recommended deployment configuration has one third of the evidence of the operator we do not recommend, and the table shows it

**Quoted text.** `00` CW2 shows `AC3-Gated-Reset | +17.0pp | 11 / 1 / 0`. 11+1+0 = **12**, in
a table headed "Across all **36** paired comparisons". Per
`paired_analysis_results.txt`, those 12 are all DeepSeek-V4-Flash. Meanwhile `00` CW5 L160
calls Gated-Reset "the configuration we recommend"; `01` L45 calls it "the deployment-relevant
configuration"; `02` L106 and `04` L51 repeat it.

**The attack.** "My W1 was that only Gated-Reset had been replicated. In the new matrix
Gated-Reset is the *least* covered arm — 12 of 36 comparisons, on a single model — and it is
still the configuration the authors recommend and the one they use to argue the corrected
ERGO number is only a tie. The recommended configuration is the least evidenced one."

Compounding: `03_reviewer_5YHP.md` L119 calls always-on Reset "our strongest operator
overall", while `00`/`01`/`02`/`04` recommend Gated-Reset, and the paper (`tex:347`)
recommends *Reset* for near-ceiling respondents and gated only where interventions carry
state-disruption cost. Three documents, three recommendations.

**Severity: HIGH.**

**Suggested revision.** (i) Footnote the 12 explicitly — "Gated-Reset was run on one
respondent (n=12 of the 36 triples); we report it separately rather than pooling" — so the
row's arithmetic is explained on the page rather than discovered. (ii) Pick one recommendation
sentence and use it in all five files. The paper's version is the defensible one and it is
operator-by-regime, which is the thesis: *always-on Reset where interventions are cheap;
Gated-Reset where an unnecessary edit carries state-disruption cost.* Stop calling
Gated-Reset "the configuration we recommend" flatly.

---

## H4 — In three separate places we answer a criticism of one operator with results for a different operator

**Instances.**

1. `03_reviewer_5YHP.md` W4. 5YHP wrote: "AC3-**Rewrite** is below AO on MATH-Hard and tied
   with AO on BigCodeBench." Our table (L65–68) is headed "**AC3**" with cells
   "**91.7 +/- 7.6** (Augment)" and "**21.7 +/- 5.8** (Reset)". Rewrite's corrected number is
   never given.
2. `01_reviewer_iNYK.md` W1. iNYK wrote: "the replicated **Gated-Reset** averages only
   38.7%." Our reply (L13–17) reports **AC3-Reset** on three models. Gated-Reset's new
   database number appears nowhere.
3. `README.md` L106 states the rule out loud: "Report **best operator per cell**, never
   'every operator beats baseline.'" The paper does the same (`tex:328`, "the best \method
   operator per cell beats Baseline in every (model, benchmark) block").

**The attack.** "I raised a specific comparison about a specific operator. The response
substitutes whichever operator wins that cell. Across the paper and the rebuttal, results are
reported as the maximum over four operators per cell with no stated selection rule and no
held-out selection — which is a per-cell oracle, and it inflates every headline. What is the
accuracy of the single configuration a user would actually deploy, chosen in advance?"

This is the most damaging *pattern* in the set, because once a reviewer names it, every
best-per-cell number in the paper is retroactively discounted, and because Vg97 Q4 is
literally "which components are essential vs task-specific" — best-of-four-per-cell is the
worst possible answer to that question.

**Severity: HIGH.**

**Suggested revision.** Two moves, both cheap.

- Give the reviewer's operator. In `03` W4 add one line: "For the operator you named:
  AC3-Rewrite on MATH-Hard is X ± Y at N=3" (from `T8`/`T21` if available; if we never ran
  Rewrite at N=3 on CollabLLM, say *that* — "we did not re-run Rewrite on this benchmark and
  therefore withdraw rather than defend the comparison you cite").
- State a **selection rule** once, in CW1: "Operator choice is not tuned per cell at
  evaluation time; the deployment rule is [X] and Table N reports that fixed rule alongside
  the per-cell best." If we cannot state a rule, then say so and report the fixed-operator
  row (Reset, which is 33/36) as primary. A single fixed operator winning 33 of 36 is a
  *stronger* claim than a per-cell maximum, and we already have it.

---

## H5 — We concede that our accuracy metric was biased in our favour, and never say which published numbers move

**Quoted text** (`04_response_to_AC.md` L48, and near-identically in `00` CW2, `02` Q2, `05` #2):

> **Our false-negative-adjusted accuracy metric is biased in our own favour** and we are
> removing it from headline reporting. ... 62% for AC3-Reset against 9% for baseline on one
> cell. ... Every number in this rebuttal is raw.

**The attack.** "The authors report that their accuracy adjustment excluded 62% of one arm's
failures and 9% of the baseline's. They say every number *in the rebuttal* is raw. They do
not say whether the numbers in the *paper* are raw. Appendix B.4 of the submission says the
procedure was 'applied to all tasks' and that flagged instances are 'excluded from accuracy
calculations'. On the natural reading, every cell of Table 1 is affected, and the paper's
headline result is unevaluated. I cannot accept a rebuttal that discloses a metric defect and
withholds its blast radius."

We *have* the answer and it is good: `tab:main`'s 20/19/25/23 denominators come from an
**arm-symmetric pool-level pre-filter** applied identically to every arm, which reproduces
those denominators exactly; the per-run metric touches at most 4 `tab:main` cells at ≤1
sample each, and 2 of those 4 favour prior work (F40–F42, D13). `README.md` L108 says in
terms: this "should be **defended, not conceded**." **No reviewer-facing sentence defends
it.** We have taken the hit and skipped the mitigation. This is simultaneously the biggest
invited-question and the biggest under-defended strength in the reply set.

**Severity: HIGH.**

**Suggested revision.** Add to `00` CW2 immediately after the concession, and compress it
into `04` item 2:

> To be precise about the blast radius, because it matters: Table 1's denominators
> (20/19/25/23) are **not** produced by this per-run metric. They come from a pool-level
> pre-filter computed once on baseline traces and applied identically to every arm before any
> method runs — an arm-symmetric filter, which we stand behind and will document. The
> per-run adjustment affects at most four cells of Table 1 by at most one sample each, and
> two of those four move in favour of prior work. What we are withdrawing is the per-run
> metric as a *reported statistic*, not the main table.

Also fix `tex:478-480`, which describes collating "all user simulator messages" when the code
collates only the visible ones — that mismatch is what makes the natural reading the bad one.

---

## H6 — The ERGO paragraph contradicts itself within four sentences, and the argument it uses disarms our own main table

**Quoted text** (`00_general_response.md` CW5 L162):

> **no ERGO-vs-AC3 difference in that table is statistically distinguishable at n ≈ 20, in
> either direction** (code p = 0.375, math p = 1.00). ... What the correction does not touch:
> ERGO remains far behind on database (12.0 against AC3-Reset's 48.0), AC3-Gated-Reset
> remains at or above ERGO on all four tasks, and **every AC3 operator still clears the
> full-context baseline in every cell.**

**The attack, part one.** "In one sentence the authors say no difference in Table 1 is
resolvable at n≈20. In the next they assert three orderings from Table 1: ERGO 'far behind'
on database, Gated-Reset 'at or above ERGO on all four tasks', and every operator clearing
baseline in every cell. They cannot have it both ways. If n≈20 cannot resolve ERGO-vs-AC3,
it cannot resolve AC3-vs-baseline either — and the entire headline of the paper is
AC3-vs-baseline in that table."

**Part two.** The last clause also breaks our own guardrail (`README.md` L106: "never 'every
operator beats baseline'"). It is true of `tab:main` as printed (which has no Rewrite row),
but a reviewer will test it against Table 2, where AC3-Reset is 47.0 vs Baseline 55.0 on
gpt-5.4/CollabLLM and Rewrite is 44.9 vs 50.0 on DSV4F — and the paper itself concedes
"some operators trail Baseline" (`tex:328`). The sentence reads globally and is false globally.

**Severity: HIGH.**

**Suggested revision.**

> ...in either direction (code p = 0.375, math p = 1.00) — and we would apply the same
> standard to our own rows in that table: at n≈20 it cannot settle any of these orderings,
> which is why our headline evidence is now the 36-comparison paired matrix at up to 150
> conversations per cell (Common Weakness 2) rather than Table 1. What the correction does
> not touch is the size of the database gap (ERGO 12.0 against AC3-Reset's 48.0, the one
> difference in that table that is larger than its own noise floor).

Delete "every AC3 operator still clears the full-context baseline in every cell" outright.

---

## H7 — "AC3 beats assistant omission in every cell" is checkably wrong about our own Table 3

**Quoted text** (`03_reviewer_5YHP.md` W1, third bullet, L35):

> Across our full per-respondent WildChat breakdown (four operators x four respondent models,
> **22 populated cells**), AC3 beats **assistant omission** in **every** cell, with per-cell
> win-rates between **72% and 92%**.

**The facts.** `tab:wildchat` (`tex:301–312`) has eight columns: `vs AO` **and** `vs FC` for
each of four respondents. Of the 22 populated cells, **13 are vs AO and 9 are vs FC**. Also,
four operators × four respondents = 16, so the parenthetical itself does not reach 22 without
the hidden second baseline dimension.

**The attack.** "The reply says AC3 beats assistant omission in all 22 cells of the
per-respondent breakdown. Nine of those 22 cells are comparisons against full context, not
against assistant omission, and 4 × 4 is 16, not 22. This is exactly the kind of arithmetic
the authors elsewhere say a reader could check with a calculator."

Note this error propagated from `T20/worklog.md:207`'s suggested wording — the audit
verified the *range* (22/22 reproduce, 71.6–91.5) but not the *description*.

**Severity: HIGH.** Checkable in 30 seconds against a table the reviewer already has, in the
reply to the reviewer most concerned about the WildChat comparison.

**Suggested revision.**

> Across our full per-respondent WildChat breakdown (Table 3: four operators × four
> respondents, against two baselines, 22 populated cells), **every populated cell favours
> AC3** — 13 against assistant omission and 9 against full context — with per-cell win-rates
> between 72% and 92%. These are single-run cells (binomial sd 4–5pp), so we quote the
> envelope as a consistency check across configurations, not as an effect range; the
> order-balanced pooled figures above are the estimate we defend.

---

## H8 — The one cell where we lose is explained away with an annotation whose traces no longer exist, drawn from the worst of three trials, to the reviewer holding the per-trial table

**Quoted text** (`00_general_response.md` CW4 L144, mirrored in `01` W3 L43):

> our own inspection of that configuration's baseline failures found that **almost all of
> them are not pollution-driven** — they are dominated by missing domain knowledge and by
> step-budget exhaustion under the hard personas, with a single case of the repetitive-loop
> behaviour our method targets.

**The attack.** "iNYK cited Appendix B.6, whose per-trial gpt-5-mini baselines are 45.0 /
55.0 / 60.0 (mean 53.3, the number in my review). The rebuttal's failure analysis counts 11
baseline failures — that is 20 − 9, i.e. the **45.0% trial**, the worst of the three, and the
table the paper reports for that cell is best-of-3. So the authors explain away the cell
where they lose using an unblinded, single-annotator reading of the single worst trial, and
the reply concedes there is no rubric. May we see the annotations?" We cannot produce them:
per T20, the 20 traces are absent from git, from `snapshot.tar.gz`, from
`supplementary.tar.gz`, and from disk, and no labels file has ever existed.

T21's softening removed the literal "1 of 11" but kept the substance and the arithmetic
signature ("a single case", "almost all"), so the reconstruction still works.

**Severity: HIGH.** Item #1 on the operator's own priority list: a claim that invites a
demand for an artifact we cannot produce, in front of the reviewer best placed to demand it.

**Suggested revision.** Cut the empirical claim to something we can stand behind and lead
with the honest limitation instead of trailing it:

> On the specific gpt-5-mini cell you cite, we should be straightforward: we do not have a
> defensible failure taxonomy for it. Our qualitative reading at the time suggested the
> baseline failures on that configuration were dominated by missing domain knowledge and
> step-budget exhaustion rather than by pollution, which would make it a low-headroom setting
> for any pollution-removal method — but that was one author's reading of one trial, without
> a rubric or a second annotator, and we would rather flag it as a hypothesis than offer it
> as evidence. For the camera-ready we will annotate all trials against a published rubric
> with a second annotator and report the taxonomy whichever way it comes out.

Conceding "we don't have this" costs us nothing here (we lose the cell either way) and buys
credibility for H5 and H6 where we do have the evidence.

---

## H9 — The sharpened claim we present as the *safe* fallback is precisely the claim T6 may falsify, and it sits outside every HOLD block

**Quoted text** (`00` CW4 L146, `01` W3 L43, `05` L33 — none inside a HOLD marker):

> we sharpen the abstract and introduction ... to the precise, checkable claim that AC3 is
> **the only method tested that improves over full context across the entire spectrum**.

**The attack.** Interim T6: DSV4F Baseline **70.2 ± 11.0** and Kimi Baseline **80.4 ± 2.5**
against published AC3 arms of 57.9 and 73.7. If those hold, AC3 does **not** improve over full
context on two of three tau2 respondents, and the sharpened claim is false on the very
benchmark it was sharpened to survive. A reviewer who later sees the corrected tau2 table —
or the camera-ready — will observe that we made the claim *more* specific and *more*
checkable at the moment we had internal evidence it was failing.

The `⚠ INTERNAL` blocks correctly quarantine the tau2 *magnitudes*. They do not quarantine
this sentence, which depends on the same magnitudes.

**Severity: HIGH** (integrity exposure, not just presentation).

**Suggested revision.** Add to the PAPER-7-blocker list in `README.md`: *the "only method
that improves over full context across the entire spectrum" sentence is tau2-dependent and
must be re-checked when T6 lands.* Pre-draft the fallback now, so it can be swapped in
without rewriting three files:

> ...the precise claim that AC3 is the only method tested that improves over full context on
> every self-contained and referential benchmark, and the only method that remains **viable**
> in the stateful agentic setting, where blanket omission fails structurally (0% on every
> respondent).

"Viable" survives any T6 outcome; "improves" does not.

---

## H10 — Vg97 asked for AC3's latency; we report the baseline's

**Quoted text** (`02_reviewer_Vg97.md` Q3, L88):

> **Latency.** At equal turn counts and equal concurrency, the **matched-budget control**
> adds roughly **13% wall-clock** over baseline (231s vs. 205s for the same 40
> conversations). Measured per-conversation on LiC-database, AC3-Reset issues 6.2 strategy
> calls and AC3-Gated-Reset 2.6, against 3.1 and 6.3 for the two summariser budgets.

**The attack.** "My Q3 asked the authors to 'report latency implications, not just API cost'
for AC3. The reply gives the wall-clock overhead of the *summarisation control*, then pivots
to call counts for AC3. AC3's own latency is still not reported — and since AC3-Reset issues
6.2 strategy calls per conversation against the 1-call summariser's 3.1, its wall-clock
overhead is plausibly larger than the 13% figure the paragraph leaves in the reader's mind.
The reply opens by saying both halves of Q3 are 'now answered with completed experiments';
one half is not."

The instrumentation exists (`outputs/T1/`, `call_meter.json`) — this is a missing number, not
a missing measurement.

**Severity: HIGH.** An explicitly requested number, from the confidence-4 reviewer, in a reply
that claims to have answered it.

**Suggested revision.** Report AC3's own wall-clock from the T1 runs, and if it is bad, say
so and lead with Gated-Reset:

> **Latency.** Measured end-to-end on LiC-database at equal concurrency: full context X s,
> AC3-Gated-Reset Y s (+a%), AC3-Reset Z s (+b%), the budget-matched summariser 231 s (+13%
> over baseline's 205 s). Per conversation, AC3-Reset issues 6.2 strategy calls and
> AC3-Gated-Reset 2.6, against 3.1 / 6.3 for the two summariser budgets. Gating is the lever
> here: it recovers +17.8pp of the +19.6pp at 0.41× the calls, and analyzer calls are
> parallelisable with respect to nothing else in the turn, so the overhead is
> latency-visible and we report it as such.

If the AC3 latency number is genuinely unavailable, say "we did not instrument wall-clock for
the AC3 arms and will report it in the camera-ready" — an admitted gap beats an apparent
substitution.

---

# MEDIUM

## M11 — "Budget-matched" is the one comparison the AC asked for, and its own robustness control is the one that did not finish

**Quoted text** (`00` CW5 L185, and `02` Q1 L39):

> A neutral-prompt variant of the summariser was implemented to check that the result does
> not hinge on our phrasing of the condenser prompt; **it did not finish in the window**, and
> both prompts will be released verbatim.

**The attack.** "The authors wrote the competitor's prompt, and the single control testing
whether they wrote it fairly is the one experiment that did not finish. Worse, their own
table shows the summariser gets *worse* when given more budget (−2.8pp at 1 call/turn,
−8.4pp at 2 calls/turn), so 'budget-matched' means 'the handicapped configuration'. This is
the reservation the meta-review listed as central, and its answer rests on a baseline the
authors built and could not verify."

**Severity: MEDIUM** (HIGH if the AC engages on it, which is likely — it is their reservation).

**Suggested revision.** Two sentences of pre-emption in CW5:

> Two honesty notes on the condenser. First, it degrades with *more* budget (−2.8 → −8.4pp),
> which is itself the mechanism prediction — a second condensation pass compresses the
> invalidated reasoning further rather than removing it — but it does mean the 2-call arm is
> not a "stronger" baseline in any useful sense, and the 1-call arm at −2.8pp (p = 0.68) is
> the fairer read: summarisation is **neutral-to-negative**, not catastrophic. Second, we
> wrote the condenser prompt, so we implemented a neutral-phrasing variant as a control; it
> did not finish in the discussion window. We release both prompts verbatim and will report
> the control regardless of outcome.

Reframing to "neutral, not catastrophic" costs us nothing (AC3 still beats it by 22–28pp
paired) and removes the appearance of stacking the deck.

## M12 — Vg97 asked for U-Fold on tau2. We neither ran it nor mentioned that we did not

Vg97's W1 is explicit: "at least one strong recent context-condensation baseline (e.g.,
MT-OSC on LiC-style benchmarks) **and one strong user-centric agent context-folding baseline
(e.g., U-Fold on tau2-bench)** — or clearly justify why they cannot be adapted." We ran the
first and are silent on the second. Our only U-Fold text (`00` CW5 L156) is the
different-failure-mode argument that Vg97 already said was "reasonable but not sufficient".

Compounding: we ran MT-OSC at w=4 and then say ourselves it "cannot compact before turn 6" on
4.1-turn conversations. The obvious follow-up — "then scale the window to the conversation
length and re-report" — has no answer, and we supplied the objection ourselves.

**Severity: MEDIUM–HIGH.** **Revision:** add one sentence to `02` Q1: "On U-Fold we did not
manage an adaptation within the window. Our reason is the same engagement argument we can now
measure for MT-OSC rather than assert, and we would run it during the discussion period if
you consider it decisive — we are asking which you would prefer given the time." Asking the
reviewer to choose converts an omission into an offer. And pre-empt the window objection:
"we also ran MT-OSC at a shortened window to check that the engagement argument, not the
hyperparameter, is doing the work" — if we have that run; if not, promise it.

## M13 — "The comparison you describe was a user-simulator artifact"

`03` W4 L63 retires a published result as a harness bug discovered after a reviewer used it
against us. The obvious follow-up — *which other results in the submission used that
simulator, and are they all being replaced?* — is not answered anywhere. **Severity: MEDIUM.**
**Revision:** add "That simulator was used only for the CollabLLM cells in Table 2; every LiC,
WildChat and tau2 result is unaffected" (verify before writing), or state the full list.

## M1 — The number of self-corrections is 3, 5, 7 and 10 depending on which file you read

`00` L32: "we correct **three** numbers ... Separately ... we found a scoring error". `04` L45:
"we want to put **five** corrections in front of the Area Chair". `05` L37: a list of
**seven**. `README.md` L45: "v5 makes **ten** [concessions]". Each count is defensible in its
own scope, but the general response — the one everyone reads first — carries the smallest
number, and the AC letter carries a bigger one. **Severity: MEDIUM** (it reads as managing the
count downward for the general audience). **Revision:** make `00`'s sentence forward-reference
the full list: "We correct three numbers reported in earlier correspondence, and a further
four found in our own re-audit; all seven are listed together in our response to the Area
Chair."

## M2 — "No per-benchmark tuning", one paragraph before two per-benchmark configuration changes

`00` CW1 L42 ("one code path with **no per-benchmark tuning**") vs L58–59 ("CollabLLM
**disables structural exclusion**", "tau2 **adds** environment-state tracking") and L63
("**rename** the tau2 variant"). A reviewer: "turning off the component you call essential,
and adding a new one, is per-benchmark configuration; renaming it does not change that."
**Severity: MEDIUM.** **Revision:** drop "no per-benchmark tuning" and say what is actually
true and stronger: "no per-benchmark *hyperparameter search and no per-benchmark prompt
tuning*; the two configuration differences are the scope condition being applied, and both
are decided by a property of the benchmark that is observable before running it (do user
turns self-specify the task? is the environment stateful?)." The *predictability* of the
switch is the defence, not its absence.

## M3 — `95.0 +/- 0.0` three times at temperature 1.0, in an experiment whose ± we have just said is understated

`00` CW3 / `01` Q1: "AC3-Gated-Reset | **95.0 +/- 0.0** | 95.0 / 95.0 / 95.0". Two attacks:
(a) three byte-identical scores at temperature 1.0 invites "were these runs cached?" — and we
have an analyzer-cache confound in our own history (F20); (b) `00` CW2 L89 concedes that
these intervals "estimate decoder variance, not sampling variance over problems, and are
correspondingly **narrower** than a full re-draw would give" — so we tell the reviewer every
± in the rebuttal understates uncertainty and then present a ±0.0. **Severity: MEDIUM.**
**Revision:** add "(38/40 in each of the three runs; the analyzer cache was disabled for
these runs, so the replicates are independent draws)" — assuming that is true; if it is not
true, we need to know before posting. And give a bootstrap CI over problems for this table:
we have item-level data, Vg97 asked for CIs, and it converts a suspicious ±0.0 into a
defensible [x, y].

## M4 — iNYK's actual argument was regression to the mean, and we never answer it — although the condensation baseline answers it perfectly

iNYK W2: "Selection on the trajectory, compounded by **regression to the mean**, will make
almost any reasonable intervention look strong on such a subset." Our reply (`01` W2)
answers with the random-subset experiment and "difficulty stratification does what it is
designed to do" — which restates the design, not a refutation.

The refutation is sitting in CW5 and we never connect it: **summarisation is a reasonable
intervention applied to the same polluted histories, and it goes down 2.8–8.4pp.** MT-OSC
moves +4.7 (n.s.). If regression to the mean made any intervention look strong, those two
arms would look strong. They do not. **Severity: MEDIUM** (under-defended strength).
**Revision:** append to `01` W2: "On the regression-to-the-mean mechanism specifically, we
now have a direct test: on the same difficulty-concentrated histories, two other good-faith
interventions — summarisation at two budgets and an MT-OSC reimplementation — score −2.8,
−8.4 and +4.7pp. If selection alone made interventions look strong, those arms would have
benefited from it too."

## M5 — "Edit precision at chance" and "preservation 4.0%" are conceded more starkly than the measurement requires

`04` item 3 L49: "AC3-**Reset**, whose edit precision on constructed pollution **sits at
chance**." `03` W5 L107: "Reset's edit precision sits at chance and its preservation rate is
4%: it removes correct injected content at essentially the same rate as false content."

Both are true. Both are also **entailed by the operator's definition** — Reset discards the
assistant side by construction, so per-span precision is not a property it was ever trying to
have, and our own delete-everything control (1.00 / 0.00) is the reference class. We have
handed the AC a quotable "at chance" without the one clause that makes it not a failure.
**Severity: MEDIUM** (over-concession, in the letter that decides). **Revision:** in `04`
item 3, keep the correction and add the frame:

> ...for AC3-**Reset**, whose per-span edit precision is at chance **by construction** — Reset
> does not attempt selective removal, it discards the assistant side and re-derives the
> specification from the user side, so span-level precision is the wrong metric for it and
> our detector study confirms that empirically. The selectivity claim belongs to
> AC3-Rewrite (removal 27.0%, preservation 38.9%). What the study *does* establish for Reset
> is that the **analyzer** detects: it names the injected pollutant in 78.6% of conversations,
> and 89.7% when the pollutant is causally harmful.

Lead with the detection number, not the precision number.

## M6 — 5YHP asked for three judge checks; we deliver two and never mention the third

5YHP W4: "No judge agreement, position-bias checks, or **human validation** reported." `03`
W4 delivers agreement and position bias in detail and is silent on human validation.
**Severity: MEDIUM.** **Revision:** one sentence — "On human validation: we did not run a
human study in the discussion window. The closest evidence we have is the degraded-copy
positive control, where three judges prefer the intact response 39/40, 36/40 and 40/40; a
human-agreement study on a sampled subset is queued for the camera-ready." Naming the gap
costs a line; being caught omitting a third of a numbered request costs the reviewer's trust.

## M7 — A bombshell about the WildChat pools is buried in a revision line

`03` W4 Revision (L87): "...and footnote the per-method sample counts, which differ because
**each method is evaluated against its own assistant-omission failure pool**." A reviewer
who parses that will ask what a "method's own assistant-omission failure pool" is and whether
the WildChat win rates are computed on method-specific, outcome-dependent pools — which is a
selection concern strictly worse than the one 5YHP raised. **Severity: MEDIUM–HIGH if
parsed.** **Revision:** either explain it in a full sentence in the body (what defines the
pool, and why it is not outcome-selected in a way that favours AC3), or, if the explanation
is long, say only "sample counts differ per method; we will footnote the exact n and the pool
construction for each cell."

## M8 — Reporting κ then substituting PABAK and Gwet's AC1 reads as statistic-shopping

`03` W4: "Cohen's kappa is 0.45–0.51, which is depressed by the ~90% marginal (the kappa
paradox), so we also report ... **PABAK 0.79–0.83 and Gwet's AC1 0.84–0.87**." The
justification is legitimate and correct. It will still read to a skeptic as "the statistic we
computed was moderate, so we computed different ones." **Severity: MEDIUM.** **Revision:**
put the raw agreement first and the alternatives as *both* reported, not as replacements:
"raw agreement 85.9–88.8%; Cohen's κ 0.45–0.51 — low relative to that agreement because both
judges favour AC3 on ~90% of pairs, the standard kappa paradox, so we report κ alongside the
prevalence-robust statistics rather than in place of them (PABAK 0.79–0.83, Gwet's AC1
0.84–0.87)."

## M9 — The replay defence answers a different objection than the one raised

`00` CW3 L113 / `03` W3 L51: "we would respectfully note that holding the polluted trajectory
fixed across methods is what makes the comparison **causal**." iNYK and 5YHP raised
**external validity** ("final-turn recovery, not end-to-end"); we answer with **internal
validity**. Both reviewers will notice, and 5YHP pre-registered the exact conclusion
("results should be read as final-turn recovery"). **Severity: MEDIUM** (tone + substance).
**Revision:** concede the label, then defend the design: "You are right that these are
final-turn recovery measurements, and we will label them that way in the paper. We keep the
design because it buys causal attribution — every method inherits an identical history — and
we supply the end-to-end evidence separately rather than claiming replay is end-to-end."
Conceding the *word* is free; we already ran the end-to-end experiment.

## M10 — Telling the Area Chair that no reviewer raised their concern

`04` L7: "we would welcome clarification if we have misread it, **since no reviewer raised an
objection framed in formal or theoretical terms**." And L11: "Testing a method past the
boundary of its own stated scope is, we would suggest, **the opposite of leaving an assumption
unexamined**."

The first reads as "your reservation has no basis in the reviews"; the second lectures.
Neither is worth the risk with the person who writes the decision. **Severity: MEDIUM.**
**Revision:** delete the "since no reviewer..." clause and open with the interpretive move
only: "Our best reading is that this refers to the scope condition for structural exclusion
(Reviewer 5YHP's W1); if the Area Chair had a different concern in mind we would be glad to
address it directly." Replace "the opposite of leaving an assumption unexamined" with
"Appendix D is our attempt to test the condition where it does not hold, and we report that
the method degrades there."

## M14 — The 78.6% naming rate has no false-alarm control

`03` W5 reports "Injected pollutant named explicitly in the analyzer's `issues`: **78.6%**"
and, two rows up, "clean-arm gate-open base rate **96.8%**". The obvious follow-up: how often
does the analyzer name a *non-injected* span as the pollutant, or name something on a clean
conversation? Naming precision is unmeasured, and we volunteer the 96.8% clean-arm open rate
in the same table, which invites exactly this question. Combined with our own disclosure that
29% (LiC) / 73% (CollabLLM) of gate-open records carry `issues: "None"`, a reviewer can build
"the analyzer fires on everything and its findings are frequently empty."
**Severity: MEDIUM.** **Revision:** if the artifact supports it, add the naming rate on the
clean control arm (from `T2A/measure.py`); if it does not, add "we did not measure naming
precision against non-injected spans; the causal factorial below is what establishes that the
removed content was the harmful content" — which is true and is the better argument anyway.

## M15 — The sign test is our weakest available statistic and Vg97 asked for CIs we do not give

The headline paired result is a **sign test over 36 (model, task, prefix) cells**, which
(a) discards effect size, (b) treats 36 correlated cells (3 prefixes of the same problems ×
3 models) as independent, and (c) is strictly weaker than the item-level exact McNemar we use
everywhere else in the same document. Vg97 Q2 asked for "confidence intervals, paired tests,
or bootstrap"; we supply only the middle one. **Severity: MEDIUM** (under-defended strength —
the result almost certainly survives). **Revision:** add a clustered bootstrap CI over
problems, e.g. "+15.9pp, 95% CI [x, y] by a task-clustered bootstrap; item-level exact
McNemar pooled across the matrix gives p = z", and keep the sign test as the assumption-light
version. We have the item-level data (it is how T1, T2c and T9 were computed).

---

# LOW

- **L1.** "**up to** 50 problems per task", "**up to** 150 per cell" (`00` CW2 L73) — iNYK
  asked for n per cell. Give the minimum too, or a per-task n row. "Up to" twice in one
  sentence reads as a ceiling being quoted as a typical value.
- **L2.** `03` W5 L115: "97.3% of LiC conversations (n=554; equivalently 98.5% of the 547
  turns...)" — fewer turns (547) than conversations (554) reads as an error even though it is
  self-consistent (539 in both numerators). Re-word: "539 of 554 conversations (97.3%); the
  analyzer ran on 547 turns and fired on 539 of them (98.5%)."
- **L3.** "1,824 judgements, **zero hard failures**" (`03` W4) — "hard" invites "what were the
  soft ones?" Say "1,824 judgements, all of which returned a parseable verdict."
- **L4.** Gratitude density. `00` opens "We sincerely thank"; `05` opens "We sincerely thank";
  `03` opens "We sincerely thank the reviewer for an exceptionally thorough review"; `01`,
  `02`, `04` all open with thanks and `02` closes with more. Trim every second one — reviewers
  read all six documents in sequence and the repetition flattens the sincerity of the places
  where we genuinely mean it (5YHP W5 deserves it; the AC letter does not need it twice).
- **L5.** `00` CW3 L109: "Its purpose is narrower and **it achieves it**." Self-congratulatory
  in a paragraph that is otherwise a model of candour. Cut four words: "Its purpose is
  narrower: it rules out the three confounds you raised, and nothing more."

---

# If I were the reviewer, the strongest single objection to this rebuttal is:

**that the rebuttal's own new measurements have quietly reduced AC3-Reset to assistant
omission with an extra LLM call, and the authors have conceded every piece of that argument
separately without ever seeing it assembled.** Here is how I would write it. The paper's
differentiating claim over Huang et al. is that AC3 "preserves what is correct and removes
what is harmful" rather than deleting the assistant side wholesale; the rebuttal withdraws
that claim for Reset and reports, from its own judge-free ground-truth study, a preservation
rate of **4.0%** against a delete-everything control that scores **0.00** — the two are
essentially indistinguishable on the axis the authors themselves say "cannot be gamed" — and
an edit precision **at chance**. The authors then describe Reset's actual mechanism as
"detect, discard the assistant side, re-derive the specification from the user side," which
is assistant omission plus a spec-extraction call. And where the two are compared head to
head on a benchmark where AO is not structurally broken, the rebuttal now declines to claim a
win: on BigCodeBench the margin narrows to +3.3pp, "inside the noise," and on MATH-Hard AC3
merely ties. That leaves exactly two places where AC3 clearly separates from AO — LiC-database
(a +2.6pp average edge over AO across the paired matrix) and tau2, where AO does not
underperform but *fails structurally* by deleting tool results, which is a misapplication of
the baseline rather than a defeat of it and which the submitted paper already reported.
Meanwhile the operator that actually *is* selective, Rewrite, is absent from the significance
table and scores −0.3pp on LiC. So: the mechanism claim is withdrawn, the head-to-head against
the prior method is withdrawn, and what remains is a small average edge over a one-line
baseline plus a well-known failure of that baseline in tool-use. That is a workshop
contribution, and the rebuttal's own honesty is what makes the case.

**How to blunt it before it is made** — and it can be blunted, because the counter-evidence
exists and is simply never assembled in one place: (1) put AC3-Reset-vs-AO as a *paired,
tested* comparison in the general response — 33/36 vs 31/36, +15.9 vs +13.3, and on database
+49.0/56.2/55.1 against AO's 45.6/27.9/30.6 on three models, which is a +21pp margin over AO
on the task where the mechanism is supposed to bite, not a 2.6pp average; (2) restore Rewrite
to the operator story (H2) so "selective editing" has a live representative, with WildChat
Kimi/Rewrite at 91.5% vs AO as its evidence; (3) reframe preservation-4.0% as *by
construction* rather than *at chance* (M5) and lead the detector section with the 78.6%
naming rate and the causal factorial (−11.1pp harmful span, +15.1pp true span, AC3 recovering
9.3% → 59.8% with the pollutant still present), which is the one result that no
delete-everything editor can produce; and (4) say plainly that the contribution is a
**decision procedure over operators indexed by referentiality**, of which AO is the correct
choice in exactly one regime — that is a claim the paper's own data supports end to end, and
it is immune to this objection because it *predicts* AO's successes rather than needing to
beat them everywhere.
