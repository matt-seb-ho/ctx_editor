"""
Score logs from a run directory of jsonl records.

Key features:
- Recursively loads *.jsonl under --run_dir
- Optional dataset_fn filter (basename match, consistent with utils_log.py)
- Optional keep-latest dedupe per (dataset_fn, task, task_id, conv_type, assistant_model)
- Group by arbitrary keys: task, model, conv_type, dataset_fn (or raw df columns)
- Produces:
    * avg_score_cond / accuracy_cond: mean over non-null score / is_correct (old behavior)
    * avg_score_all  / accuracy_all : mean over ALL rows, treating missing eval as 0 / False
    * n_missing_eval: rows where both score and is_correct are missing
    * n_mismatch_both_present: rows where both present but disagree (binary assumption)

Examples:
  python score_runs.py --run_dir logs
  python score_runs.py --run_dir logs --dataset_fn sharded_instructions_600.json --dedupe
  python score_runs.py --run_dir logs --dedupe --group_by task conv_type model --out_csv results.csv
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
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
                        # skip bad lines
                        continue
        except OSError:
            continue

    return records


def normalize_dataset_fn(dataset_fn: str) -> str:
    return os.path.basename(dataset_fn)


def extract_run_time(record: Dict[str, Any]) -> float:
    """
    Sortable numeric "run time" for dedupe:
    - prefer latest parseable timestamp in trace
    - fallback to source file mtime
    """
    trace = record.get("trace", None)
    if isinstance(trace, list) and trace:
        ts = []
        for msg in trace:
            if isinstance(msg, dict) and msg.get("timestamp"):
                ts.append(msg["timestamp"])
        if ts:
            parsed = pd.to_datetime(ts, errors="coerce", utc=True).dropna()
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
    for col in [
        "task",
        "task_id",
        "assistant_model",
        "conv_type",
        "dataset_fn",
        "score",
        "is_correct",
    ]:
        if col not in df.columns:
            df[col] = None

    # Unify task naming if needed
    if "task_name" in df.columns and df["task"].isna().all():
        df["task"] = df["task_name"]

    # Optional dataset filter (basename match)
    if dataset_fn is not None:
        target = normalize_dataset_fn(dataset_fn)
        df["dataset_fn"] = df["dataset_fn"].astype(str).map(os.path.basename)
        df = df[df["dataset_fn"] == target].copy()

    # Normalize numeric/bool
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["is_correct"] = df["is_correct"].map(to_bool_or_none)

    # "Has evaluation signal" (not necessarily "sim finished")
    df["has_eval_signal"] = (~df["score"].isna()) | (~df["is_correct"].isna())

    # For dedupe
    df["_run_time"] = df.apply(lambda r: extract_run_time(r.to_dict()), axis=1)

    # --- Canonicalization you asked for ---
    # Correctness:
    #   - if is_correct exists, trust it
    #   - else if score exists, correct iff score == 1.0 (>= 1.0 to tolerate float)
    #   - else (both missing), treat as failure
    df["correct_bool"] = np.where(
        df["is_correct"].notna(),
        df["is_correct"].astype(bool),
        np.where(df["score"].notna(), df["score"] >= 1.0, False),
    )

    # Canonical score for "all denom" averages:
    #   - if score exists, use it (supports partial credit)
    #   - elif is_correct exists, map True/False -> 1/0
    #   - else 0
    df["canonical_score"] = np.where(
        df["score"].notna(),
        df["score"].astype(float),
        np.where(df["is_correct"].notna(), df["is_correct"].astype(float), 0.0),
    )

    # Helpful diagnostics
    df["missing_eval"] = ~df["has_eval_signal"]  # both missing
    df["both_present"] = df["score"].notna() & df["is_correct"].notna()

    # For mismatch checking, assume binary score when comparing:
    # mismatch if both present and (is_correct != (score == 1))
    df["mismatch_both_present"] = df["both_present"] & (
        df["is_correct"].astype(bool) != (df["score"] >= 1.0)
    )

    return df


def dedupe_keep_latest(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
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
    g = df.groupby(group_by, dropna=False)

    out = g.agg(
        n_convs=("task_id", "count"),
        # Old behavior (conditional on non-null field)
        avg_score_cond=("score", mean_over_nonnull),
        accuracy_cond=("is_correct", mean_over_nonnull),
        n_with_score=("score", lambda s: int(s.notna().sum())),
        n_with_is_correct=("is_correct", lambda s: int(s.notna().sum())),
        # New behavior (ALL rows in denom; missing eval => 0 / False)
        avg_score_all=("canonical_score", "mean"),
        accuracy_all=("correct_bool", "mean"),
        # Diagnostics
        n_missing_eval=("missing_eval", lambda s: int(s.sum())),
        n_both_present=("both_present", lambda s: int(s.sum())),
        n_mismatch_both_present=("mismatch_both_present", lambda s: int(s.sum())),
    ).reset_index()

    # A couple derived columns that are useful to eyeball
    out["missing_eval_rate"] = out["n_missing_eval"] / out["n_convs"]
    out["mismatch_rate_among_both_present"] = np.where(
        out["n_both_present"] > 0,
        out["n_mismatch_both_present"] / out["n_both_present"],
        np.nan,
    )

    out = out.sort_values(group_by).reset_index(drop=True)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_dir", type=str, required=True)
    parser.add_argument("--dataset_fn", type=str, default=None)

    parser.add_argument(
        "--group_by",
        nargs="+",
        default=["task"],
        help="Grouping keys: task, model, conv_type, dataset_fn (or raw column names).",
    )

    parser.add_argument("--dedupe", action="store_true")
    parser.add_argument(
        "--dedupe_keys",
        nargs="+",
        default=["dataset_fn", "task", "task_id", "conv_type", "assistant_model"],
        help="Keys for keep-latest dedupe (column names; accepts 'model' alias).",
    )

    parser.add_argument("--out_csv", type=str, default=None)
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
        print("No records found (or none matched dataset_fn).")
        return

    if args.dedupe:
        before = len(df)
        df = dedupe_keep_latest(df, dedupe_keys)
        after = len(df)
        print(f"Dedupe keep-latest: {before} -> {after} rows")

    summary = aggregate(df, group_by=group_by)

    with pd.option_context(
        "display.max_rows", 200, "display.max_columns", 200, "display.width", 220
    ):
        print(summary.to_string(index=False))

    if args.out_csv:
        Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.out_csv, index=False)
        print(f"\nWrote: {args.out_csv}")


if __name__ == "__main__":
    main()
