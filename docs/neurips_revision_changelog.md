# NeurIPS Revision Changelog

## 2026-05-06 (round 3) — "agentic subroutine"; drop least-privilege from abstract; prior+concurrent

User feedback on round 2:
1. **"Agentic subagent" is redundant.** Use "agentic subroutine".
2. **Least-privilege does not belong in the abstract.** It was a post-hoc analogy, not a core design principle (just realized somewhat related to "minimum necessary"). The "prompting is insufficient" parenthetical also feels clunky when included twice.
3. **Compaction contrast: prefer "prior *and concurrent*" (active field); add explicit "see Section §X for further discussion"; drop the awkward "By goal... By setting" two-axis structure.**
4. **"Empirical wrinkle" sounds weird.** Find another way.
5. **Core verification vs. peripheral ablation:** asked for my preference (justified) and to make the call.

### Decisions
- **My preference on "core verification" framing: keep the subtler version.** The terms "core verification" and "peripheral ablation" are NeurIPS-reviewer shorthand — they declare importance without demonstrating it. The current Discussion opening ("The answer determines whether the analyzer is a coherent solution or itself part of the problem, so we test it directly") makes the case rather than asserting it; the subsection title ("Verifying the design: contamination is contagious") preserves Philippe's framing intent at the structural level. Keeping the subtler version in both intro and Discussion.

### Changes
- **Abstract.** "an agentic subagent routine" -> "an agentic subroutine". The least-privilege framing is dropped; replaced with: "We therefore route each subagent only the conversation slices its role requires, deliberately keeping the rest out of view." Concise and direct. The "prompt instructions are insufficient" parenthetical is also dropped from the abstract — it stays in the intro (deeper version) where it has more room to breathe.
- **Intro: compaction contrast rewritten as a single "While... we..." sentence.** New form: "While prior and concurrent agentic context-management work [refs] compacts an agent's own reasoning trajectory to support efficient long-horizon execution, we focus on multi-turn user--agent dialogue and remove pollution to improve correctness (see Section §related for further discussion)." Adds "and concurrent" and the explicit forward pointer; drops the "By goal / By setting" parallel construction.
- **Intro contagion lead.** "An empirical wrinkle further constrains the design" -> "But the analyzer is itself susceptible to the failure it diagnoses". The new opener naturally motivates the immediate follow-up sentence about a separate model also anchoring on assistant reasoning, and avoids both "non-obvious" (echoing abstract) and "empirical wrinkle" (awkward).
- **Intro least-privilege language replaced with prose.** "We therefore design the pipeline around a *least-privilege* principle: each subagent's view of the conversation is restricted to exactly what its role requires..." -> "We therefore route each subagent only the conversation slices its role requires, with the boundaries imposed by what we provide as input rather than by prompt instructions to ignore content (which alone is insufficient)." Same concept, no security-jargon framing.

Inner-repo commit: `894cf06` (on top of `f1793c0`).

---

## 2026-05-06 (round 2) — Agentic framing, least-privilege, subtler verification framing

User feedback on the prior round:

1. **"Subagent routine" or "agentic pipeline" instead of "analyzer pipeline"; do not say "short sequence of LLM calls".** The "LLM calls" gloss flattens the method to "just prompting"; reviewers will tag that. Lean on the *agentic* keyword to deflect.
2. **"We therefore tailor/restrict" still clunky.** Try a *least-privilege* (security / HIPAA "minimum necessary") frame. Convey "deliberate, designed visibility controls for individual agents in the curation routine."
3. **Bring Tyen back near Kamoi in Methods §3.2.** Useful as a second prior result motivating the external anchor.
4. **Compaction-vs-ours framing too one-axis.** Two distinctions: (a) goal: efficiency (target redundancy) vs. correctness (target pollution); (b) setting: user provides full task spec in one message vs. multi-turn user--agent dialogue with incrementally revealed intent.
5. **"Non-obvious" repeats between abstract and intro.** Stands out.
6. **Literal "we treat this as a core verification rather than a peripheral ablation" reads heavy-handed.** Convey the framing through structure and surrounding language, not via a meta-declaration sentence.

