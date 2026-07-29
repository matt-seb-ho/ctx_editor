#!/usr/bin/env python
"""T14 — survey shipped false-negative exclusion rates across every archived run.

Reads, for each run directory that has a ``false_negatives.json``:
  - the strategy / task / model from ``config.yaml`` (fallback ``run_summary.json``)
  - raw correct / total from ``metrics.json`` and ``results.json``
  - the shipped user-sim-induced exclusion count from ``false_negatives.json``

No LLM calls. Emits one row per run to ``survey.json``.

Controls built in:
  - cross-checks ``metrics.json`` vs ``results.json`` vs ``run_summary.json`` and flags
    disagreement (T1 §8.4 control 2, and the double-write corruption trap).
  - flags runs whose FN analysis produced ZERO analysed samples despite having
    incorrect samples — that is the signature of the silent no-op under
    ``load_balancer=trapi`` with an unserved judge model.
"""
import json
import sys
from pathlib import Path

import yaml

ROOTS = [Path(p) for p in sys.argv[1:]] or [
    Path("/home/t-matthewho/ac3/t14_snapshot/ctx_editor/outputs")
]
OUT = Path(__file__).parent / "survey.json"


def jload(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def yload(p):
    try:
        return yaml.safe_load(open(p))
    except Exception:
        return None


def dig(d, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


rows = []
for root in ROOTS:
    for fn_path in sorted(root.rglob("false_negatives.json")):
        run = fn_path.parent
        fn = jload(fn_path)
        if fn is None:
            continue
        cfg = yload(run / "config.yaml") or {}
        summ = jload(run / "run_summary.json") or {}
        met = jload(run / "metrics.json") or {}
        res = jload(run / "results.json")

        strategy = (
            dig(cfg, "experiment", "strategy", "_target_")
            or dig(cfg, "experiment", "name")
            or summ.get("strategy")
            or ""
        )
        strategy_name = dig(cfg, "experiment", "name") or summ.get("strategy") or ""
        task = dig(cfg, "task", "name") or summ.get("task") or ""
        model = (
            dig(cfg, "model", "assistant_model")
            or dig(cfg, "model", "name")
            or summ.get("model")
            or ""
        )
        user_mode = (
            dig(cfg, "user_mode", "name")
            or dig(cfg, "task", "user_mode")
            or summ.get("user_mode")
            or ""
        )
        fn_model = dig(cfg, "false_negative_analysis", "model") or ""
        fn_enabled = dig(cfg, "false_negative_analysis", "enabled")
        lb = dig(cfg, "load_balancer", "name") or dig(cfg, "load_balancer", "_name_") or ""

        # --- raw counts, cross-checked from three sources -------------------
        n_res = n_correct_res = None
        n_err = 0
        if isinstance(res, list):
            valid = [r for r in res if not dig(r, "metadata", "error")]
            n_err = len(res) - len(valid)
            n_res = len(valid)
            n_correct_res = sum(1 for r in valid if r.get("is_correct"))

        # `adjusted_accuracy` is written into metrics by run_experiment.py:706 and
        # surfaced in run_summary.json["metrics"] (RECON calls this the canonical
        # headline number). metrics.json is the same dict for newer runs but not all.
        smet = summ.get("metrics") or {}
        met_correct = met.get("correct", smet.get("correct"))
        met_total = met.get("total_samples", smet.get("total_samples"))
        met_adj_total = met.get("adjusted_total", smet.get("adjusted_total"))
        met_adj_acc = met.get("adjusted_accuracy", smet.get("adjusted_accuracy"))
        met_user_sim_induced = met.get("user_sim_induced", smet.get("user_sim_induced"))
        met_raw_acc = met.get("accuracy", smet.get("accuracy"))
        summ_acc = smet.get("accuracy")

        # --- shipped FN exclusions ------------------------------------------
        analysed = fn.get("total_analyzed")
        excl = dig(fn, "summary", "user_sim_induced")
        non_ans = dig(fn, "summary", "non_answer_attempts")
        fn_errors = sum(1 for r in (fn.get("results") or []) if r.get("error"))

        # --- controls --------------------------------------------------------
        flags = []
        if n_res is not None and met_total is not None and n_res != met_total:
            flags.append(f"total_mismatch res={n_res} met={met_total}")
        if n_correct_res is not None and met_correct is not None and n_correct_res != met_correct:
            flags.append(f"correct_mismatch res={n_correct_res} met={met_correct}")
        if summ_acc is not None and met_raw_acc is not None and abs(summ_acc - met_raw_acc) > 1e-6:
            flags.append(f"summary_acc_mismatch {summ_acc} vs {met_raw_acc}")
        n_incorrect = (n_res - n_correct_res) if n_res is not None else None
        if n_incorrect and not analysed:
            flags.append("FN_NOOP: incorrect samples exist but 0 analysed")
        if analysed and fn_errors == analysed:
            flags.append("FN_ALL_ERRORED")

        rows.append(
            dict(
                run=str(run),
                group=str(run.relative_to(root)).split("/")[0],
                strategy_name=strategy_name,
                strategy_target=strategy,
                task=task,
                model=model,
                user_mode=user_mode,
                fn_judge_model=fn_model,
                fn_enabled=fn_enabled,
                load_balancer=lb,
                n_valid=n_res,
                n_correct=n_correct_res,
                n_incorrect=n_incorrect,
                n_errors=n_err,
                met_raw_acc=met_raw_acc,
                met_adj_acc=met_adj_acc,
                met_adj_total=met_adj_total,
                met_user_sim_induced=met_user_sim_induced,
                fn_analysed=analysed,
                fn_excluded_user_sim=excl,
                fn_non_answer=non_ans,
                fn_errors=fn_errors,
                excl_rate=(excl / analysed) if (excl is not None and analysed) else None,
                flags=flags,
            )
        )

json.dump(rows, open(OUT, "w"), indent=2)
print(f"{len(rows)} runs surveyed -> {OUT}")
bad = [r for r in rows if r["flags"]]
print(f"{len(bad)} runs with control flags")
from collections import Counter

c = Counter(f.split(":")[0].split(" ")[0] for r in bad for f in r["flags"])
for k, v in c.most_common():
    print(f"  {k}: {v}")
