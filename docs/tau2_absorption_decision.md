# Tau2: Absorb or Federate?

The question: now that we want to scale Tau2 experiments alongside LiC / CollabLLM / WildChat, do we **absorb** the tau2 evaluation code into `ctx_editor`, **federate** (status quo — keep it in our fork of the upstream tau2-bench repo), or some **hybrid**?

## Constraints (the facts that matter)

- **tau2-bench is a real upstream package.** `/home/agent/tau2-bench/pyproject.toml` builds via hatchling, package name `tau2`. We could `pip install` it.
- **Our work lives in `/home/agent/tau2-bench/ctx_edit/`** — six Python files (~2k LoC: `agents.py`, `analyzer.py`, `run_parallel.py`, `run_experiment.py`, `run_diagnostic.py`, `build_cheatsheet.py`). Self-contained relative to the rest of tau2-bench.
- **Python version mismatch.** ctx_editor: `>=3.10`. tau2-bench: `>=3.12,<3.14`. Current dev env is 3.13 so both work, but absorbing forces ctx_editor's floor up to 3.12.
- **Heavy dependency footprint.** tau2-bench pulls in loguru, fastapi, uvicorn, deepdiff, addict, tenacity, etc. Adding all of those to ctx_editor's main deps would noticeably bloat anyone installing the package.
- **Big data tree.** `tau2-bench/data/` is **734 MB** (domain databases, task definitions, golden traces). Definitely not absorbing that into `ctx_editor/`.
- **Tau2's analyzer prompts are in their own world.** The `v10` / `v10.4` prompts are inline strings in `ctx_edit/analyzer.py`, shaped for tool-call + backend-state conversations. They are not interchangeable with our `v8/v9/v11` prompts in `strategies/analyzer_prompts.py` — those target conversational reasoning tasks. So unifying "analyzer prompt versions" is a code question, not a repo-layout question.
- **Tau2's S3 (Rewrite) is net-negative** today and not in the paper's headline table. Whatever we do here is preparation for *future* scaling, not preserving paper numbers — risk tolerance is higher than for LiC/CollabLLM/Huang.
- **Our `ctx_edit/` sits on a separate fork** (`mine` remote = `matt-seb-ho/tau2_ctxe.git`) of `sierra-research/tau2-bench`. Upstream tau2-bench is moving; we may want to pull their changes occasionally.

## Three options

### A. Status quo — fully federated

Keep `/home/agent/tau2-bench/ctx_edit/` as the only home for tau2 experiment code. No shared imports with `ctx_editor`.

- **Pros:** Already works. Upstream `git pull` from sierra-research is trivial. Tau2's 734MB data + heavy deps stay out of ctx_editor.
- **Cons:** Two repos to clone for reproduction. Tau2 doesn't inherit any of the Phase 1–3 improvements (analyzer prompt registry, ContextStrategy protocol, cross-benchmark schema, aggregator). To run "Tau2 across 3 seeds with v12 analyzer prompts", you write a bespoke shell loop — exactly what the rest of the cleanup was meant to retire.

### B. Absorb — move `ctx_edit/` into ctx_editor as `bench/tau2/`, depend on tau2-bench as a pip library

Migrate the six files into `src/ctx_editor/bench/tau2/`. Add `tau2 @ git+https://github.com/sierra-research/tau2-bench.git@<pinned-sha>` (or a pip-installable path) to ctx_editor's deps. The 734 MB data tree stays in tau2-bench (loaded via tau2's own paths).

- **Pros:** One repo to clone (modulo tau2 as an installed lib + its `data/`). Full Hydra integration. Tau2 gets the analyzer prompt registry, ContextStrategy protocol, run_summary schema, and aggregator for free. Future multi-seed sweeps are one `--multirun` flag.
- **Cons:** Forces ctx_editor's Python floor to 3.12. ctx_editor's dep tree balloons (loguru, fastapi, uvicorn, deepdiff, addict, tenacity, …). One-time migration touches every Tau2 import and adds Hydra wiring. If we ever want to ship `ctx_editor` to non-Tau2 users, the heavy deps are a real install-time cost.