### Changes
- **Subagent terminology.** Abstract: `analyzer pipeline` -> `analyzer (an agentic subagent routine)`. Intro: `an analyzer pipeline: a short sequence of LLM calls that...` -> `an agentic analyzer pipeline that...`. Both abstract and intro now lead with the *agentic* keyword; the abstract additionally contextualizes the analyzer as a "subagent routine" (pluralizable), and the intro relies on the same idea via "pipeline." The "LLM calls" gloss is gone.
- **"We therefore tailor" -> least-privilege framing.** Abstract: "We therefore impose a *least-privilege* policy on the pipeline: each subagent sees only the conversation slices its role requires, controlled by what we route in rather than by prompt instructions to ignore content." Intro: "We therefore design the pipeline around a *least-privilege* principle: each subagent's view of the conversation is restricted to exactly what its role requires, with the boundaries imposed by what we route in rather than by prompt-level instructions to ignore content (which Section §contamination shows is insufficient)." Same idea, two surface forms, both anchored on least-privilege.
- **Tyen restored near Kamoi.** Methods §3.2 now reads: "This aligns with prior findings on intrinsic self-correction: \citet{kamoi2024criticalselfcorrect} show that LLMs cannot reliably self-correct without external feedback, and \citet{tyen2024errors} show that LLMs cannot locate their own reasoning errors but can correct them given the error location. Our user-grounded specification provides the external anchor those results identify as missing."
- **Compaction distinction expanded to two axes.** Replaced the single sentence with: "Two contrasts distinguish this from prior agentic context-management work. By goal, we target correctness through pollution removal, rather than efficiency through redundancy compaction~[refs]. By setting, we focus on multi-turn user--agent dialogue with incrementally revealed intent, rather than agentic trajectories spawned by a single user request (Section §related)."
- **"Non-obvious" decoupled.** Intro's "This design is constrained by a non-obvious finding" -> "An empirical wrinkle further constrains the design". Abstract still leads its contagion sentence with "A non-obvious finding falls out of the design"; only one occurrence now.
- **Literal "core verification" sentences dropped (subtler framing).** In intro, the closing sentence "We treat this as a core verification of the proposed design rather than a peripheral ablation" is removed entirely; the new least-privilege sentence already implies the load-bearing nature, with a forward pointer to Section §contamination. In Discussion §contamination, the opening "We treat this as a *core verification* of the proposed design rather than a peripheral ablation, because the answer determines whether the analyzer is a coherent solution or itself part of the problem" is replaced with "The answer determines whether the analyzer is a coherent solution or itself part of the problem, so we test it directly." The closing line "These results verify the central design claim:..." -> "Removing the contamination at the prompt level is therefore not enough;...". The framing now comes from the subsection title ("Verifying the design: contamination is contagious") and surrounding emphasis, not from a meta-declaration.

Inner-repo commit: `f1793c0` (on top of `0890582`).

---

## 2026-05-06 — Macros redo on top of user's pulled abstract/intro edits

Context: the prior macro commit (`6d5ff86`) was made before user pulled the previous batch into Overleaf. User then edited the abstract and intro on Overleaf and pushed. To avoid a messy merge, I reset local back to `acb9208` (dropping the macro commit), pulled the Overleaf edits (`0a55bba`, `661b66d`), and reapplied the macros — now bound to the new working method name "Agentic Conversation Context Curation" / "AC3" (placeholder for ACC).

User feedback addressed in this round:

