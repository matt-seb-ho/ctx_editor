"""
Score per group from a run directory of jsonl logs, with optional keep-latest dedupe.

Examples:
  python score_runs.py --run_dir logs
  python score_runs.py --run_dir logs --dataset_fn sharded_instructions_600.json
  python score_runs.py --run_dir logs --dedupe --group_by task model
  python score_runs.py --run_dir logs --dedupe --group_by task conv_type model --out_csv results.csv
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def iter_jsonl_records(run_dir: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    run_path = Path(run_dir)
    if not run_path.exists():
        raise FileNotFoundError(f"run_dir not found: {run_dir}")

    for p in run_path.rglob("*.jsonl"):
        file_mtime = p.stat().st_mtime
        try:
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        d["_source_file"] = str(p)
                        d["_source_mtime"] = file_mtime
                        records.append(d)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    return records


def normalize_dataset_fn(dataset_fn: str) -> str:
    return os.path.basename(dataset_fn)


def extract_run_time(record: Dict[str, Any]) -> float:
    """
    Returns a sortable numeric time for the run.
    Prefers latest parseable timestamp in trace; falls back to source file mtime.
    """
    trace = record.get("trace", None)
    if isinstance(trace, list) and trace:
        ts = [msg.get("timestamp") for msg in trace if isinstance(msg, dict) and msg.get("timestamp")]
        if ts:
            parsed = pd.to_datetime(ts, errors="coerce", utc=True)
            parsed = parsed.dropna()
            if len(parsed):
                return float(parsed.max().timestamp())
    return float(record.get("_source_mtime", 0.0))


def to_bool_or_none(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)) and x in (0, 1):
        return bool(int(x))
    if isinstance(x, str):
        xl = x.strip().lower()
        if xl in ("true", "t", "1", "yes", "y"):
            return True
        if xl in ("false", "f", "0", "no", "n"):
            return False
    return None


def to_dataframe(records: List[Dict[str, Any]], dataset_fn: Optional[str] = None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Ensure expected columns exist
    for col in ["task", "task_id", "assistant_model", "conv_type", "dataset_fn", "score", "is_correct"]:
        if col not in df.columns:
            df[col] = None

    # Unify possible alternative naming
    if "task_name" in df.columns and df["task"].isna().all():
        df["task"] = df["task_name"]

    # Optional dataset filter (basename match, consistent with utils_log.py)
    if dataset_fn is not None:
        target = normalize_dataset_fn(dataset_fn)
        df["dataset_fn"] = df["dataset_fn"].astype(str).map(os.path.basename)
        df = df[df["dataset_fn"] == target].copy()

    # Normalize types
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["is_correct"] = df["is_correct"].map(to_bool_or_none)

    # Completed = has either score or is_correct
    df["is_completed"] = (~df["score"].isna()) | (~df["is_correct"].isna())

    # Run time used for dedupe
    df["_run_time"] = df.apply(lambda r: extract_run_time(r.to_dict()), axis=1)

    return df


def dedupe_keep_latest(
    df: pd.DataFrame,
    keys: List[str],
) -> pd.DataFrame:
    """
    Keep latest row per group defined by keys, based on _run_time.
    """
    missing = [k for k in keys if k not in df.columns]
    if missing:
        raise ValueError(f"Missing dedupe keys in df: {missing}")

    df2 = df.sort_values("_run_time")
    latest = df2.groupby(keys, dropna=False, as_index=False).tail(1)
    return latest.reset_index(drop=True)


def mean_over_nonnull(series: pd.Series) -> float:
    s = series.dropna()
    return float(s.mean()) if len(s) else float("nan")


def aggregate(df: pd.DataFrame, group_by: List[str]) -> pd.DataFrame:
    grouped = df.groupby(group_by, dropna=False)

    out = grouped.agg(
        n_convs=("task_id", "count"),
        completion_rate=("is_completed", "mean"),
        avg_score=("score", mean_over_nonnull),
        accuracy=("is_correct", mean_over_nonnull),
    ).reset_index()

    out["n_with_score"] = grouped["score"].apply(lambda s: int(s.notna().sum())).values
    out["n_with_is_correct"] = grouped["is_correct"].apply(lambda s: int(s.notna().sum())).values

    out = out.sort_values(group_by).reset_index(drop=True)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_dir", type=str, required=True, help="Root folder containing logs")
    parser.add_argument("--dataset_fn", type=str, default=None, help="Optional dataset filter (basename match)")

    parser.add_argument(
        "--group_by",
        nargs="+",
        default=["task"],
        help="Grouping keys: task, model, conv_type, dataset_fn (or raw column names).",
    )

    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Keep only latest run per (dataset_fn, task, task_id, conv_type, assistant_model).",
    )
    parser.add_argument(
        "--dedupe_keys",
        nargs="+",
        default=["dataset_fn", "task", "task_id", "conv_type", "assistant_model"],
        help="Override dedupe keys (column names).",
    )

    parser.add_argument("--out_csv", type=str, default=None, help="Optional output CSV path")
    args = parser.parse_args()

    key_map = {
        "task": "task",
        "task_id": "task_id",
        "model": "assistant_model",
        "assistant_model": "assistant_model",
        "conv_type": "conv_type",
        "dataset_fn": "dataset_fn",
    }
    group_by = [key_map.get(k, k) for k in args.group_by]
    dedupe_keys = [key_map.get(k, k) for k in args.dedupe_keys]

    records = iter_jsonl_records(args.run_dir)
    df = to_dataframe(records, dataset_fn=args.dataset_fn)

    if df.empty:
        print("No records found (or none matched dataset_fn filter).")
        return

    if args.dedupe:
        before = len(df)
        df = dedupe_keep_latest(df, dedupe_keys)
        after = len(df)
        print(f"Dedupe keep-latest: {before} -> {after} rows")

    summary = aggregate(df, group_by=group_by)

    with pd.option_context("display.max_rows", 200, "display.max_columns", 200, "display
