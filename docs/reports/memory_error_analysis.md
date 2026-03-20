# Memory Error Analysis: S1 vs S1+mem vs S1.5 vs S1.5+mem

**Date**: 2026-03-17
**Branch**: `newleaf2`
**Scope**: Sample-level analysis of memory's effect on S1 and S1.5 across math, code, and database tasks (v8 batch, dev set, compare-targeted memory).

## Summary

Memory (cheatsheet injected into Query 2) uniformly improves S1 (+2 math, +3 code, +3 database, 0 regressions across all tasks). S1.5 does not share this property — memory causes 4 regressions on database, offsetting its 3 new solves (net -1). The root cause is **structural**: in S1 the analysis is supplementary (full conversation visible), so flaws in memory-influenced analysis are harmless. In S1.5 the analysis IS the entire context, so even minor over-specification becomes catastrophic.

## Results Reference

| Config | Math (n=20) | Code (n≈19) | Database (n=25) |
|--------|:-----------:|:-----------:|:---------------:|
| S1 | 16/20 (80%) | 10/18 (56%) | 8/25 (32%) |
| S1+mem | 18/20 (90%) | 13/19 (68%) | 11/25 (44%) |
| S1.5 | 16/20 (80%) | 11/16 (69%) | 10/25 (40%) |
| S1.5+mem | 17/20 (85%) | 12/17 (71%) | 9/25 (36%) |

---

## Per-Task Analysis

### Math: +2 new solves, 0 regressions (S1 → S1+mem)

**Flip table:**

| Category | Count | Samples |
|----------|-------|---------|
| New solves | 2 | GSM8K/1190, GSM8K/144 |
| Regressions | 0 | — |
| Stable correct | 16 | — |
| Stable wrong | 5 | GSM8K/1287, 267, 534, 315, 427 |

S1.5 → S1.5+mem: +1 new solve (GSM8K/1190), 0 regressions.

#### New Solve: GSM8K/1190 (bandage inventory)

**S1 (wrong, answer: 50):** The analyzer produced a verbose user_intent (2893 chars) with extensive ambiguity discussion. The issues correctly flagged the premature "ANSWER: 50" but also noted "no actual solved numeric S provided." The assistant hedged between two interpretations (Case A = 19, Case B = 69) without committing. Extractor picked up the stale 50.

**S1+mem (correct, answer: 19):** The user_intent was much more concise (1678 chars) and critically included: *"If any given fact is ambiguous... explicitly state the assumption you adopt before proceeding with the calculation. Preferably choose the natural interpretation that allows solving the problem."* The assistant committed to one interpretation ("'ordered' = 'received' on that day") and produced ANSWER: 19.

**Mechanism:** Memory principle III (Disambiguation) told the analyzer to prescribe a deterministic disambiguation rule instead of inviting exploration of all interpretations. This shortened the spec and forced a commitment.

#### New Solve: GSM8K/144 (Kim's housekeeping profit)

**S1 (wrong, answer: 664):** The user_intent was 4438 chars and demanded both interpretations be computed: (A) 92 = total weekly income, (B) 92 = per-client income. The assistant produced multiple ANSWER lines; extractor picked up 664 (interpretation B).

**S1+mem (correct, answer: 20):** The user_intent was 1907 chars and committed to a single reading: *"Weekly income: 92 (Kim is making $92 per week from his work)"* with an explicit 5-step computation procedure. The assistant followed the steps: 8 clients, expense=72, profit=92-72=20.

**Mechanism:** Memory's "canonical task spec" and "one final answer" formatting principles caused the analyzer to NOT bifurcate into multiple interpretations. The spec became a recipe instead of a debate.

#### Why S1.5+mem did NOT flip GSM8K/144

S1.5+mem still hedged between interpretations, producing a fractional answer (520/3). The S1.5 strategy strips the full conversation, so the compacted context inherits whatever the analysis says — and the analysis for this sample still included interpretation branching. The memory effect on this sample was apparently not strong enough to overcome the analyzer's uncertainty when the full conversation was absent.

