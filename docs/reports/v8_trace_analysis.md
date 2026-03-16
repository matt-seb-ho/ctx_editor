# V8 Trace Analysis — 2026-03-16

Investigating three open questions from the v8 replay-last-turn batch:
1. Why is S2 not better than S1?
2. Why does memory hurt S2?
3. Is the actions task solvable?

## 1. Why S1 Outperforms S2 (Math: S1+mem 90% vs S2+mem 75%)

**Key finding: S2's binary edit/no-edit gate creates catastrophic false negatives.**

There are **zero cases** where S2 beats S1 on math. The gap is entirely one-directional — S2 loses 3 samples that S1 gets right and gains nothing.

### Case Studies

**GSM8K/435 (Lollipops)** — S2 edit introduced multi-answer confusion.
- The S2 analyzer correctly detected the assistant missed a division step and triggered a reset.
- But the compacted task spec over-specified deliverables, asking for both "per friend" and "total" answers.
- The assistant produced two `ANSWER:` lines. The extractor grabbed the wrong one (20 instead of 5).
- S1 simply appended analysis, the assistant recalculated, gave one clean `ANSWER: 5`.

**GSM8K/307 (Sandy's weight)** — S2 analyzer false negative.
- The analyzer returned `needs_edit: false` with empty issues, failing to detect the assistant was giving a weekly rate (0.5) instead of number of weeks (16).
- S1's appended analysis caught the gap: "did not incorporate the latest user fact." The assistant self-corrected.

**GSM8K/144 (Kim's profit)** — S2 analyzer false negative.
- The analyzer validated incorrect reasoning ($92 = revenue for 3 clients, then scaled up) as "correct."
- Returned `needs_edit: false`. The assistant kept the wrong answer (173.33).
- S1's analysis nudged the assistant to reconsider, producing the correct answer (20).

### Root Cause

S1 is "always on" — analysis is appended every turn regardless of severity. Even imperfect analysis gives the assistant a chance to self-correct. S2's gate means a false negative is catastrophic: the assistant gets no help at all.

**Implication**: S2 could adopt a hybrid approach — always append analysis (like S1), and additionally do context edits when truly needed. This would eliminate the false-negative problem.

---

## 2. Why Memory Hurts S2 (Code: 72% → 68%, Database: 44% → 36%)

**Key finding: The cheatsheet crowds out the analyzer's natural reasoning ability.**

### Regression Patterns

**Code — livecodebench/2979**: The assistant solved the wrong problem (single-house matching instead of weighted interval scheduling). Without memory, the analyzer correctly identified "Fundamental problem mismatch" and triggered a successful edit. With memory (~1067 words of cheatsheet), the analyzer returned `needs_edit: false` — completely missing the algorithmic mismatch.

**Database — spider-val-972**: The assistant used `UPPER(TRIM(...)) LIKE '%NORTH%'` instead of simple `LIKE '%North%'`. Without memory, the analyzer caught both issues. With memory (~1108 words), it returned empty issues.

**Database — spider-val-401**: The assistant used GROUP_CONCAT/GROUP BY producing one row per teacher, when the spec required individual teacher-course rows. Without memory, caught and fixed. With memory (~1030 words), missed entirely.

### What the Cheatsheets Contain

Both final cheatsheets (~1080-1120 words) do NOT contain known harmful patterns ("ask clarifying questions", "Tag UNCONFIRMED_ASSUMPTION"). They are within the 1500-word cap. However, they exhibit:

1. **Attention dilution**: ~1000 words of procedural meta-instructions (sequencing, checklists, diagnostic pattern catalogs, severity heuristics) injected between the conversation and analysis. This large block of generic guidance consumes the model's attention, causing it to "follow the checklist" rather than deeply examine the conversation. In 3/4 regressions, the memory analyzer returned completely empty issues where the no-memory analyzer found clear problems.

2. **Surface-level bias**: Cheatsheets are heavily weighted toward surface validation (signatures, return types, formatting) and under-represent semantic/algorithmic correctness. The code regression involved a completely wrong algorithm that checklist-based analysis couldn't detect.

3. **Ambiguity amplification**: "Produce variants" / "document ambiguities" guidance causes the edited context to hedge instead of being decisive. In DB 497, the edited context included "Clarify whether the exclusion should be case-insensitive..." which confused the assistant into overly complex SQL.

### Key Takeaway

Memory doesn't introduce overtly harmful rules but **crowds out the analyzer's natural reasoning**. Without the cheatsheet, gpt-5-mini correctly identifies problems by reasoning about the conversation directly. With ~1000 words of procedural guidance, the analyzer becomes more procedural and less attentive to actual content, resulting in false negatives. This is particularly damaging for S2 because S2 depends on the analyzer correctly detecting problems.

---

## 3. Actions Task Solvability

**Key finding: Two orthogonal failure modes, one fixable, one structural.**

### Failure Mode 1: Only Last Call Extracted (11/18 failures)

The evaluation takes only `trace.last_assistant_message`. For parallel tasks requiring 2-4 simultaneous calls, the assistant naturally responds to each shard with just the current call. The last message contains only the most recent single call.

The 5 correct cases succeeded because the **last shard explicitly triggered accumulation**:
- parallel_2: "And **I also** want to calculate using aluminum's resistivity"
- parallel_43: "**Also** check for events in New York"
- parallel_54: "make the **second** order from the uptown location"

The 11 failures had shards that were **sequential without accumulation signals**:
- parallel_134 (BMI): shards reveal 4 people one at a time. Last message only has person 4's call.
- parallel_49 (player_status): "He wasn't a top scorer in 2017, so check for 2018 next" — actively encourages sequential behavior.
- parallel_177 (metals): shards add gold, silver, platinum, palladium one at a time.

### Failure Mode 2: Boolean `true` vs `True` (7/18 failures)

The model writes `true`/`false` (JavaScript/JSON style). The BFCL AST parser treats lowercase `true` as a Python variable name, producing string `"true"` instead of boolean `True`. This is a pure evaluator bug — the answers are semantically correct.

Affected: parallel_121, 155, 187, 199, 35, 5, 91.

### Classification of All 18 Failures

| Category | Count |
|---|---|
| Only last call extracted (no accumulation) | 11 |
| Boolean casing `true` vs `True` | 5 |
| Both (correct structure but bools wrong + partial accumulation) | 2 |

### Is It Solvable?

**Partially, with targeted fixes:**

1. **Boolean casing** — Straightforward evaluator fix. Normalize `true`/`false` to `True`/`False` before AST parsing. This alone would recover ~5-7 samples (22% → ~43-48%).

2. **Accumulation** — Deeper structural problem. Options:
   - System prompt: "always include ALL previously discussed function calls in your response"
   - Change extraction to accumulate function calls across all assistant messages (not just last)
   - Change user simulator to add accumulation signals in later shards

The accumulation problem is fundamentally adversarial to the sharded disclosure format. The user sim converts "do X, Y, and Z" into sequential messages that look like individual requests, not a batch.

---

## Output Directories (v8 batch)

| Run | Result | Dir |
|-----|:------:|-----|
| S0 math | 12/20 (60%) | `outputs/2026-03-16/19-13-13` |
| S0 code | 3/19 (16%) | `outputs/2026-03-16/19-16-03` |
| S0 database | 1/25 (4%) | `outputs/2026-03-16/19-23-00` |
| S0 actions | 2/23 (9%) | `outputs/2026-03-16/19-26-46` |
| S0+mem math | 11/20 (55%) | `outputs/2026-03-16/19-29-11` |
| S0+mem code | 4/19 (21%) | `outputs/2026-03-16/19-38-53` |
| S0+mem database | 1/25 (4%) | `outputs/2026-03-16/19-52-09` |
| S0+mem actions | 2/23 (9%) | `outputs/2026-03-16/20-01-16` |
| S1 math | 16/20 (80%) | `outputs/2026-03-16/20-08-42` |
| S1 code | 10/18 (56%) | `outputs/2026-03-16/20-12-21` |
| S1 database | 8/25 (32%) | `outputs/2026-03-16/20-25-10` |
| S1 actions | 5/23 (22%) | `outputs/2026-03-16/20-29-27` |
| S1+mem math | **18/20 (90%)** | `outputs/2026-03-16/20-33-21` |
| S1+mem code | **13/19 (68%)** | `outputs/2026-03-16/20-42-35` |
| S1+mem database | **11/25 (44%)** | `outputs/2026-03-16/20-52-21` |
| S1+mem actions | 2/23 (9%) | `outputs/2026-03-16/21-02-17` |
| S2 math | 15/20 (75%) | `outputs/2026-03-16/21-13-55` |
| S2 code | **13/18 (72%)** | `outputs/2026-03-16/21-18-03` |
| S2 database | **11/25 (44%)** | `outputs/2026-03-16/21-30-50` |
| S2 actions | 3/23 (13%) | `outputs/2026-03-16/21-35-58` |
| S2+mem math | 15/20 (75%) | `outputs/2026-03-16/21-41-45` |
| S2+mem code | 13/19 (68%) | `outputs/2026-03-16/21-51-32` |
| S2+mem database | 9/25 (36%) | `outputs/2026-03-16/22-02-35` |
| S2+mem actions | 3/23 (13%) | `outputs/2026-03-16/22-14-40` |

**Logs**: `outputs/replay_logs/2026-03-16_19-13-12/`
**Memory checkpoints**: `outputs/replay_memories/2026-03-16_19-13-12/`

---

## Actionable Next Steps

1. **S2 hybrid mode**: Always append analysis (like S1), plus do context edits when issues are found. Eliminates false-negative catastrophe.
2. **Memory attention budget**: Cap cheatsheet at ~500 words instead of 1500, or restructure to be more concise. The current ~1000 words of procedural guidance is diluting the analyzer.
3. **Actions boolean fix**: Normalize `true`→`True` in BFCL AST parser. Quick win for ~5-7 samples.
4. **Actions accumulation**: Add system prompt guidance "include ALL function calls in your response" or change extraction to accumulate across messages.
