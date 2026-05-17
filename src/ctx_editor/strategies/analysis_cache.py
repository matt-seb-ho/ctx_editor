"""Content-addressed cache for analyzer outputs.

When multiple AC3 variants (Augment, Reset, Gated-Reset, Rewrite) are run
against the same conversation prefix with the same analyzer model + prompt
version, they all do the SAME analyzer query. Without a cache that costs us
N analyzer calls per (prefix, variant) and — worse — introduces analyzer
non-determinism into the variant comparison.

This module is a lightweight filesystem cache keyed on:
  - canonical hash of the trace's message list
  - analyzer model
  - prompt version
  - the call-time knobs that change the prompt (spec_only,
    memory_target_query, enforce_compliance, whether memory is attached)

Layout::

    outputs/analysis_cache/
        registry.json                # append-only index
        {key[:2]}/{key}.json         # cached AnalysisResult + metadata

Each cache file holds a complete provenance record so we can audit later.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Lazy import to avoid circulars
def _AnalysisResult():  # noqa: N802 - factory style
    from .analyzer import AnalysisResult
    return AnalysisResult


_REGISTRY_LOCK = threading.Lock()


class AnalysisCache:
    """File-backed analyzer-output cache.

    Thread/process-safe for concurrent reads. Writes use a lock on the
    in-process registry update plus atomic-rename for cache files; concurrent
    workers that try to fill the SAME key may both compute, but only one wins
    the rename — the cost is one wasted query in that rare case, never a
    corrupt file.
    """

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "registry.json"
        if not self.registry_path.exists():
            self.registry_path.write_text(json.dumps({"entries": []}, indent=2))

    # ------------------- key construction -------------------

    @staticmethod
    def _hash_trace(trace) -> str:
        """Stable hash of the trace's message stream (role + content only).

        Handles both Message dataclasses (attribute access) and dict messages
        (mapping access). Empty role/content are coerced to empty strings.
        """
        msgs = []
        for m in getattr(trace, "messages", []) or []:
            if hasattr(m, "role"):
                role = getattr(m, "role", "") or ""
                content = getattr(m, "content", "") or ""
            else:
                role = m.get("role", "") if isinstance(m, dict) else ""
                content = m.get("content", "") if isinstance(m, dict) else ""
            msgs.append({"role": role, "content": content})
        canonical = json.dumps(msgs, sort_keys=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def make_key(
        *,
        trace_hash: str,
        analyzer_model: str,
        prompt_version: str,
        spec_only: bool,
        memory_target_query: str,
        enforce_compliance: bool,
        memory_present: bool,
    ) -> str:
        payload = {
            "trace_hash": trace_hash,
            "analyzer_model": analyzer_model,
            "prompt_version": prompt_version,
            "spec_only": bool(spec_only),
            "memory_target_query": memory_target_query,
            "enforce_compliance": bool(enforce_compliance),
            "memory_present": bool(memory_present),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # ------------------- I/O paths -------------------

    def _path_for(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    # ------------------- read/write -------------------

    def lookup(self, key: str):
        """Return an AnalysisResult or None."""
        p = self._path_for(key)
        if not p.exists():
            return None
        try:
            payload = json.loads(p.read_text())
        except Exception:
            return None
        result_data = payload.get("result")
        if not result_data:
            return None
        AR = _AnalysisResult()
        # Tolerate forward/backward field additions.
        known = {f.name for f in fields(AR)}
        kwargs = {k: v for k, v in result_data.items() if k in known}
        try:
            return AR(**kwargs)
        except Exception:
            return None

    def store(
        self,
        key: str,
        result,
        *,
        key_inputs: dict[str, Any],
        experiment_origin: str | None = None,
        provenance: Optional[dict[str, Any]] = None,
    ) -> None:
        p = self._path_for(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        AR = _AnalysisResult()
        if not isinstance(result, AR):
            # Defensive: only cache AnalysisResult-like
            return
        record = {
            "key": key,
            "key_inputs": key_inputs,
            "result": asdict(result),
            "experiment_origin": experiment_origin or os.environ.get("EXPERIMENT_NAME", "unknown"),
            "provenance": provenance or {},
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(record, indent=2))
        os.replace(tmp, p)
        self._append_registry(record)

    def _append_registry(self, record: dict) -> None:
        # Compact registry entry (no full result body)
        entry = {
            "key": record["key"],
            "analyzer_model": record["key_inputs"].get("analyzer_model"),
            "prompt_version": record["key_inputs"].get("prompt_version"),
            "spec_only": record["key_inputs"].get("spec_only"),
            "memory_present": record["key_inputs"].get("memory_present"),
            "experiment_origin": record["experiment_origin"],
            "provenance": record["provenance"],
            "created_at": record["created_at"],
            "file": str(self._path_for(record["key"]).relative_to(self.root.parent)) if self.root.parent in self._path_for(record["key"]).parents else str(self._path_for(record["key"])),
        }
        with _REGISTRY_LOCK:
            try:
                reg = json.loads(self.registry_path.read_text())
            except Exception:
                reg = {"entries": []}
            reg.setdefault("entries", []).append(entry)
            tmp = self.registry_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(reg, indent=2))
            os.replace(tmp, self.registry_path)

    # ------------------- maintenance -------------------

    def invalidate(
        self,
        *,
        prompt_version: str | None = None,
        analyzer_model: str | None = None,
        before: str | None = None,  # ISO date
        experiment_origin: str | None = None,
    ) -> int:
        """Delete matching cache entries. Returns count removed."""
        try:
            reg = json.loads(self.registry_path.read_text())
        except Exception:
            return 0
        keep, drop = [], []
        for e in reg.get("entries", []):
            if prompt_version and e.get("prompt_version") != prompt_version:
                keep.append(e); continue
            if analyzer_model and e.get("analyzer_model") != analyzer_model:
                keep.append(e); continue
            if experiment_origin and e.get("experiment_origin") != experiment_origin:
                keep.append(e); continue
            if before and (e.get("created_at") or "") >= before:
                keep.append(e); continue
            drop.append(e)
        for e in drop:
            p = self._path_for(e["key"])
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        with _REGISTRY_LOCK:
            self.registry_path.write_text(json.dumps({"entries": keep}, indent=2))
        return len(drop)

    def summary(self) -> dict[str, Any]:
        try:
            reg = json.loads(self.registry_path.read_text())
        except Exception:
            return {"total": 0}
        entries = reg.get("entries", [])
        by_am: dict[str, int] = {}
        by_pv: dict[str, int] = {}
        for e in entries:
            am = e.get("analyzer_model") or "?"
            pv = e.get("prompt_version") or "?"
            by_am[am] = by_am.get(am, 0) + 1
            by_pv[pv] = by_pv.get(pv, 0) + 1
        return {
            "total": len(entries),
            "by_analyzer_model": by_am,
            "by_prompt_version": by_pv,
        }