- **Subagent terminology mismatch.** Abstract had introduced "a separate \emph{analyzer} subagent" (singular), then later said "each subagent's input" (plural). Resolved by switching the umbrella term from "analyzer subagent" to "analyzer pipeline." The pipeline is a sequence of steps; each step gets its own restricted view of the conversation. Same idea, but the noun matches the plurality of what we describe later. Applied to both abstract and intro, with intro adding "a short sequence of LLM calls" as an in-line gloss so a reader unfamiliar with "pipeline" still has a hook.
- **"We therefore tailor" repeated in abstract and intro.** Replaced with two distinct phrasings: abstract uses "we therefore restrict each step's input to just what its role calls for, removing the rest at the data layer rather than relying on prompt instructions"; intro uses "We therefore narrow each step's view of the conversation to just what its role calls for, with these visibility boundaries enforced at the input level (the rest is structurally absent) rather than via prompt instructions (which we show is insufficient)."
- **Tyen citation in intro looked orphaned.** Dropped. The same "user-grounded spec catches errors that intrinsic self-correction misses" claim is supported in Methods §3.2 via Kamoi (`kamoi2024criticalselfcorrect`).
- **Bring back compaction-vs-pollution distinction in intro (1--2 sentences).** Added one sentence at the end of the intro method paragraph: "Unlike most prior context-management work, which compacts an agent's own reasoning trajectory for efficiency [refs], we target the multi-turn user--agent dialogue itself and aim for correctness through selective removal rather than compression (Section [related])."
- **Intro reads too similarly to abstract in the latter half.** Method intro paragraph rewritten as prose (single sentence with embedded actions) rather than the (1)(2)(3) list the abstract uses. Contagion paragraph reframed to lead with "This design is constrained by a non-obvious finding..." (vs. abstract's "A non-obvious finding falls out of the design...") and expanded with the intuition that a separate model still anchors on assistant reasoning when exposed.
- **Typo fix.** "early errors about the user intent gets recorded ... biases later turns" -> "early errors about the user's intent get recorded ... bias later turns."

Inner-repo commit: `0890582`. Builds on `661b66d` (user's Overleaf push).

Items deferred to user decision (not edited):
- Abstract sentence "...may only exist in assistant turns, but referenced in later turns by the user and assistant alike" reads ungrammatical (missing auxiliary "are"). Suggesting "may only exist in assistant turns but are referenced in later turns by the user and assistant alike."
- Blanket-removal vs. AO consistency: keeping the lexical variation, since it avoids repetition while the technical referent (any approach that discards all assistant messages) is consistent.

---

## 2026-05-05 12:10 UTC — Method-name macros (`\method`, `\methodfull`)

The team considers "Agentic Context Curation" / "ACC" a placeholder name (too generic) and wants to be able to rename in one place. Defined `\methodfull` and `\method` (using `xspace`) in the preamble:

```latex
\usepackage{xspace}
\newcommand{\methodfull}{Agentic Context Curation\xspace}
\newcommand{\method}{ACC\xspace}
```

Replaced every body-text occurrence with the macros. Variant strategy names (`ACC-Augment`, `ACC-Reset`, `ACC-Gated-Reset`, `ACC-Rewrite`) become `\method-Augment`, etc.; `xspace`'s default exception list includes `-`, so the hyphen joins cleanly without needing explicit `{}`.

To rename: edit only lines 25--26 of the preamble.

Inner-repo commit: `6d5ff86`.

---

## 2026-05-05 11:35 UTC — Abstract follow-up (single paragraph, terminology fixes, em-dash sweep)

User feedback after the first abstract pass:
1. Abstract should be a single paragraph (was three).
2. "multi-turn LLM use" → "multi-turn LLM interaction".
3. "The standard mitigation discards all assistant messages" → "Previous proposed interventions discard all assistant messages" (more honest about provenance, less authoritative tone).
4. Contextualize the analyzer at first introduction — call it a "subagent" so a reader unfamiliar with the term has a hook.
5. "reconstruct the task" → "consolidate a clean, unified specification" (reflects the actual operation; aligns with how we describe Subtask 1 in the body).
6. "must structurally see only the slice of history its role requires" — too jargon-y. Find an elegant, easy-to-understand phrasing.
7. **General writing-style note (applies beyond the abstract):** stop overusing em dashes. Lately em-dash overuse reads as evidence of pure AI-generated text, which this paper is not (lots of human-in-the-loop turns).

### Changes
- Collapsed the abstract to a single paragraph.
- Applied the terminology fixes above. The analyzer is now introduced as "a separate \emph{analyzer} subagent."
- Replaced the slice-of-history sentence with: "we therefore tailor each subagent's input to its role, removing what it should not see rather than asking it to ignore what is in front of it." Same idea, plain English.
- Em-dash sweep across the prose I added/edited in the previous batch. Replaced with parens, semicolons, colons, or commas as appropriate. Touched: intro contributions paragraph (analyzer steps; structural exclusion sentence), Section 2 referential-turns paragraph (the in-line examples now in parens), Methods opener (the "user actually asked for" parenthetical), Discussion EF post-hoc subsection (the "did not start from this framing" aside), Conclusion (the "and increasingly agentic, stateful" aside), the contamination-verification subsection, and Related Work (the "self-contained, a setting LiC was designed to test" aside). Pre-existing legitimate em dashes (LaTeX comments, table cell "no value" markers, paragraph headings) left intact.
- Standing rule for future revisions: prefer parens, colons, semicolons, or commas over em dashes. Reserve `---` for tables / typographic conventions only.

### Final abstract word count: ~280 (was ~350 in pre-Michel-batch, ~290 first-pass, now ~280).

---

## 2026-05-05 10:58 UTC — Feedback from Michel (round 2) and Philippe (LiC lead author)

Inner-repo commits: `9c723f5` (main batch), plus follow-up abstract revision (commit pending).

### 1. Abstract — meta opening, drop direct LiC `\citep`, drop EF prominence, end punchier
**Why:** Michel: don't cite LiC paper directly in abstract; needs to read for both LiC-aware and unaware readers; ending on the memory-based system "reads as a secondary contribution—let's end with something punchier"; the analyzer should be evident if referenced.

**First pass (committed in `9c723f5`):** Replaced the EF-forward opening, removed `\citep{huang2026context}`, made "analyzer" explicit, replaced the memory-based ending with a "blanket-removal-vs-curation will only grow" line. Still ~290 words.

**Second pass (today, after Michel's note):** Michel flagged that the new opening ("Large language models degrade in long multi-turn conversations…") still wasn't clear about whether the failure mode was being presented as our claim or as established prior work, and asked for a more *meta* opening. Rewrote para 1 to lead with "A growing body of work has identified a systematic failure mode in multi-turn LLM use…" — establishing context pollution as a documented phenomenon before our method enters. Compressed paras 2 and 3 (~290 → ~265 words). Kept the punchier closer ("selective curation, not blanket removal, is what scales").

### 2. Intro — shorter, references Fig 1, less prior work, less EF
**Why:** Michel: methods section starts on page 4 (intro too long). Reference the hero Figure 1 in the intro contributions paragraph; don't open a sentence on a pronoun ("This is not a capability gap"); too much prior-work scaffolding; give LiC more credit for the context-pollution phenomenon (LiC says "mistakes carry forward and compound" — the inferential leap to "pollution" is small) and reserve the *naming* for Huang.

**Changes:**
- Cut the EF-driven paragraph ("In cognitive science, this regulatory capacity…") from the intro entirely. EF moved to a post-hoc Discussion subsection (item 5 below).
- Cut the "context engineering literature splits along two axes" paragraph that surveyed prior work in the intro.
- Removed the pronoun-led "The cause is not a raw capability gap" opening.
- Rewrote the contribution paragraph so it now references `Figure~\ref{fig:story}` and explicitly names AO (Huang et al.) as the prior fix being extended.
- Re-attributed: now LiC gets credit for identifying the compounding-error dynamic; Huang gets credit for *naming* it "context pollution" and for AO.

### 3. New Section 2 "Problem Setting" (Fig 2 + formulation move here)
**Why:** Michel: Figure 2 (the pollution illustration, formerly Fig 1) doesn't fit cleanly in the intro after the figure reshuffle, but is too important to drop; introduce a new Section 2 that owns the problem statement, with Fig 2 + the formal formulation + qualitative discussion. This also helps the page-budget by relieving the intro of formulation prose.

**Changes:**
- Created new `\section{Problem Setting}` between Introduction and Methods.
- Moved Figure 2 (`fig:problem`) into the new section as the section-opener.
- Moved the problem formulation block (notation; distribution-shift inequality; AO inadequacy on referential turns; editing-operator desiderata) here from `\subsection{Problem formulation}` of Methods.
- Methods section now opens directly with the analyzer pipeline, pointing back to Section 2 for the formal setup.
- All `Section~\ref{sec:problem-setting}` references continue to resolve (label moved with the content).

### 4. Terminology: stateless/stateful → self-contained/referential
**Why:** Philippe (LiC lead): "stateless/stateful" is overloaded — it means something slightly different in systems work. Suggested options: (a) referential vs. self-contained; (b) contextualized vs. decontextualized (borrowing Choi 2021); (c) entangled/disentangled; (d) coupled/decoupled. We picked (a) — Philippe's first preference, and it works for both individual utterances ("a referential turn") and conversations as a whole ("a referential conversation"). Reserved "stateful" for genuine system-state contexts (tau2-bench tool calls), where the conventional meaning still applies.

**Changes:**
- Replaced occurrences across abstract, intro, problem setting, intervention strategies, experiments roadmap, results sections, discussion, related work, and Table 1 caption.
- Added a footnote in the new Section 2 explaining the choice (and crediting Choi).
- Kept "stateful" in: tau2-bench descriptions; the "Default choice" note (Gated Reset for stateful agentic settings); conclusion (the future is "long, referential, multi-turn dialogues — and increasingly agentic, stateful settings").
- Added `choi2021decontextualization` to the bibliography.

### 5. EF moved to post-hoc Discussion subsection
**Why:** Michel: "want to be less forceful/forward of the executive function/cognitive science angle … the original idea was to unite a bunch of disparate ideas (selective attention, working memory, planning) under EF, but we really zoomed in on selective attention so the analogy is less useful framing-wise. Make EF more post-hoc (problem → solution → link to EF)."

**Changes:**
- Removed EF from the abstract (already done in item 1).
- Removed the EF paragraph from the introduction (item 2).
- Added new Discussion subsection `\subsection{Post-hoc connection to executive function}` (`sec:exec-function-discussion`). Phrasing explicitly disclaims that EF was load-bearing motivation: "We did not start from this framing — each design choice was driven directly by a specific failure mode — but the correspondence is hard to miss in retrospect."
- Trimmed the Related Work EF subsection (was a standalone block); now folded into a short pointer at the end of the agentic context-management subsection: "We discuss our (post-hoc) connection to executive function in [Discussion + Appendix]."
- Appendix `\section{Executive function as a design pattern}` retained as-is (lives at the end, post-Conclusion appendix; appropriate for design-pattern recap).

### 6. Contamination ablation reframed as "core verification"
**Why:** Philippe: "I really like the finding around contamination, it's very fun, perhaps right now it's undersold as an ablation. This is really a core verification of the proposed method and not really an ablation."

**Changes:**
- Renamed Discussion subsection from `Conversation analysis ablations` → `Verifying the design: contamination is contagious`.
- Rewrote the introductory paragraph to position this as the core verification of whether structural exclusion is load-bearing or stylistic: "We treat this as a *core verification* of the proposed design rather than a peripheral ablation, because the answer determines whether the analyzer is a coherent solution or itself part of the problem."
- Updated the closing line to "These results verify the central design claim…" instead of the previous "These results suggest that any multi-stage LLM pipeline…"
- Also added a corresponding pointer in the introduction's contagion paragraph: "We position this as a core verification of the proposed design rather than a peripheral ablation."

### 7. Figure 1 caption compressed
**Why:** Michel: keep Figure 1 as the hero figure (it's "the overall arc of the paper — fine grained management is robust to increasing statefulness"), but compress the caption — currently it (plus Fig 2) takes too much vertical space and is part of why the methods section starts on page 4.

**Changes:** Caption rewritten more tersely. Removed the "schematic; curves illustrate qualitative trends" parenthetical, dropped the per-benchmark sentence-by-sentence walkthrough, kept the AO/ACC/full-context contrast in compressed form.

### 8. Tau2-bench sub-table margin fix
**Why:** The (d) sub-table for tau2-bench was overflowing the right margin (NeurIPS doesn't allow this).

**Changes:** Dropped the `Cost` column from sub-table (d). Numbers are now reported in the prose: tau2-bench Results section now reads "Gated Reset achieves 55--65% vs. the 45--55% baseline, at a per-task cost of $0.60--0.67 vs. $0.51 for the baseline (AO is the cheapest at $0.36, but its 0% success rate makes the comparison moot)." Caption updated to point readers to the prose for cost numbers.

### Items NOT addressed in this batch (deferred / out of scope for NeurIPS deadline)

- **Philippe: WildChat referentiality statistics.** He proposed running an LLM-based classifier over a WildChat subset to report "in practice, XX% of real-world Human-AI conversations have at least 1 referential user utterance." Skipped due to time. Huang et al. already classify turns into `new_ask`/`feedback`/`no_feedback` and we report those distributions in App. WildChat — that's a partial proxy.
- **Philippe: precompute rollouts.** He noted our setup tests "recovery" more than "prevention" — would prefer per-turn analysis to demonstrate prevention. We acknowledge this in the Limitations appendix already; full prevention experiments are post-NeurIPS work.
- **Philippe: 4-dataset critique → single controlled "vary referentialness" benchmark.** Explicitly future work for the summer (Philippe co-managing the intern); not for this submission.
- **Philippe-suggested experiments on per-turn analysis** (run with method for first K turns, then without). Out of scope for the deadline.

---

## 2026-04-20 — Feedback from Lianhui (17 Apr) and Michel (19 Apr)

---

### 1. Title: Remove "EF," rename approach

**Before:** `Curing Context Pollution: Externalized Executive Function for Multi-Turn LLM Conversations`  
**After:** `Agentic Context Curation for Multi-Turn LLM Conversations`

**Why:** Lianhui and Michel both asked to remove EF from the title. Michel wants the title to emphasize (1) solving a multi-turn problem and (2) agentic intervention—not a training method. The new title names the approach (Agentic Context Curation) and the setting (multi-turn LLM conversations). Michel also suggested drawing on the "LLMs managing their own context" framing; "Agentic Context Curation" captures that without too directly referencing the MSR paper.

**Alternative titles considered (for discussion with advisors):**
- `Staying on Track: Agentic Context Curation for Multi-Turn LLM Conversations` — more catchy, emphasizes navigation metaphor Michel mentioned
- `Agentic Context Curation: Helping LLMs Navigate Multi-Turn Conversations` — clearer but longer
- `Clearing the Context: Agentic Curation for Multi-Turn LLM Interactions` — avoids "pollution" in title per Michel

---

### 2. Abstract: Soften EF from "we frame this as" to "inspired by"

**Before:** "We frame this as a deficit of \emph{executive function}: the higher-order cognitive capacity..."  
**After:** "Inspired by \emph{executive function}---the higher-order cognitive capacity...---we propose a training-free, inference-time context curation method..."

**Why:** Lianhui's instruction: "ok to keep 'inspired by EF' in the abstract." The old phrasing made EF the central theoretical frame; the new phrasing positions EF as design inspiration while keeping the proposed method as the subject of the sentence.

---

### 3. Intro para 2: Remove student analogy, reduce EF weight

**Removed:** "A student who realizes one lemma in their proof is wrong can scratch out that lemma while keeping the rest; an LLM that has generated three turns of reasoning---some correct, some not---cannot selectively discard the flawed parts..."

**Why:** Lianhui explicitly asked to remove the student analogy.

**EF framing reduced:** Changed `\textbf{executive function}` to `\emph{executive function}` and replaced the extended EF explanation with a single sentence describing the LLM's parallel deficit. The detailed EF justification now lives in the Related Work section (moved—see below).

---

### 4. Method name: "Agentic Context Curation (ACC)"

**Changed throughout:** `context curation via externalized executive function` → `Agentic Context Curation (ACC)`

**Locations updated:**
- Intro para 4 (method proposal sentence)
- Figure 2 caption
- Algorithm 1 caption
- Conclusion opening sentence

**Why:** Lianhui asked to give the method an actual name. Michel wants to emphasize agentic intervention. "ACC" is memorable and describes what the method does without requiring the EF framing.

---

### 5. Self-correction localization citation (Tyen et al. 2024)

**Added citation in intro para 4:**  
"...then identifies *where* the assistant's work diverges from that specification~\citep{tyen2024errors}..."

**Paper:** Tyen, Mansoor, Carbune, Chen, Mak. "LLMs cannot find reasoning errors, but can correct them given the error location." *Findings of ACL 2024.*

**Why:** Lianhui noted that research shows pointing out *where* the problem is is as important as how to fix it. This is exactly what Tyen et al. demonstrate: LLMs can correct errors when given error location but cannot find the location themselves. Our method's core contribution is the structured pipeline that identifies *where* the context is polluted—this citation directly supports that framing.

**Also note:** This citation is a natural complement to `kamoi2024criticalselfcorrect` already in the methods section (line ~153), which shows intrinsic self-correction fails without external feedback. Tyen et al. adds the positive result: given location, correction succeeds.

---

### 6. Related Work: Moved from before Methods to after Discussion

**Before:** Related Work appeared immediately after the Introduction (standard position).  
**After:** Related Work appears between Discussion and Conclusion.

**Why:** Lianhui: "abstract + intro + related work means reader doesn't get to our method until several pages in." Moving it after Discussion lets the reader reach Methods immediately after the intro, reducing time-to-method. This is an increasingly common structure at NeurIPS/ICML for methods-heavy papers.

**Note on references:** `\label{sec:related}` is preserved. No cross-references to `\ref{sec:related}` were found in the main text, so this move is safe. Internal section cross-references (e.g., `Section~\ref{sec:decomposition}`) within the Related Work block are unaffected since those sections still exist.

---

### 7. Related Work: Trim U-Fold/MemoBrain paragraph

**Before:** ~100-word paragraph covering U-Fold and MemoBrain in detail.  
**After:** ~50-word summary, pointing to Appendix~\ref{app:agentic-context} for full comparison.

**Why:** The appendix already has a detailed comparison. This trims ~50 words from the main text to help with page budget. Combined with the student-analogy removal (~35 words) and minor intro tightening, this moves the paper toward the 9-page limit.

---

### 8. Related Work: Trim EF paragraph slightly

Removed "not merely as an analogy but as" from the EF paragraph (now in Related Work after Discussion). The connection is stated functionally without the meta-commentary about whether it's "merely an analogy."

---

## Outstanding items

- **Title final decision**: Three alternatives listed above—please confirm preferred title with advisors (especially in light of the upcoming LiC news Michel mentioned).
- **Tyen et al. citation placement**: Currently in intro para 4. Could also be strengthened by adding it to the methods section (Section 3.2, near `kamoi2024criticalselfcorrect`). Recommend adding once title/framing is settled.
- **New figure 1** (statefulness vs. performance): Lianhui requested a new Figure 1 that relates statefulness to performance to show where the method applies. Not addressed here—this is a data/visualization task.
- **Figure 2 redesign** (pollution illustration): Suggestion—use different background colors or fonts to distinguish the conversation turns from the analysis layer, making the pollution vs. curation contrast more visually obvious. Not edited in .tex since this is an asset change.
- **New experiment: reasoning effort vs. context pollution**: Michel/Lianhui suggest exploring how different reasoning effort levels relate to context pollution. Not addressed here.
- **Page count**: Student analogy removal (~35 words) + U-Fold/MemoBrain trim (~50 words) + minor EF tightening (~20 words) = ~105 words removed. At NeurIPS column width, ~100 words ≈ 0.3–0.4 pages. Should help move from 9.3 toward 9 pages, but compile and measure to confirm.
