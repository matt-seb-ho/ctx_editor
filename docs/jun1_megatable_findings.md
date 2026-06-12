# Mega-table findings: paper-text changes needed beyond the table itself

**Source data**: `docs/reports/post_may18_progress_update_v4_bandaid_tau2.html` (canonical mega-table), `docs/reports/post_may26_megatable_round_summary.md` (provenance + per-cell notes), `docs/reports/post_may18_r6_summary.md` (v8 winner declaration).

**Scope**: catalogues new insights worth promoting into the paper now that the mega-table covers 3 respondent models (GPT-5.4 / DSV4F / Kimi-K2.6) across LiC, CollabLLM, WildChat, tau2-bench. Companion to the inline table + brief discussion edits already in `writing/overleaf_repo/neurips/neurips_2026_conference.tex`.

This doc is a punch list. Each item flags whether it's a new claim to add, a contradiction to fix, or a discussion-direction shift.

---

## 1. New findings worth promoting to paper text

### 1a. "Appropriate intensity" now has multi-model legs

**What's new**: across the three tau2-bench respondents, the winning AC3 operator changes monotonically with respondent strength.

| Respondent (rough strength) | Winning operator on tau2 | Gain vs Baseline |
|---|---|---|
| GPT-5.4 (strongest) | AC3-Augment (lightest) | +15.8pp |
| DSV4F (mid) | AC3-Augment / AC3-Rewrite tied | +26.3pp |
| Kimi-K2.6 (weakest) | AC3-Rewrite (heaviest) | +47.4pp |

**Why this matters for the paper**: the original Section 3.2 ("Intervention strategies") presents Augment / Reset / Rewrite as three points on a spectrum with no empirical grounding for when each is the right choice — the paper had to recommend per-task defaults ("Reset for LiC, Gated Reset for stateful, Rewrite for open-ended") on largely qualitative grounds. The tau2 mega-table now grounds the "appropriate intensity" framing in cross-model data: stronger agents benefit from analyzer hints without destruction; weaker agents benefit from heavier interventions that aggressively prune polluted reasoning.

**Already done in paper**: new paragraph in §6 Discussion ("Appropriate intensity: one analyzer, three operators") + extension of §5.4 (Tau2-bench results).

**Further work to consider**: Section 3.2 could explicitly cite this pattern, framing the operator menu as a per-deployment knob rather than three equally-valid choices.

### 1b. The catastrophic AO collapse on tau2 generalizes across all three models (0% everywhere)

**What's new**: the AO=0% finding holds for gpt-5.4, DSV4F, and Kimi-K2.6 in the Foundry sweep — not just the original gpt-5-mini cell. This is the strongest version of the "blanket omission destroys tool-call state" claim the paper makes.

**Already done in paper**: §5.4 first paragraph now says "across every respondent we evaluated" with reference to both Tables.

### 1c. AC3-Rewrite on agentic / open-ended settings (the v8 → v11 portability story)