#### Stable wrong samples

5 samples stayed wrong across S1 and S1+mem: GSM8K/1287, 267, 534 (assistant never produced an ANSWER line in any condition), 315 and 427 (same wrong answer in both). These represent problems where the baseline conversation was too broken for the analyzer to recover, regardless of memory.

---

### Code: +3 new solves, 0 regressions (S1 → S1+mem)

**Flip table:**

| Category | Count | Samples |
|----------|-------|---------|
| New solves | 3 | livecodebench/2812*, 2881, 2979 |
| Regressions | 0 | — |
| Stable correct | 10 | — |
| Stable wrong | 6 | — |

*2812 was a timeout artifact (S1 timed out, S1+mem didn't). Two genuine flips below.

S1.5 → S1.5+mem: 0 new solves, 0 regressions. Memory had zero effect on S1.5 for code.

#### New Solve: livecodebench/2881 (string splitting)

**S1 (wrong):** Analysis flagged "function signature and return format mismatch" but the corrected answer still included `allowed = {'.', '|', '$', '#', '@'}` — **missing comma `,`** from the allowed separator set. This caused a ValueError when tested with `,` as separator.

**S1+mem (correct):** Analysis flagged the same issue but with a **concrete failing example**: `Input: strings=["a.b","c.d"], sep='.'  Expected: ["a","b","c","d"]`. The corrected answer omitted unnecessary validation entirely, trusting user-provided constraints. Simple, correct function.

**Mechanism:** Cheatsheet rules "Do not invent stricter runtime validations for guarantees the user already provided" and "For each FAIL supply a single concrete failing test-case" guided the analyzer to (a) flag unnecessary validation and (b) include concrete examples that made the correction unambiguous.

#### New Solve: livecodebench/2979 (house offers / max gold)

**S1 (wrong):** Analysis identified the **wrong problem** in its user_intent: "The buyer will accept any **single house** whose index is in the inclusive range." Focused on interface mismatches (wrong function names, wrong return types) but completely missed the core semantic error — the assistant solved bipartite matching instead of weighted interval scheduling.

**S1+mem (correct):** Analysis correctly identified the problem as **weighted interval scheduling** ("no two selected offers may overlap in any house index"). First issue: "Core semantic mistake: almost all offered implementations solve a different problem." Included a concrete failing example proving the algorithms give different answers.

**Mechanism:** Cheatsheet rules "Algorithmic/semantic correctness relative to examples" and "Also escalate when there is a core semantic misinterpretation (assistant solved a different problem)" directly prompted the analyzer to check algorithm semantics, not just interface compliance.

#### Batch placement

Both genuine flips (2881, 2979) were in Batch 4 — the final batch. The cheatsheet had been trained on 15 prior samples before seeing them. The rules that drove the flips (concrete test cases, semantic verification, unnecessary validation) were learned from earlier failures.

---

### Database: +3 new solves, 0 regressions (S1 → S1+mem)

**Flip table:**

| Category | Count | Samples |
|----------|-------|---------|
| New solves | 3 | spider-val-498, val-555, val-75 |
| Regressions | 0 | — |
| Stable correct | 8 | — |
| Stable wrong | 14 | — |

S1.5 → S1.5+mem: +3 new solves (val-457, val-75, val-946), **4 regressions** (val-389, val-401, val-498, val-932). Net -1.

#### New Solve: spider-val-498 (battles with lost Brig ships)

**S1 (wrong):** Produced `SELECT b.id AS battle_id, b.name AS battle_name` — aliased columns that the evaluator rejected.

**S1+mem (correct):** Analysis explicitly flagged: "the task spec explicitly listed the required columns as battle.id and battle.name (no aliasing was requested)." Produced `SELECT DISTINCT b.id, b.name` — exact column names.

**Mechanism:** Cheatsheet rule "Capture exact-match constraints (exact column names, exact aliases) as hard requirements."

#### New Solve: spider-val-555 (first registered student)

**S1 (wrong):** Produced `WHERE date_first_registered = (SELECT MIN(...))` — returns all tied rows, evaluator expected a single row.

**S1+mem (correct):** Analysis explicitly called out: "The queries return all students who share the earliest date... No tie-breaking or LIMIT 1 was applied." Produced `ORDER BY date_first_registered ASC, student_id ASC LIMIT 1`.

**Mechanism:** Cheatsheet rule "For singular wording that implies a single row, prefer single-row semantics (deterministic tie-breaking via ordering+limit)."

#### New Solve: spider-val-75 (students who have pets)

**S1 (wrong):** The assistant **never produced a SQL query at all** — kept asking clarifying questions across 4 turns. The S1 analysis noted "No contradictions or incorrect assumptions were made" — too lenient.

**S1+mem (correct):** Analysis flagged: "The assistant has not yet produced the final SQL query requested by the user." Produced the correct JOIN query.

**Mechanism:** Cheatsheet rule "Do not recommend asking the user for clarification when the environment forbids it" and "If the assistant asked clarifying questions in a no-clarification environment, mark them as wasted turns."

---

## S1.5 Database Regressions: Detailed Analysis

These 4 regressions are the core finding — they explain why memory's benefits don't transfer cleanly from S1 to S1.5.

### Regression 1: spider-val-389 (teachers with Age 32 or 33)

**S1.5 (correct):** Clean spec: "Age filter: include teachers whose Age is 33 or 32. Note: Age is stored as TEXT... use TEXT values '33' and '32'." Issues correctly identify numeric CAST/GLOB as wrong. Assistant produced `SELECT Name FROM teacher WHERE Age IN ('33', '32');` ✓

**S1.5+mem (wrong):** Spec included: *"If anything above is unclear (for example, whether Age is numeric vs text in the actual data, or whether duplicates should be removed), ask the user before producing the final query."* Issues included: "The assistant did not ask about whether duplicate names should be removed." The assistant asked a clarifying question instead of producing SQL. ✗

**Failure mode:** Memory-influenced analysis invited clarification-seeking despite the cheatsheet saying "apply deterministic defaults." The compacted context inherited the invitation, and the assistant followed it literally.

### Regression 2: spider-val-401 (teacher names + courses)

**S1.5 (correct):** Spec stated clear defaults about join semantics. Assistant produced the correct JOIN query. ✓

**S1.5+mem (wrong):** Spec listed two "Open questions / clarifications needed from the user (do not assume answers)." The assistant asked those questions instead of producing SQL. ✗

**Failure mode:** Same as val-389 — analysis invited clarification, assistant followed literally in the absence of any other context.

### Regression 3: spider-val-498 (battles with lost Brig ships)

**S1.5 (correct):** Clean JOIN approach: `SELECT DISTINCT b.id, b.name FROM battle b JOIN ship s ON s.lost_in_battle = b.id WHERE s.ship_type = 'Brig';` ✓

**S1.5+mem (wrong):** Memory-influenced analysis was more prescriptive about what NOT to do (no aliases, no aggregation), pushing the assistant toward `WHERE EXISTS(SELECT 1 FROM ship ...)`. Semantically equivalent but evaluator rejected it. ✗

**Failure mode:** Over-prescriptive guidance steered toward an alternative SQL form that the execution-based evaluator penalized. Ironic: this is the same sample that S1+mem FIXED (by removing aliases), but S1.5+mem BROKE (by changing the query structure).

### Regression 4: spider-val-932 (professionals with 2+ treatments)

**S1.5 (correct):** Spec requested 3 columns: "professional_id, first_name, role (use role_code)." Assistant produced those 3 columns. ✓

**S1.5+mem (wrong):** Spec requested 4 columns: "professional_id, first_name, role_code, treatment_count." Issues flagged alias mismatch for `treatment_count`. The user never asked for a count column — the "2+ treatments" was a filter (HAVING), not a projection. Assistant produced 4 columns including COUNT. ✗

**Failure mode:** Memory-influenced analysis **hallucinated a column requirement** (`treatment_count`). In S1, the assistant could cross-reference the actual user messages and ignore the hallucinated column. In S1.5, the user_intent IS the user's voice — the assistant trusted it completely.

---

## Structural Root Cause: Why Memory Helps S1 But Hurts S1.5

| Property | S1 (append) | S1.5 (reset) |
|----------|-------------|--------------|
| Full conversation visible? | Yes | No |
| Analysis role | Supplementary hint | Sole context |
| Effect of analysis flaws | Diluted by original messages | Amplified — no safety net |
| Memory benefit | Better structure, better issue detection | Same potential |
| Memory cost | Occasional over-specification (harmless) | Over-specification becomes the truth |

**In S1**, the assistant sees: full conversation + analysis. The analysis is a "second opinion" — the assistant can weigh it against the actual user messages. When memory makes the analysis slightly overspecified (adds a column requirement, invites clarification), the assistant can override it by looking at what the user actually said.

**In S1.5**, the assistant sees: compacted context only (task spec + aligned + issues + last user message). The analysis IS the user's intent — there are no original messages to cross-reference. Every flaw in the analysis is trusted at face value.

### Three specific anti-patterns in memory-influenced analysis that are harmless in S1 but catastrophic in S1.5:

1. **Clarification-seeking leakage** (val-389, val-401): Despite the cheatsheet prescribing "deterministic defaults," the analyzer sometimes writes "ask the user before producing the final query." In S1, the assistant ignores this because it can see the user's actual messages. In S1.5, the assistant follows the instruction literally and asks questions.

2. **Hallucinated requirements** (val-932): The analyzer adds column requirements the user didn't request. In S1, the assistant can check the actual messages and omit the extra column. In S1.5, it trusts the spec completely and adds the column.

3. **Over-prescriptive "don't" rules** (val-498): The analyzer over-constrains the SQL form (no aliases, no aggregation). In S1, the assistant picks whatever form it naturally would. In S1.5, the prescriptive rules steer toward an alternative form that happens to be evaluated differently.

---

## Cheatsheet Content Summary

All three cheatsheets are well-structured, domain-tuned, and contain genuinely useful principles. The issue is not that the cheatsheet is bad — it's that the analyzer sometimes contradicts its own cheatsheet rules (e.g., recommending clarification despite the cheatsheet saying not to).

### Math cheatsheet (~7400 chars, 4 batches)
Key principles that drove improvements:
- **Disambiguation policy**: Adopt deterministic interpretation, don't explore all branches
- **Anchoring detection**: Flag premature ANSWER lines before all shards are in
- **Canonical task spec**: Consolidate to one clean reading, not multiple interpretations

### Code cheatsheet (~7100 chars, 4 batches)
Key principles that drove improvements:
- **Semantic verification**: Check that the algorithm solves the right problem, not just interface compliance
- **Concrete failing examples**: Every issue must include Input/Expected/Actual
- **No unnecessary validation**: Trust user-provided guarantees

### Database cheatsheet (~7900 chars, 5 batches)
Key principles that drove improvements:
- **Exact column matching**: Treat column names/aliases as hard requirements
- **Single-row semantics**: Singular wording → ORDER BY + LIMIT 1
- **No clarification in constrained environments**: Apply deterministic defaults

---

## Implications for Improving Memory

### Problem diagnosis

The core issue is not with the cheatsheet content but with **compliance** — the analyzer doesn't always follow its own cheatsheet. The three anti-patterns (clarification-seeking, hallucinated requirements, over-prescription) are all things the cheatsheet explicitly warns against. The analyzer is a general-purpose LLM that sometimes ignores the cheatsheet rules in favor of its default behaviors (being helpful by asking questions, being thorough by adding detail).

### Potential improvements

1. **For S1 — memory is already working well.** +8 new solves across 3 tasks with zero regressions. The key is that S1's architecture (full conversation + supplementary analysis) naturally filters out analysis flaws. No changes needed for S1.

2. **For S1.5 — the analysis must be more precise.** Since the analysis is the sole context, we need:
   - **Stronger compliance enforcement**: Add explicit negative examples to the cheatsheet prompt — "NEVER write 'ask the user for clarification' in the user_intent or issues."
   - **User_intent audit**: Post-process the user_intent to strip any clarification-seeking language before using it in S1.5's compacted context.
   - **Column/requirement validation**: Cross-check the user_intent's column list against the actual user messages (available in the trace) before building the S1.5 context.

3. **For spec-targeted memory** — today's experiment showed that putting memory in Query 1 (task spec) matches or beats compare-targeted memory on code and database, but drops badly on math (70% vs 90%). The comparison query adds value on math by helping identify issues; removing memory from it while adding it to the spec diluted the spec on math. A "both" variant could combine the benefits.

4. **Cheatsheet format for S1.5**: Consider a separate cheatsheet mode for S1.5 that is more conservative — fewer recommendations, more constraint-focused, no "ask if unclear" patterns. Or filter the cheatsheet before injection to remove any rules that mention clarification or ambiguity.

---

## Experiment: Fixing S1.5+mem Regressions

Two approaches were tested to address the S1.5+mem regressions:

### Approach A: Post-Processing Sanitization (`--sanitize`)

Strip clarification-seeking patterns from the analysis before building S1.5's compacted context. Uses existing S1+mem traces — no re-running required.

Regex removes: "ask the user", "if unclear", "open questions", "do not assume answers", "clarification needed from the user", and related patterns from both `user_intent` and `issues` fields.

### Approach B: Compliance Rules in Analyzer Prompt (`enforce_compliance`)

Append explicit anti-clarification and anti-overspecification rules after the memory section in the comparison query prompt. Three rules:
1. NEVER suggest asking for clarification
2. Only include user-stated requirements (no hallucinated columns)
3. Describe WHAT is wrong, not HOW to fix it (avoid prescribing SQL forms)

Requires re-running S1+mem with the new prompt, producing new traces.

### Results

#### S1 Results (analysis-time)

| Config | Math (n=20) | Code (n≈19) | Database (n=25) |
|--------|:-----------:|:-----------:|:---------------:|
| S1 (no mem) | 16/20 (80%) | 10/18 (56%) | 8/25 (32%) |
| **S1+mem** | **18/20 (90%)** | **13/19 (68%)** | **11/25 (44%)** |
| S1+mem+compliant (B) | 15/20 (75%) | 13/19 (68%) | 7/25 (28%) |

**Approach B hurts S1.** The compliance rules over-constrain the analyzer:
- Math drops 90% → 75%: the "don't prescribe" rule makes the analysis too vague for math where specific error identification helps.
- Database drops 44% → 28%: the "don't add columns" rule may make the analyzer too conservative, and "don't prescribe SQL forms" removes guidance that database tasks benefit from.
- Code is unchanged at 68%.

#### S1.5 Results (context-reset)

| Config | Math (n≈20) | Code (n≈19) | Database (n=25) |
|--------|:-----------:|:-----------:|:---------------:|
| S1.5 (no mem) | 16/20 (80%) | 11/16† (69%) | 10/25 (40%) |
| S1.5+mem | 17/20 (85%) | 12/17† (71%) | 9/25 (36%) |
| **S1.5+mem+sanitize (A)** | **17/20 (85%)** | **13/19 (68%)** | **11/25 (44%)** |
| S1.5+compliant (B) | 15/20‡ (75%) | 13/19‡ (68%) | 9/25 (36%) |
| S1.5+compliant+sanitize (A+B) | 15/20‡ (75%) | 12/17‡ (71%) | 10/25 (40%) |

†Reduced denominators due to timeouts. ‡Uses approach B traces (already degraded at S1 level).

### Analysis of Results

**Approach A (sanitization) is the winner.** It keeps S1 unchanged (uses the same traces) and improves S1.5+mem:
- Database: 36% → **44%** (recovered from below-baseline to matching S1+mem)
- Math: 85% → 85% (unchanged, no clarification patterns in math)
- Code: 71% → 68% (comparable, denominator difference due to timeouts)

S1.5+mem+sanitize is the **first configuration where memory uniformly helps S1.5** across all tasks (vs S1.5 no-mem: math 85%≥80%, code 68%≈69%, database 44%>40%).

**Approach B (compliance rules) is harmful.** It degrades S1 quality on math (-15pp) and database (-16pp), and those degraded traces cascade into S1.5. The compliance rules are too blunt — they prevent valid analysis behaviors alongside the problematic ones.

**Approach A+B combined** doesn't help beyond A alone since the damage is done at analysis time in approach B.

### Why Approach A Works and B Doesn't

The key insight: **the anti-patterns are in the analysis output, not the analysis prompt.** The cheatsheet already contains the right rules ("do not recommend asking the user for clarification"). The analyzer just doesn't always comply. Adding more rules to the prompt (approach B) doesn't fix non-compliance — it adds more rules to potentially not comply with, while constraining the analyzer's useful behaviors.

Post-processing (approach A) is more surgical: it fixes the output directly, removing only the specific anti-patterns that cause S1.5 regressions, without touching the analysis process that S1 benefits from.

### Recommendation

Use **Approach A (sanitization)** for S1.5+mem runs:
- Add `--sanitize` flag when running `scripts/run_s15_experiment.py` with memory traces
- Do NOT use `enforce_compliance` — it harms S1 and provides no additional S1.5 benefit
- The sanitization is transparent and reversible (just a flag, traces unchanged)

### Remaining Gaps

Sanitization fixed 1/4 database regressions directly (val-389, the purest clarification-seeking case). The other 3 involved hallucinated columns (val-932), alternative SQL forms (val-498), and a subtler clarification pattern (val-401 with GROUP_CONCAT vs per-row). The net effect is still positive because sanitization also enables memory's benefits to flow through — the 3 new solves from S1+mem (val-498 in S1, val-555, val-75) are preserved while the regressions are partially mitigated.

---

## Run Directories

| Run | Dir |
|-----|-----|
| S1 math | `outputs/2026-03-16/20-08-42` |
| S1+mem math | `outputs/2026-03-16/20-33-21` |
| S1 code | `outputs/2026-03-16/20-12-21` |
| S1+mem code | `outputs/2026-03-16/20-42-35` |
| S1 database | `outputs/2026-03-16/20-25-09` |
| S1+mem database | `outputs/2026-03-16/20-52-20` |
| S1.5 math | `outputs/2026-03-17/01-21-21` |
| S1.5+mem math | `outputs/2026-03-17/01-28-32` |
| S1.5 code | `outputs/2026-03-17/01-22-15` |
| S1.5+mem code | `outputs/2026-03-17/01-29-56` |
| S1.5 database | `outputs/2026-03-17/01-27-14` |
| S1.5+mem database | `outputs/2026-03-17/01-34-55` |
| S1.5+mem+sanitize | `outputs/2026-03-17/08-13-54` (math/code), `outputs/2026-03-17/08-19-23` (database) |
| S1+mem+compliant math | `outputs/2026-03-17/08-20-09` |
| S1+mem+compliant code | `outputs/2026-03-17/08-29-02` |
| S1+mem+compliant database | `outputs/2026-03-17/08-39-22` |
| S1.5+compliant | `outputs/2026-03-17/08-57-15` |
| Memory checkpoints (v8) | `outputs/replay_memories/2026-03-16_19-13-12/` |
| Memory checkpoints (compliant) | `outputs/replay_memories/compliant_2026-03-17_08-20-08/` |
