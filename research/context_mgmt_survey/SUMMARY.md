# Context-management survey — wake-up memo

**For:** Matthew (back from intern-project focus). **Ran:** 2026-08-03 → 08-04, autonomous (deli).
**One-line answer to your question:** *No, we are not beating a strawman — but re-center the incumbent
from assistant-omit to summarization/compaction, and keep assistant-omit as the clean minimal baseline.*

---

## The question you asked

> Are we over-indexing on assistant-omit (one basic MIT paper) as *the* method to beat? Should we
> weigh more popular context-management techniques and their weaknesses (like entanglement is the
> weakness of assistant-omit)?

## The answer, in three bullets

1. **Assistant-omit is the right *minimal baseline*, not the headline foil.** Huang et al. 2026
   (`huang2026llmsbenefit`, the "context pollution" paper) is not an adversary — it *motivates us*. In
   its own words it: coins "context pollution"; measures the entanglement failure ("follow-up without
   feedback") at **33.1%** of real turns; says blanket omit is over-aggressive (*"requires storing only
   the relevant assistant turn"*); names our exact method as future work (*"a finer-grained approach …
   that preserves only the specific past assistant responses relevant to a given prompt"*); defers
   stateful/agentic tasks (tool outputs, execution traces) as *"an even more critical design problem"*;
   and calls for *"benchmarks that reflect true multi-turn dependence."* **We build the eval that
   measures the two gaps its own authors flagged.** (Full verbatim quotes: `findings/depth_huang.md`.)

2. **The real incumbent to foreground is summarization/compaction** — it's what production actually
   ships (Anthropic Compaction API, Cline auto-compact, Cursor `/summarize`), and the strongest research
   version for *stateful* agents is **ACON** (`kang2026acon`, ICML 2026, MSR). ACON is a **fair, strong
   comparator on the statefulness axis** (public code; AppWorld 56.5% vs 56.0% no-compression at ~26%
   fewer tokens) — *not* a strawman. But it is **compress-then-hope**: it summarizes raw history and
   leans on a *learned* guideline optimizer to keep whatever cross-turn signal mattered on its training
   tasks. It never resolves references first. Our wedge = *resolve-then-prune* holds on **novel**
   entanglement patterns its guideline never saw; plus ACON preserves the assistant's erroneous
   assumptions while our analyzer removes them. (`findings/depth_acon.md`.)

3. **Scooping is CLEAR.** The nearest neighbor, **StructFlowBench** (`li2025structflowbench`, Findings
   ACL 2025), has a 6-way *categorical* inter-turn taxonomy but: no continuous entanglement dial, no
   statefulness axis, no faithfulness gate, no context-strategy comparison, and it measures instruction
   *compliance in clean context* — not task accuracy under pollution. Cite-and-distinguish.
   (`findings/depth_structflowbench.md`.)

## Unifying framing (the one sentence for the paper)

> Every incumbent commits its lossy op — drop / evict-KV / summarize / retrieve-key / reset — **before**
> resolving how later turns refer back to earlier ones (*prune-then-hope*); we **resolve-then-prune**
> (decontextualize-then-edit), and expose **entanglement × statefulness** as independently dial-able,
> faithfulness-gated axes so strategies can be compared along them.

## The one thing to *run*, not argue (Experiment E1)

Seven of eight reviewer objections are answerable by citation today. The single paper-threatening one —
*"summarize with a state-preserving prompt already does both"* — needs an ablation. Add
**`summarize_guided`** (summarizer told to preserve every later-referenced referent + all env state) to
the method axis alongside `summarize_v1` and ours. It either underperforms us (generative summary can't
guarantee verbatim preservation) or collapses into an un-instrumented version of our mechanism — both
vindicate us. Already folded into `docs/plans/entanglement_benchmark_spec.md`. Full logic:
`notes/strawman_refutation.md`.

## Method axis for the accuracy sweep (final)

`accumulate` · `omit_assistant` (Huang) · `summarize_v1` (naive) · **`summarize_guided`** (O1 steelman) ·
`context_edit_v2` (ours) · *[optional]* **ACON** on the statefulness axis.

## What's where

| Artifact | Contents |
|---|---|
| `docs/entanglement_knob_findings.md` §7 | **Paper-facing** positioning + **drop-in related-work paragraph** |
| `notes/context_mgmt_survey.md` | Cross-cluster method-family × {entanglement, statefulness} matrix + scooping |
| `notes/strawman_refutation.md` | 8 reviewer objections steelmanned + rebutted; O1 → E1 |
| `findings/depth_{huang,acon,structflowbench}.md` | Verbatim-quote depth reads of the 3 load-bearing papers |
| `findings/cluster{1..5}_*.md` | Wave-1 breadth: summarization / memory-agents / retrieval / KV-pruning / evals-scooping |
| `findings/citation_audit.md` | 42 entries: 34 verified + 8 fixed, **0 fabrications** |
| `related_work.bib` | 42 deduped, audited BibTeX entries |
| `WORKLOG.md`, `state/` | Full decision log + deli state (iterations 0–3) |

## Recommended next actions (yours)

1. **Build the artifact-refinement benchmark** (`docs/plans/entanglement_benchmark_spec.md`) with the
   `summarize_guided` condition — that's the decisive experiment.
2. Optionally wire **ACON** as the statefulness-axis comparator (public code: github.com/microsoft/acon).
3. Paste §7.4's related-work paragraph into the NeurIPS/ICLR draft; bib is ready.

*No blockers. Survey milestones M1–M5 complete; effort saturated per the deli stop rule.*