**What's new**: the R6-aligned Rewrite prompt (v8 on LiC, v11 on tau2 — the ports are described as a clean cross-modality success in `docs/reports/post_may18_r6_summary.md`) is the winner on:
- tau2 × Kimi-K2.6 (73.7%, +47.4pp over Baseline)
- WildChat × Kimi-K2.6 (91.5% quality vs AO)
- CollabLLM × Kimi-K2.6 × BigCodeBench (16.67%, beats Reset's NaN cell)

**Why this matters for the paper**: the current draft frames Rewrite as a forward-looking operator whose ceiling "we expect to exceed that of deterministic mapping as model capabilities improve" (§3.2). The mega-table shows Rewrite already winning on the open-ended / agentic ends of the referentiality axis with current models — the forward-looking framing understates the present-day evidence.

**Already done in paper**: new "Rewrite wins on referential generation" paragraph in §5.3 (WildChat results) + extension of §5.4 (Tau2-bench).

**Further work to consider**: tone down the "we expect" language in §3.2 to "we already see" on appropriately open-ended benchmarks.

### 1d. Gated-Reset vs Reset is asymmetric — false negatives are the dominant cost

**What's new**: on text benchmarks (LiC, CollabLLM), the analyzer's `needs_edit=True` flag fires on ≥97% of turns, so Gated-Reset ≈ Reset. The divergence happens on WildChat × gpt-5.4: always-on Reset wins 88.6% vs AO; Gated-Reset on the same 76-prefix set scores 74.1% (−14.5pp). The gate's `needs_edit=False` decisions are false negatives — the agent would have benefited from a Reset on turns the analyzer judged "on track."

**Why this matters for the paper**: §3.2 currently presents gating as orthogonal to operator choice with no caveat. The paper makes a recommendation in the Discussion to default to Gated-Reset, which is wrong on near-ceiling respondents.

**Already done in paper**: new "Gated vs.\ always-on Reset on a strong respondent" paragraph in §5.3.

**Further work to consider**: the current Discussion line "Gated Reset is consistently the best or joint-best strategy ... conservative, gated intervention as a robust default" should be qualified — it's robust for weaker respondents and tool-call settings; for strong respondents on open-ended text it leaves quality on the table.

### 1e. The single-LiC-model story is now a multi-LiC-model story

**What's new**: LiC accuracy at the benchmark-average level for our three Foundry models:
- DSV4F: Baseline 51.3 → Reset 68.4 (+17.1pp), Rewrite 64.7 (+13.4pp)
- gpt-5.4: Baseline 60.4 → Reset 77.2 (+16.8pp), Rewrite 76.6 (+16.2pp)
- Kimi-K2.6: Baseline 60.4 → Reset 74.3 (+13.9pp), Rewrite 74.8 (+14.4pp)

The current Appendix `tab:multi-model` uses different models (GPT-5, DeepSeek V3.2 (older), Qwen 3.5) on a *harder GPT-5.2-selected subset*. The mega-table provides a second cross-model robustness check using newer models on the default LiC subset — independent evidence the analyzer pipeline generalizes.

**Already done in paper**: new sentence at end of §5.1 "Generalization across model families" paragraph referencing Table 2.

---

## 2. Contradicted / softened claims in the current draft

### 2a. "Gated Reset stays within trial noise of the full-context baseline" on tau2 — too pessimistic

**Old claim** (current §5.4, original): "Gated Reset stays within trial noise of the full-context Baseline across 3 seeds. We hypothesize this is because tau2-bench's domain policy already supplies a breadth-first list of diagnostic approaches, so the agent can route around early incorrect paths without an external editor, leaving little headroom for context editing... Rather, the key finding is that selective editing does \emph{not} catastrophically collapse the way AO does."

**Why it's wrong now**: that claim was based on gpt-5-mini single-model best-of-3 trials. The mega-table shows AC3 beats Baseline by +15.8 to +47.4pp across the other three respondents. The "little headroom" hypothesis is true for gpt-5-mini but false for DSV4F and Kimi.

**Fix applied**: §5.4 now leads with the multi-model picture (AC3 substantially beats Baseline with operator-by-model winners) and keeps the gpt-5-mini single-model caveat as a "sits at the edge of the curve" sub-paragraph rather than as the headline.

### 2b. The "+10pp at +20% cost" tau2 framing in §6 Discussion was undersold

**Old claim** (current §6.1): "on tau2-bench, AO is catastrophic while editing remains within trial noise of the full-context baseline."

**Why it's misleading**: the editing-vs-baseline gap is +15.8 to +47.4pp across three respondents — substantial, not within noise.

**Fix applied**: §6.1 paragraph reworded to "AO collapses to 0\% on every respondent we tried while editing remains viable, with the Foundry sweep yielding +15.8 to +47.4pp over Baseline depending on the respondent."

### 2c. Rewrite as "forward-looking" — present-day evidence already shows wins

**Old claim** (current §3.2): "[Rewrite is the] most flexible intervention ... we expect the ceiling for learned rewriting to exceed that of deterministic mapping as model capabilities improve."

**Why it understates current data**: Rewrite already beats Reset on WildChat × Kimi (91.5 vs 71.6), tau2 × Kimi (73.7 vs 68.4), and CollabLLM × Kimi × BigCodeBench. The "as model capabilities improve" hedge is no longer needed for the present-day picture.

**Fix not yet applied**: §3.2 Rewrite paragraph hedges remain; consider softening on a future pass.

### 2d. The Abstract claim that AO collapses "from ~60% to 0%" needs to be model-specific

**Old claim** (current Abstract): "remains viable in agentic tool use where blanket omission collapses from $\sim$60\% to 0\%"

**Why it's worth refining**: 60% is the gpt-5-mini best-of-3 baseline. The Foundry sweep shows baselines of 26-68% across respondents, all collapsing to 0% under AO. The headline number is correct (AO = 0%) but the "from ~60%" implies one specific baseline.

**Fix not yet applied**: minor wording. Could become "where blanket omission collapses to 0\% regardless of respondent" if precision matters more than the lossy gap framing.

---

## 3. Discussion-direction shifts (not single-line edits)

### 3a. "Selective curation, not blanket removal" is still the headline, but the operator-per-deployment story is a new wrinkle

The conclusion currently positions AC3 as "selective curation > blanket removal." The mega-table evidence supports that, but the additional finding — that one operator is not enough; the right operator depends on respondent capability and benchmark referentiality — is itself a paper-shaped contribution that the current conclusion does not yet make.

**Suggested direction**: extend the Conclusion to land two points instead of one:
1. Selective curation (any AC3 operator) > blanket removal (AO), across referentiality.
2. Among AC3 operators, intensity should be matched to respondent capability: lighter (Augment) for strong respondents, heavier (Rewrite) for weak ones; the shared analyzer pipeline supports both.

### 3b. The analyzer is the contribution; operators are knobs

The mega-table makes this concrete in a way the original single-operator results did not. §3 ("Methods") already says "The analytical core is the contribution; operator choice is a design knob" — but that statement is currently disconnected from headline results that only varied operator within a fixed respondent. The mega-table can be cited there to back the framing.

**Suggested direction**: add a parenthetical reference to Table 2 in §3.2 first sentence ("This menu of operators trades the same analyzer artifact against different intervention intensities; the right point on that spectrum is respondent-dependent — see Table~\ref{tab:megatable}.").

### 3c. CollabLLM as a referentiality-midpoint, not a single result

Current §5.2 reads as a one-sentence "Rewrite helps on BigCodeBench." The mega-table shows CollabLLM is the most ambiguous benchmark in the suite — AO is often competitive, Rewrite is sometimes worse than Augment (DSV4F: 44.9 vs 57.5), and the bigcodebench Reset cells have content-filter infrastructure issues that prevent clean reads on 2 of 3 respondents. This is honest: CollabLLM sits midway along the referentiality axis where AO still helps but no operator dominates.

**Suggested direction**: §5.2 currently makes this point in one sentence ("AO is also competitive... CollabLLM sits midway along the referentiality axis"). Worth expanding to one paragraph that uses the mega-table's per-respondent picture to land the "no single AC3 operator dominates here" observation as part of the appropriate-intensity story, rather than as an awkward acknowledgment of mixed results.

### 3d. The current §6 Discussion does not surface the v8 prompt history

Not necessarily a paper change — the analyzer-parity bug (R5 discovery, R6 v8 prompt redesign) was deliberately kept out of the paper per the previous thread's decision. But the per-cell numbers in the mega-table reflect post-parity values throughout. Any reviewer who cross-references published Rewrite numbers from earlier reports vs. the mega-table should not see a discrepancy because we're now using post-parity values everywhere; the change is silent and contained to the underlying data pipeline.

**No action needed**, just flagging for awareness if a reviewer asks why Rewrite is ~13pp higher than older internal numbers.

---

## 4. Table layout decisions (locked in this round)

- **Two tables, not one merge**: Table 1 (per-task LiC + minor CollabLLM/WildChat/tau2 panels with single-model gpt-5-mini headline numbers) stays as-is. Table 2 (`tab:megatable`) added immediately after Table 1, showing 4-benchmark × 3-respondent averages with Augment / Reset / Rewrite rows.
- **Reset and Gated-Reset merged into one row**: per user direction, the `\method-Reset` row in Table 2 reports always-on Reset where available; cells marked `*` are Gated-Reset (used in the tau2 cells where always-on Reset was not run). The WildChat × gpt-5.4 cell is always-on Reset (88.6); the Gated-Reset on that prefix set scores 74.1 and is discussed inline (§5.3) rather than shown in the table.
- **Logos**: standardized to 200×200 px, two SVG → PDF (OpenAI, DeepSeek), one PNG (Moonshot). Files at `writing/overleaf_repo/assets/logos/`. Column headers use a small inline logo + abbreviation (`gpt-5.4`, `dsv4f`, `k2.6`) via new `\mgpt`, `\mdsv`, `\mkimi` macros.
- **Footnote markers** in Table 2 caption:
  - `*` = Gated-Reset (Reset row, tau2 cells)
  - `†` = MATH-Hard only (CollabLLM Reset cells where BigCodeBench had content-filter / endpoint issues)
  - `---` = data not gathered (WildChat Baseline/AO; we evaluate via pairwise judge against AO so a self-comparison isn't meaningful)

---

## 5. Items deferred (mentioned in the round summary; not promoted to paper)

- Tau2 Kimi Baseline + AO at workers=2 to clear rate-limit floor — would raise Baseline from 26.3 toward 40-50, but the AC3-Rewrite delta survives either way.
- WildChat × Gated-Reset for DSV4F + Kimi — would let us check whether the gpt-5.4 false-negative-rate finding is respondent-strength-specific or cross-model.
- Multi-seed on tau2 — currently N=1 per cell; the gpt-5-mini headline has best-of-3, others do not.
- CollabLLM Reset re-run with content-filter back-off — would fix the `†` cells.

None block the present paper revision; all are listed as follow-ups in `docs/reports/post_may26_megatable_round_summary.md` §6 if the camera-ready window allows.
