# Implementation Map — `EntanglementUserAgent`

Goal: a user-simulation variant that, when revealing a shard, phrases the utterance
to *depend on the assistant's prior turn* to a controllable degree (`entanglement_level`,
int 0–3). Shard **intent** (and thus grading) is unchanged; only surface phrasing changes.
One benchmark can then be swept across entanglement levels to compare context strategies.

All refs are `file:line` against repo root `/home/t-matthewho/ac3/ctx_editor`.

---

## 1. UserAgent (the thing we vary)

File: `src/ctx_editor/agents/user_agent.py`

- Class `UserAgent` at `user_agent.py:31`. Constructor `user_agent.py:37-57` takes
  `task`, `model`, optional `prompt_file`. Prompt defaults to `DEFAULT_USER_PROMPT`
  loaded at module import (`user_agent.py:17`) from `prompts/user_agent.txt`.
- `async def generate_response(...)` at `user_agent.py:59-136`. Flow:
  - `num_user_msgs = trace.num_user_turns` (`:78`).
  - Special-cased tasks (translation/summary/data2text) use `populate_sharded_prompt`
    (`:81-84`) — not relevant to math/code/db/actions.
  - **First turn** (`num_user_msgs == 0`, `:87-93`): returns `sample["shards"][0]["shard"]`
    verbatim with its `shard_id`, **no model call**. (No prior assistant turn exists, so
    entanglement is impossible here — leave verbatim.)
  - **Subsequent turns** (`:95-136`): computes revealed vs unrevealed shards from
    `trace.get_revealed_shard_ids()` (`:96-101`); if none left returns a fixed
    "shared all" message (`:104-109`); else builds the prompt via
    `self.prompt_response.format(conversation_so_far=..., shards_revealed=..., shards_not_revealed=...)`
    (`:112-117`) and calls `model_client.generate_json(...)` under `call_tag("user")`
    (`:120-128`). Returns `UserResponse(content=result["response"], shard_id=result["shard_id"], ...)`
    (`:130-136`).
- `UserResponse` dataclass at `user_agent.py:20-28`: fields `content`, `shard_id`,
  `cost_usd`, `model_response`, `budget_exhausted`. **`shard_id` is what drives grading/
  progress** (logged as `shard_revealed`, see §3). Preserve it unchanged.

Prompt file: `src/ctx_editor/prompts/user_agent.txt`
- Placeholders: `{conversation_so_far}`, `{shards_revealed}`, `{shards_not_revealed}`
  (all `.format()`-substituted). Note literal `{{...}}` for the JSON example (escaped braces).
- Output contract: JSON `{"response": <str>, "shard_id": <int or -1>}`.
- Existing rule `[Rephrase Shards]` (line 19) already permits conversational rephrasing —
  entanglement just pushes rephrasing to *reference the assistant's last turn*.
- **`{conversation_so_far}` already contains the assistant's prior message**, so the model
  physically sees it; entanglement is achieved by adding level-keyed *instructions*, not new data.

**How a variant plugs in.** User-agent selection is **not** Hydra `_target_` — it's a
hardcoded `if/elif` on `cfg.user_mode.name` in `run_experiment.py` (see §2/§5). So the
clean pattern is: subclass `UserAgent`, add an `entanglement_level` ctor arg, and add a
branch. Existing siblings that subclass/duplicate this shape:
`agents/natural_user_agent.py` (`NaturalUserAgent`, `:22`) and
`agents/length_constrained_user_agent.py` (`LengthConstrainedUserAgent`). Exports live in
`agents/__init__.py:1-15`.

Instantiation sites of `UserAgent(` (grep):
- `run_experiment.py:281` — the sharded fallback branch (our entry point to extend).
- `run_collabllm.py:153` — separate CollabLLM entrypoint (out of scope).
- `src/lic/simulator_sharded.py:32`, `src/lic/simulator_snowball.py:41` — legacy LiC
  code (out of scope).

---

## 2. Config system (Hydra)

Root config: `src/ctx_editor/config/config.yaml`
- `defaults` (`config.yaml:1-7`): `experiment`, `model`, `task`, `user_mode: sharded`,
  optional `load_balancer`.
- `experiment_name: ${experiment.name}_${user_mode.name}_${model.name}_${task.name}`
  (`config.yaml:10`) — output dir naming picks up `user_mode.name` automatically.

`user_mode/` group: `src/ctx_editor/config/user_mode/`
- `sharded.yaml` — just `name: sharded` (LiC-identical; the default).
- `natural.yaml` — `name`, `include_shards`, `max_turns`.
- `length_constrained.yaml` — `name`, token-budget params.

