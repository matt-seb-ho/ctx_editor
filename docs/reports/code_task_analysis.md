# Code Task Spot-Check Analysis — 2026-03-14

## Results Context

| Setting | Accuracy |
|---------|----------|
| Concat baseline | 21/25 (84%) |
| S0 (baseline) | 1/25 (4%) |
| S1 (append analysis) | 2/25 (8%) |
| S2 (context edit) | 2/23 (9%) |
| S0+mem | 4/25 (16%) |
| S1+mem | 5/24 (21%) |

The massive gap between concat (84%) and multi-turn (<21%) demanded investigation.

## Finding 1: Answer Extraction Bug (accounts for ~3 false negatives per strategy)

The `extract_answer()` method in `src/lic/tasks/code/task_code.py` has a bug in its
fallback path. When the assistant outputs raw Python without markdown code fences:

```python
import_idx = text.rfind("import")
def_idx = text.rfind("def")
start_idx = import_idx if import_idx >= 0 else def_idx
```

When an `import` appears inside a function body (e.g., `import math`), `rfind("import")`
finds it at a position after `rfind("def")`, causing the parser to start from an indented
line → `ast.parse` SyntaxError → empty string returned.

**Confirmed false negatives** (code passes tests but extraction fails):
- S0: HumanEval/105, HumanEval/73, livecodebench/2850
- S1: HumanEval/105, livecodebench/2916
- S2: HumanEval/153, livecodebench/2845, livecodebench/2873

**Why concat doesn't have this problem**: The concat prompt template includes code fence
instructions, so the model wraps code in `\`\`\`python\`\`\``. The primary extraction path
(regex for code blocks) works fine. In multi-turn mode, the system prompt doesn't ask for
code fences.

**Note**: This is a LiC evaluation issue. The extraction code is from the original LiC
codebase. We should be cautious about "fixing" it since it changes the evaluation conditions.
However, the extraction failure is an artifact of the multi-turn format (longer responses,
more inline imports) that doesn't affect concat mode. It's reasonable to note this as a
known measurement issue.

## Finding 2: Sharding Fundamentally Harms Code Tasks

Even with extraction fixed, ~80% of problems fail because the code itself is wrong. The
sharding process loses critical information that the concat prompt preserves:

### 2a. Missing Function Signatures and Starter Code (biggest factor)

The concat prompt includes starter code (e.g., `class Solution: def canSplitArray(self,
nums: List[int], m: int) -> bool:`) which gives the model the exact function signature,
parameter types, return type, and class structure.

Multi-turn shards describe the problem in natural language without conveying:
- Expected function name or signature
- Parameter types and count
- Return type
- Whether `class Solution` is required (all LiveCodeBench problems need this)

The system prompt says "Do not wrap with a class" — directly contradicting LCB requirements.

**Example — livecodebench/2812** (theMaximumAchievableX): Shard 1 is "what's the max
achievable number?" The model produces `def answer(): return ("I don't have enough
information...")`. The concat baseline gets the complete starter code and solves it trivially.

### 2b. Vague First Shards Lock the Model

6/25 S0 traces produced `def answer()` or `def solve()` — stub functions returning string
explanations. The first shard is often so vague the model treats it as a question, not
a coding task. Once locked into this pattern, later shards can't overcome it.

**Example — HumanEval/62** (polynomial derivative): Shard 1 is "Find the derivative of a
polynomial." The model writes `def solve()` reading from stdin. Even after 5 more shards
clarifying the input format, it stays on the stdin approach.

### 2c. Return Type Mismatches

Even when the algorithm is correct, the model gets the return type wrong because shards
don't specify it.

**Example — HumanEval/5** (intersperse): The model returns a joined string (`"1, 2, 3"`)
when tests expect a list (`[1, 4, 2, 4, 3]`). The shards say "add a delimiter between
list items" which sounds like string joining.

## Finding 3: S1/S2 Strategies Can't Fix Missing Specifications

The analysis correctly identifies the user's requirements, but can't supply information
that was never in the shards (function signatures, starter code, class structure). The
fundamental problem is information loss during sharding, not inadequate analysis.

S2 triggered edits in 10/25 traces. In one case (HumanEval/118), the reset helped and
the problem was solved. But in most cases, editing can't fix what was never there.

## Corrected Accuracy Estimates (if extraction were fixed)

| Strategy | Official | Extraction-Fixed |
|----------|----------|-----------------|
| S0 | 1/25 (4%) | ~4/25 (16%) |
| S1 | 2/25 (8%) | ~4/25 (16%) |
| S2 | 2/25 (9%) | ~5/25 (20%) |
| Concat | 21/25 (84%) | 21/25 (84%) |

## Implications

1. **The code task has structural evaluation issues** that inflate the gap between concat
   and multi-turn. Missing starter code and the extraction bug account for a large portion
   of failures.

2. **Our strategies (S1, S2) are not the bottleneck** for code — the sharding process is.
   The analysis works fine but can't supply missing function signatures.

3. **For fair evaluation**, the code task results should be interpreted with these caveats.
   The math and actions tasks are cleaner tests of our methods since they don't rely on
   specific function signatures or starter code.

4. **Extraction fix estimate**: If we fixed the extraction bug (but not the sharding
   issue), S2 would show a modest advantage (20% vs 16%) suggesting the context editing
   is helping where it can.