### C. Hybrid — ctx_edit/ stays in the tau2-bench fork, but it imports from ctx_editor

Keep the current `tau2-bench/ctx_edit/` layout. Make ctx_editor pip-installable into the tau2-bench venv. Refactor `tau2-bench/ctx_edit/` to import `strategies.analyzer_prompts.ANALYZER_PROMPT_REGISTRY`, `huang_eval.strategies.HuangContextEditResult`-style metadata, and the run_summary schema from `ctx_editor`. The dependency is one-way: tau2-bench/ctx_edit depends on ctx_editor; the reverse does not hold.

- **Pros:** Doesn't move tau2-side code. Doesn't pollute ctx_editor's deps. Shared abstractions (analyzer prompts, AC3 contract, run_summary schema) propagate. Upstream tau2-bench `git pull` still trivial. Run-aggregator can scan tau2-bench/ctx_edit/outputs/ alongside ctx_editor's `outputs/` if we ask it to (already supports multiple roots).
- **Cons:** Two repos still — collaborators reproducing tau2 need to clone both. The shared-code change is bidirectional in practice: a refactor in ctx_editor that touches analyzer prompts has to be coordinated with a tau2-bench/ctx_edit version bump.

## Recommendation: **Option C (hybrid)**

The deciding factor is the **734 MB data tree + heavy dep footprint**. Tau2's evaluation cost is dominated by the upstream package + data, not by our ~2k lines of code. Pulling all of that into ctx_editor's install surface to make six Python files easier to find is a poor trade. Option C gets us the abstractions-sharing benefit (the actual goal) without paying that cost.

Federation framing the user proposed — "tau machinery is too complex for us to reimplement, let's just test our method against their benchmark by implementing our thing inside (a fork of) their repo" — is essentially Option C. The only extension is making the fork's ctx_edit/ pip-install ctx_editor so the shared abstractions actually flow.

## Concrete migration plan (if Option C is approved)

Ordered by reversibility. Each step is a small, separate commit so we can stop at any point.

1. **Make ctx_editor pip-installable from outside.** It already is (`pip install -e .`). Sanity check by installing into the tau2-bench venv.
2. **In tau2-bench/ctx_edit/, replace inline `v10`/`v10.4` analyzer prompts with entries in ctx_editor's `analyzer_prompts.py` registry.** Add a new flow `agentic_two_query` to the registry if needed (mirror of `two_query` but with the tool-aware framing). Tau2's analyzer becomes a thin sync wrapper around the existing ConversationAnalyzer pattern.
3. **Adopt the cross-benchmark schema.** Have tau2-bench/ctx_edit/run_parallel.py write `run_summary.json` alongside its existing `config.json` and `results.json`. Use `{benchmark: "tau2", experiment_name, metrics, …}`.
4. **Update `scripts/aggregate_results.py` to recognize `tau2-bench/ctx_edit/outputs/exp*` as run dirs.** Already supports multiple input paths; just need to point it at the tau2 outputs in addition to `outputs/`.
5. **Hydra-ify tau2-bench/ctx_edit/run_parallel.py** so `--multirun seed=42,43,44` works. Configs live in tau2-bench/ctx_edit/config/, not in ctx_editor's config tree, but use the same Hydra pattern.
6. **Document the dependency arrow in CLAUDE.md** (or a tau2-bench/CLAUDE.md): tau2-bench/ctx_edit depends on a specific commit of ctx_editor; updates are one-way.

Steps 1–3 are independently valuable and can ship without committing to 4–6. Steps 4–5 give us the Tau2-multirun-via-Hydra story.

## When to revisit

- If the heavy-dep concern goes away (e.g. tau2-bench publishes a slim eval-only extra), reconsider Option B.
- If we end up doing significant work *inside* tau2-bench itself (not just ctx_edit/), upstream-tracking pain may push toward absorbing.
- If Tau2's S3 gets fixed and becomes a real headline result, the case for tighter integration strengthens (paper-readiness > install-ergonomics).
