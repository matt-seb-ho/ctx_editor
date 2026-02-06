#!/usr/bin/env python3
"""
Score per task from a run directory containing task subfolders.

Example:
  python score_runs.py --run_dir logs --dataset_fn sharded_instructions_600.json
  python score_runs.py --run_dir logs --group_by task model
  python score_runs.py --run_dir logs --group_by task conv_type model --out_csv results.csv
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def iter_jsonl_records(run_dir: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    run_path = Path(run_dir)
    if not run_path.exists():
        raise FileNotFoundError(f"run_dir not found: {run_dir}")

    for p in run_path.rglob("*.jsonl"):
        # read each jsonl line as one conversation record
        try:
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        d["_source_file"] = str(p)
                        records.append(d)
                    except json.JSONDecodeError:
                        # skip bad lines; your utils_log.load_results_from does cleanup,
                        # but we keep this robust.
                        continue
        except OSError:
            continue

    return records


def normalize_dataset_fn(dataset_fn: str) -> str:
    # match utils_log behavior: compare only basename
    return os.path.basename(dataset_fn)


def to_dataframe(records: List[Dict[str, Any]], dataset_fn: Optional[str] = None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Ensure expected columns exist
    for col in ["task", "assistant_model", "conv_type", "dataset_fn", "score", "is_correct"]:
        if col not in df.columns:
            df[col] = None

    # Some logs may use "task_name" instead of "task" (rare); unify.
    if "task_name" in df.columns and df["task"].isna().all():
        df["task"] = df["task_name"]

    # If dataset_fn filter requested
    if dataset_fn is not None:
        target = normalize_dataset_fn(dataset_fn)
        df["dataset_fn"] = df["dataset_fn"].astype(str).map(os.path.basename)
        df = df[df["dataset_fn"] == target].copy()

    # Normalize booleans
    # is_correct may be None
    def to_bool_or_none(x):
        if x is None:
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

    df["is_correct"] = df["is_correct"].map(to_bool_or_none)

    # Score may be None; coerce numeric where possible
    df["score"] = pd.to_numeric(df["score"], errors="coerce")

    # Some tasks may only populate score or only is_correct.
    # Define "completed" as having either.
    df["is_completed"] = (~df["score"].isna()) | (~pd.isna(df["is_correct"]))

    return df


def aggregate_scores(df: pd.DataFrame, group_by: List[str]) -> pd.DataFrame:
    if df.empty:
        return df

    # accuracy: mean over non-null is_correct
    # avg_score: mean over non-null score
    def mean_over_nonnull(series: pd.Series) -> float:
        s = series.dropna()
        return float(s.mean()) if len(s) else float("nan")

    grouped = df.groupby(group_by, dropna=False)

    out = grouped.agg(
        n_convs=("conv_id", "count") if "conv_id" in df.columns else ("_source_file", "count"),
        completion_rate=("is_completed", "mean"),
        avg_score=("score", mean_over_nonnull),
        accuracy=("is_correct", mean_over_nonnull),
    ).reset_index()

    # Helpful: also count how many had score / is_correct
    out["n_with_score"] = grouped["score"].apply(lambda s: int(s.notna().sum())).values
    out["n_with_is_correct"] = grouped["is_correct"].apply(lambda s: int(s.notna().sum())).values

    # Sorting for readability
    sort_cols = [c for c in group_by if c in out.columns]
    out = out.sort_values(sort_cols).reset_index(drop=True)

    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run_dir", type=str, required=True, help="Root folder containing task subfolders"
    )
    parser.add_argument(
        "--dataset_fn", type=str, default=None, help="Optional filter (basename match)"
    )
    parser.add_argument(
        "--group_by",
        nargs="+",
        default=["task"],
        help="Grouping keys, e.g. task model conv_type",
    )
    parser.add_argument("--out_csv", type=str, default=None, help="Optional path to write CSV")
    args = parser.parse_args()

    # Map friendly names to actual columns
    key_map = {
        "task": "task",
        "model": "assistant_model",
        "assistant_model": "assistant_model",
        "conv_type": "conv_type",
        "dataset_fn": "dataset_fn",
    }
    group_by = [key_map.get(k, k) for k in args.group_by]

    records = iter_jsonl_records(args.run_dir)
    df = to_dataframe(records, dataset_fn=args.dataset_fn)

    if df.empty:
        print("No records found (or none matched dataset_fn filter).")
        return

    summary = aggregate_scores(df, group_by=group_by)

    # Print nicely
    with pd.option_context(
        "display.max_rows", 200, "display.max_columns", 200, "display.width", 200
    ):
        print(summary.to_string(index=False))

    if args.out_csv:
        Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.out_csv, index=False)
        print(f"\nWrote: {args.out_csv}")


if __name__ == "__main__":
    main()
