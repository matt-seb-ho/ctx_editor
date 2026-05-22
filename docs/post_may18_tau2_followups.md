# tau2 Phase 0–1 findings + followups

**Predecessor**: `docs/post_may18_tau2_plan.md` (the execution plan, gated on R6 winner).
**Status**: Phase 0 + Phase 1 complete. Phase 2 (port v8) ready to start.

## Phase 0 — venv setup ✅

Built `/home/v-homatthew/tau2_ctxe/.venv` with Python 3.12.3.

Wrinkles that required workarounds:

1. **`python3-venv` apt package not installed on the system.** The plain `python3.12 -m venv` creates the venv tree but `ensurepip` fails (`No module named ensurepip`). Worked around by bootstrapping pip via `curl https://bootstrap.pypa.io/get-pip.py | python` inside the venv.
2. **`pyaudio` requires system PortAudio libs.** Not available; building from source fails. `pyaudio` is referenced unconditionally by `tau2.voice.utils.audio_io` which is on the import chain of `tau2/__init__.py` → `tau2.runner` → `tau2.evaluator` → `tau2.agent.base.streaming`. So ANY tau2 import fails without it. Worked around with a `.pth` shim that mocks `pyaudio` at Python startup:
   ```
   /home/v-homatthew/tau2_ctxe/.venv/lib/python3.12/site-packages/00_tau2_voice_shim.pth:
   import sys, types; sys.modules.setdefault('pyaudio', types.ModuleType('pyaudio'))
   ```
   The voice subsystem is irrelevant for `telecom_small` (text-only). We never instantiate any voice code path, so the mock is never exercised — it only needs to exist to satisfy the import.
3. **`scipy`, `elevenlabs`, `rank_bm25` are also on the import chain** (tau2 imports its evaluator + knowledge subsystems unconditionally). Installed via pip.

Smoke test passes:
```bash
PYTHONPATH=/home/v-homatthew/tau2_ctxe /home/v-homatthew/tau2_ctxe/.venv/bin/python -c "
from tau2.agent.llm_agent import LLMAgent
from ctx_edit.agents import AssistantOmitAgent, ContextEditAgent, ContextRewriteAgent
from ctx_editor.strategies.analyzer_prompts import ANALYZER_PROMPT_REGISTRY
"
```
Returns clean.

## Phase 1 — analyzer parity audit ✅ no refactor needed

### Setup

tau2's `ctx_edit/analyzer.py` has three prompt constants:

| Constant | Used by | Where the output goes |
|---|---|---|
| `TASK_SPEC_PROMPT_V10` | Q1 of both S2 and S3 | Internal intermediate (downstream Q2) |
| `COMPARE_PROMPT_V10_S2` | Q2 of S2 (Gated-Reset) | **Directly into the compacted context** (assistant reads it as briefing) |
| `COMPARE_PROMPT_V10_S3` | Q2 of S3 (Rewrite) | Q3 input (the rewriter LLM rewrites it into the final context) |

Q1 is shared, so the user-spec extraction is parity-identical between S2 and S3 ✓. This is the LiC analog's bug, and tau2 doesn't have it.

The S2/S3 Q2 prompts are **materially different**, which is the same architectural-asymmetry class that caused the LiC bug. We needed to check whether the difference is legitimately motivated.

### Diff: COMPARE_PROMPT_V10_S2 vs COMPARE_PROMPT_V10_S3

| Aspect | S2 (Q2 → compacted context) | S3 (Q2 → Q3 → compacted context) |
|---|---|---|
| Framing voice | First-person to the agent: *"You are performing a mid-task reflection..."*, *"Your analysis will directly replace..."* | Third-person about the agent: *"You are performing a mid-task analysis"*, *"Your analysis will be passed to a separate step that prepares a clean context"* |
| Style | Expansive, explanatory, includes encouragement and warnings ("Be thorough — missing a successful tool result here means the agent will waste a turn re-calling it") | Telegraph-style, data-rich: *"Be precise and data-rich — the next step needs exact values, not summaries"* |
| Sections | Backend state / valid progress (with explicit "for each successful tool call, include name/args/key fields") / issues / **next steps** | Backend state / valid progress / issues; **no explicit "next steps"** (deferred to Q3) |
| File self-documents the asymmetry | — | Explicit comment block: *"S3 variant: the analysis is an intermediate step — a separate LLM call will use it to write the final context. Be precise and data-rich (Q3 needs the raw facts)."* |

### Verdict — asymmetry is legitimately motivated

The two prompts have different consumers (assistant vs another LLM), and the framing differences match those consumer needs. S2 needs to talk *to* the agent because its output IS the briefing. S3 needs to dump raw facts because a downstream LLM will compose the briefing. The asymmetry was deliberate (per the inline `# v10.1 fixes` comment block — fixes targeted S3 specifically based on S3 failure analysis).

**Not the same class of bug as LiC.** Proceeding with Phase 2 (porting v8) without refactoring tau2's analyzer.

### Latent risk to monitor (not a Phase 1 blocker)

S3's Q2 is significantly more terse than S2's Q2. If S3 underperforms S2 by a wide margin in the eventual sweep, the asymmetry should be revisited — terseness may be dropping state that S2 preserves. The right test is: if v11 (R6-aligned Q3) doesn't close the S3 < S2 gap, try unifying Q2 (use S2's expansive Q2 as input to Q3 and see if the rewriter does better with richer input).

This is a hypothesis to test in Phase 5, not a refactor to do up front. The Phase 5 cells already separate S2 from S3 so we'll see the gap directly.

## Phase 2 next steps (not yet started)

Port v8 to tau2 as `CONTEXT_REWRITE_PROMPT_V11`. Inherit framing (analyzer-centered, conversation-as-reference, open-ended `<new_context>`, role-boundary) and add the tau2-specific tool-list block. Add a CLI flag in `run_parallel.py` so V10 (old) and V11 (R6-aligned) can be run side by side on one task as a smoke test before launching the full sweep.

## Acceptance log

- [x] Phase 0: tau2 + ctx_edit + ctx_editor imports clean (this doc).
- [x] Phase 1: parity is acceptable, proceeding (this doc).
- [ ] Phase 2: port v8 → CONTEXT_REWRITE_PROMPT_V11.
- [ ] Phase 3: implement AugmentAgent.
- [ ] Phase 5: 10-cell sweep.
- [ ] Phase 6: mega-table fill + summary doc.
