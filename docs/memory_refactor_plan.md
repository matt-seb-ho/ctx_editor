# Refactor Plan: `cheatsheet/` → `memory/`

## Goal

Rename and restructure the cheatsheet module into a generic memory system with ABCs, so we can slot in different memory implementations (retrieval-augmented, structured KV, episodic, etc.) and compare them via config changes.

## Progress

| Step | Description | Status |
|------|-------------|--------|
| 1 | Create ABCs in `memory/base.py` | **DONE** |
| 2 | Create `memory/cheatsheet.py` (`CheatsheetMemory` + `CheatsheetUpdater`) | **DONE** |
| 3 | Update `strategies/base.py` | **DONE** |
| 4 | Update `strategies/baseline.py` | **DONE** |
| 5 | Update `strategies/context_edit.py` | **DONE** |
| 5 | Update `strategies/reflection.py` | **DONE** |
| 5 | Update `strategies/agentic_edit.py` | **DONE** |
| 6 | Update execution layer (`batched.py`, `parallel.py`, `runner.py`) | **DONE** |
| 7 | Update `core/simulator.py` and `run_experiment.py` | **DONE** |
| 8 | Update Hydra configs (`config.yaml`, experiment YAMLs) | **DONE** |
| 9 | Delete old `cheatsheet/` directory | **DONE** |
| 10 | Verify imports / smoke test | **DONE** |

## What Changed So Far

### New files created
- `src/ctx_editor/memory/__init__.py` — exports `MemoryModule`, `MemoryUpdater`, `CheatsheetMemory`, `CheatsheetUpdater`
- `src/ctx_editor/memory/base.py` — ABCs: `MemoryModule`, `MemoryUpdater`
- `src/ctx_editor/memory/cheatsheet.py` — `CheatsheetMemory(MemoryModule)`, `CheatsheetUpdater(MemoryUpdater)`

### Naming changes applied (complete)
| Old | New |
|-----|-----|
| `CHEATSHEET_BLOCK_TEMPLATE` | `MEMORY_BLOCK_TEMPLATE` |
| `_inject_cheatsheet_to_trace()` | `_inject_memory_to_trace()` |
| `_is_cheatsheet_injected()` | `_is_memory_injected()` |
| `cheatsheet_injected` (log type) | `memory_injected` |
| `prepare_context(cheatsheet=...)` | `prepare_context(memory=...)` |
| `use_cheatsheet` param | `use_memory` |
| `cheatsheet_target` param | `memory_target` |
| `CHEATSHEET_SECTION_TEMPLATE` | `MEMORY_SECTION_TEMPLATE` |
| `cheatsheet_section` format key | `memory_section` |
| `Cheatsheet` type hints | `MemoryModule` |

### `CheatsheetMemory` vs old `Cheatsheet`
- `content` and `version` are now `@property` accessors over `_content`/`_version` (required by ABC)
- All other behavior (history, rollback, metadata, save/load/clone) unchanged
- `CheatsheetUpdater.update_from_trajectory` and `batch_update` now accept `MemoryModule` (not `Cheatsheet`)
- Metadata writes use `isinstance(memory, CheatsheetMemory)` guard

## Design Notes

- Keep it lightweight: one ABC + one concrete implementation. No registry/factory/plugin system yet.
- The concrete class name `CheatsheetMemory` preserves the paper reference where relevant.
- Prompt templates keep `<cheatsheet>` XML tags for now to stay aligned with the Dynamic Cheatsheet paper terminology — this is cosmetic and can change later.
- The `cheatsheet/` directory should be fully removed after migration (no backwards-compat shims).