**Key fact:** user_mode configs carry **no `_target_`**. The agent object is chosen by an
`if/elif` on `cfg.user_mode.name` at `run_experiment.py:262-281`, reading extra params via
`cfg.user_mode.get("<param>", default)`. So a new `entangled.yaml` just needs a `name` plus
`entanglement_level`, and a matching branch in that if/elif.

Strategies, by contrast, **do** use `_target_` (`get_strategy` at `run_experiment.py:129-135`
calls `hydra.utils.instantiate`). Not needed for the user agent.

New file to add — `src/ctx_editor/config/user_mode/entangled.yaml`:
```yaml
# Entangled user mode — reveals shards but phrases them to depend on the
# assistant's prior turn to a controllable degree. Shard intent preserved.
name: entangled
entanglement_level: 2   # 0=self-contained (== sharded) .. 3=fully relative
```
Selected on the CLI with `user_mode=entangled user_mode.entanglement_level=3`.

Instantiation path (config → object):
`config.yaml` defaults → `run_experiment.main` builds `cfg` → `make_simulator`
(`run_experiment.py:242-293`) reads `cfg.user_mode.name` (`:263`) → new `elif user_mode ==
"entangled"` branch constructs `EntanglementUserAgent(...)` → passed to
`ConversationSimulator(user_agent=..., ...)` (`:283-293`).

---

## 3. Simulator turn loop — is the prior assistant turn available?

File: `src/ctx_editor/core/simulator.py`, `_run_turn` at `:389-551`.
- Step 1 (`:401-409`) calls `self.user_agent.generate_response(trace=self.trace, sample=...,
  model_client=..., temperature=user_cfg.temperature, reasoning_effort=...)`. The `trace`
  passed in **already contains all prior turns**, including the previous assistant message
  (assistant messages are appended at `:454-457` in the *previous* iteration).
- **Yes — the assistant's prior turn is available** on turn ≥2. Access it via
  `trace.last_assistant_message` (property, `core/trace.py:52-58`) → returns a `Message`
  (or `None`); use `.content`.
- Shard bookkeeping: after the user msg is added, `_run_turn` logs
  `shard_revealed` with `shard_id` when `shard_id not in (None, -1)` (`simulator.py:419-422`).
  `trace.get_revealed_shard_ids()` (`core/trace.py:359-361`) reads those logs. Grading/
  progress depend only on `shard_id`, **not** on utterance phrasing → intent preservation
  holds as long as the subclass returns the same `shard_id` the base logic would.

Relevant `ConversationTrace` methods (`core/trace.py`):
- `last_assistant_message` `:52-58`; `last_user_message` `:44-50`.
- `get_conversation_string(skip_system, only_last_turn, active_only)` `:307-332` —
  `only_last_turn=True` returns just messages after the last user msg (handy if you want
  *only* the assistant's latest reply rather than the whole transcript).
- `get_revealed_shard_ids()` `:359-361`; `num_user_turns` `:60-63`.

---

## 4. Strategies available as baselines (config name → class)

Selected via `experiment=<name>`; each `experiment/*.yaml` sets `strategy._target_`.
Class aliases are defined in `strategies/__init__.py:20-61`.

| Role | `experiment=` yaml | `_target_` (as written in yaml) | Impl class:line |
|---|---|---|---|
| S0 baseline (no edit) | `baseline` | `ctx_editor.strategies.BaselineStrategy` | `baseline.py:14` |
| Drop-assistant | `omit_assistant` | `ctx_editor.strategies.OmitAssistantStrategy` | `prior_work_baselines.py:19` |
| S1 append analysis | `append_analysis` | `ctx_editor.strategies.AppendAnalysisStrategy` | `append_analysis.py:41` (`AC3AugmentStrategy`) |
| S2 our method (gated reset) | `context_edit_v2` | `ctx_editor.strategies.ContextEditV2Strategy` | `context_edit_v2.py:24` (`AC3ResetStrategy`) |
| Summarization | `summarize_v1` | `ctx_editor.strategies.SummarizationStrategy` | `summarization.py:55` |
| Compaction / rewrite | `collabllm_compaction` | `ctx_editor.strategies.ContextCompactionStrategy` | `context_compaction.py:51` (`AC3RewriteStrategy`) |
| ERGO restart | `ergo` | `ctx_editor.strategies.ERGORestartStrategy` | `ergo_restart.py:50` |

Note: `assistant_omit.py:22` defines `AssistantOmitStrategy` (a distinct, BaseStrategy-derived
"omit assistant" variant, exported in `__init__`); the `omit_assistant.yaml` config wires the
`prior_work_baselines.OmitAssistantStrategy`. Also `AssistantOmitStrategy` vs
`OmitAssistantStrategy` are two separate classes — confirm which you want when comparing.
All strategies implement `prepare_context()` (`ContextStrategy` protocol, `base.py:24-56`;
`BaseStrategy` at `base.py:59`). **Entanglement is orthogonal to strategy** — no strategy
change is needed; you sweep `user_mode` × `experiment`.

---

## 5. Run entrypoint & launching one benchmark

Console script: `ctx-editor = "ctx_editor.run_experiment:main"` (`pyproject.toml:47`).
Entry file `src/ctx_editor/run_experiment.py`.

- Model client chosen in `get_model_client` (`:113-126`): `AnthropicModelClient` if
  `"claude"` in the assistant model name, else `OpenAIModelClient(load_balancer_config=...)`.
- Samples loaded by `load_samples` (`:88-110`): reads `cfg.task.data_file`, filters by
  `cfg.task.filter`, and truncates by `cfg.task.limit` (`:106-108`) — set
  `task.limit=N` to run a pilot on N samples.
- Simulator built per-sample in `make_simulator` (`:242-293`); user-agent branch at
  `:262-281` (the site to extend, §2).
- Outputs land under `logging.output_dir` = `outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}`
  (`config.yaml:44`). Per-sample traces + `results_partial.jsonl` written incrementally
  (`:315`, `:329-345`). (CLAUDE.md's `outputs/{experiment_name}/{timestamp}/` is the older
  layout; current default is date/time-based — either way, unique per run.)

Minimal pilot CLI (few samples, cheap model, gated-reset strategy, entangled level 2):
```bash
ctx-editor \
  experiment=context_edit_v2 \
  model=gpt4o_mini \
  task=dev_math \
  user_mode=entangled user_mode.entanglement_level=2 \
  task.limit=3 \
  execution.max_concurrent=3 \
  logging.verbose=true
```
Swap `user_mode.entanglement_level=0..3` and `experiment=baseline|append_analysis|context_edit_v2`
to fill the sweep. `dev_math` already maps `math → math_v2` (`task/dev_math.yaml:7-8`).

---

## 6. Sample / shard data format

Confirmed via `data/dev_math_subset.json` (N=23). Per-sample keys:
`question, answer, task_id, shards, task, full_spec_q, ground_truth_a`.
- `shards`: list of `{"shard_id": <int>, "shard": <str>}`. E.g.
  `{"shard_id": 1, "shard": "how many fruits does an avocado tree produce over 10 years?"}`,
  `{"shard_id": 2, "shard": "a 5-year-old avocado tree produces 50 fruits normally"}`.
- `full_spec_q` and `ground_truth_a` present (used by `_build_result_metadata`,
  `simulator.py:112-133`, and evaluation). **Entanglement must not touch these.**
- `shard_id` here is an **int**; user-agent JSON returns int or `-1`. Preserve type.

Smallest pilot files (`data/`): `dev_math_subset.json` (23), `dev_code_subset.json`,
`dev_database_subset.json`, `dev_actions_subset.json`. Even smaller sets:
`lic_mini_eval4.json`, `t24_fullspec_single_shard.json`. Use `task=dev_math` + `task.limit`.

---

## 7. Model client

File: `src/ctx_editor/models/base.py`.
- Protocol `generate_json(messages, model, temperature=0.0, max_tokens=None, timeout=30,
  variables=None, reasoning_effort=None)` at `:114-138`; `BaseModelClient.generate_json`
  default impl `:158+` wraps `generate` (`:145-156`) + JSON parse. This is what the user
  agent already uses (`user_agent.py:123`) for structured `{"response","shard_id"}` output —
  **reuse it unchanged** for the entangled agent.
- Concrete clients: `OpenAIModelClient`, `AnthropicModelClient` (imported in
  `run_experiment.py:33-35`).
- Per-role model/temperature/reasoning come from the `model/*.yaml` config; the user role's
  settings are read in `simulator._run_turn` (`user_cfg = self.config.model_config.user`,
  `:402-408`) and passed into `generate_response`. The agent's own `self.model` is set from
  `sim_config.user_model` at construction (`run_experiment.py:281`).

Model configs (`config/model/*.yaml`), per-role blocks `user/assistant/system/ctx_editor`
(see `gpt4o_mini.yaml`):
- `model=gpt4o_mini` — cheapest, needs `OPENAI_API_KEY` (or Azure `AZURE_OPENAI_API_KEY` +
  `AZURE_OPENAI_ENDPOINT`).
- `model=claude` — needs `ANTHROPIC_API_KEY`; triggers `AnthropicModelClient`.
- `model=gpt5_4_mini_trapi` — TRAPI/`azure_foundry` `gpt-5.4-mini`; requires the TRAPI
  load-balancer config (`load_balancer=trapi` or `.../t9_foundry_trapi`) and TRAPI env
  (see MEMORY `trapi-in-ctx-editor`). Env vars auto-load from `.env` at repo root.

For a low-cost entanglement pilot use `model=gpt4o_mini`.

---

## Integration checklist (ordered, minimal, pattern-matching)

1. **Prompt** — add `src/ctx_editor/prompts/entangled_user_agent.txt`. Start from
   `prompts/user_agent.txt` (keep the `{conversation_so_far}`, `{shards_revealed}`,
   `{shards_not_revealed}` placeholders and the JSON `{"response","shard_id"}` contract with
   escaped `{{...}}`), and add one new placeholder, e.g. `{entanglement_instructions}`,
   plus a rule: *"Phrase your reveal so it references the assistant's most recent message per
   the entanglement instructions, but the underlying information you convey must be exactly
   the chosen shard — do not change or drop any of its content."* Preserve `[Reveal Entire
   Shard]` and `[One Shard at a Time]`.

2. **Agent** — add `src/ctx_editor/agents/entanglement_user_agent.py` with
   `class EntanglementUserAgent(UserAgent)` (subclass — inherits `__init__`/first-turn/
   all-revealed handling). Add ctor param `entanglement_level: int = 0`; store it. Load the
   new prompt (module-level `ENTANGLED_USER_PROMPT = (PROMPTS_DIR/"entangled_user_agent.txt").read_text()`).
   Override `generate_response`: mirror the base subsequent-turn path
   (`user_agent.py:95-136`) but (a) short-circuit to the base implementation when
   `entanglement_level == 0` (== plain sharded) or when `trace.last_assistant_message is None`
   (first turn / no prior assistant); (b) build a level→instruction string via a small dict
   (0: "self-contained, do not reference the assistant"; 1: "lightly reference it"; 2:
   "moderately relative — pronouns/back-references ok"; 3: "fully relative, e.g. 'no, reverse
   that' style"); (c) `.format(..., entanglement_instructions=...)` and call
   `model_client.generate_json(...)` exactly as the base does; (d) return `UserResponse` with
   the model's `shard_id` **unchanged**. Keep first-turn/all-revealed branches identical to
   base (reuse via `super().generate_response` where possible).

3. **Exports** — add `EntanglementUserAgent` to `src/ctx_editor/agents/__init__.py`
   (import + `__all__`, matching lines `:3-15`).

4. **Config** — add `src/ctx_editor/config/user_mode/entangled.yaml` with
   `name: entangled` and `entanglement_level: 2` (see §2). No `_target_` needed.

5. **Wiring** — in `src/ctx_editor/run_experiment.py`, import the class
   (add to the `from ctx_editor.agents import ...` line at `:16`) and add a branch in
   `make_simulator` alongside `:264-281`:
   ```python
   elif user_mode == "entangled":
       user_agent = EntanglementUserAgent(
           sample_task,
           model=sim_config.user_model,
           entanglement_level=cfg.user_mode.get("entanglement_level", 0),
       )
   ```
   Keep the existing `else: UserAgent(...)` fallback.

6. **(Optional) provenance** — to analyze by level later, stash `entanglement_level` into
   run metadata. `experiment_name` already includes `user_mode.name` (`config.yaml:10`); if
   you want the integer in outputs too, add it where `user_mode` is recorded in
   `run_experiment.py:677` / `:731`.

7. **Smoke test** — run the §5 pilot with `user_mode.entanglement_level=0` and confirm
   results match a plain `user_mode=sharded` run (byte-identical shard_ids / scores), then
   bump to `=3` and eyeball `verbose` output for relative phrasing while scores/`shard_id`s
   stay valid.

**Files added:** `prompts/entangled_user_agent.txt`, `agents/entanglement_user_agent.py`,
`config/user_mode/entangled.yaml`.
**Files modified:** `agents/__init__.py`, `run_experiment.py` (import + one `elif`).
No strategy, simulator, trace, evaluator, or data changes required.
