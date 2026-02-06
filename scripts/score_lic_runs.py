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
    Prefers the latest timestamp in trace, else falls back to source file mtime.
    """
    # Your date_str() format is unknown here; pandas can parse many formats.
    trace = record.get("trace", None)
    if isinstance(trace, list) and trace:
        ts = []
        for msg in trace:
            t = msg.get("timestamp")
            if t:
                ts.append(t)
        if ts:
            parsed = pd.to_datetime(ts, errors="coerce", utc=True)
            parsed = parsed.dropna()
            if len(parsed):
                return float(parsed.max().timestamp())
    return float(record.get("_source_mtime", 0.0))


def to_dataframe(records: List[Dict[str, Any]], dataset_fn: Optional[str] = None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Ensure columns
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

    if "task_name" in df.columns and df["task"].isna().all():
        df["task"] = df["task_name"]

    if dataset_fn is not None:
        target = normalize_dataset_fn(dataset_fn)
        df["dataset_fn"] = df["dataset_fn"].astype(str).map(os.path.basename)
        df = df[df["dataset_fn"] == target].copy()

    df["score"] = pd.to_numeric(df["score"], errors="coerce")

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

    # Run time used for dedupe
    df["_run_time"] = df.apply(lambda r: extract_run_time(r.to_dict()), axis=1)

    return df


def dedupe_keep_latest(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    """
    Keep latest run per group defined by `keys`.
    """
    missing = [k for k in keys if k not in df.columns]
    if missing:
        raise ValueError(f"Missing dedupe keys in df: {missing}")

    # Sort by run time so tail(1) is latest
    df2 = df.sort_values("_run_time")
    latest = df2.groupby(keys, dropna=False, as_index=False).tail(1)
    return latest.reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--dataset_fn", default=None)
    ap.add_argument(
        "--dedupe",
        action="store_true",
        help="If set, dedupe and keep latest per (dataset_fn, task, task_id, conv_type, assistant_model).",
    )
    ap.add_argument("--out_csv", default=None)
    args = ap.parse_args()

    records = iter_jsonl_records(args.run_dir)
    df = to_dataframe(records, dataset_fn=args.dataset_fn)

    if df.empty:
        print("No records found.")
        return

    if args.dedupe:
        dedupe_keys = ["dataset_fn", "task", "task_id", "conv_type", "assistant_model"]
        before = len(df)
        df = dedupe_keep_latest(df, dedupe_keys)
        after = len(df)
        print(f"Dedupe keep-latest: {before} -> {after} rows")

    # Example: per-task aggregate after dedupe
    summary = (
        df.groupby(["task"], dropna=False)
        .agg(
            n=("task_id", "count"),
            avg_score=("score", "mean"),
            accuracy=(
                "is_correct",
                lambda s: s.dropna().mean() if len(s.dropna()) else float("nan"),
            ),
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    if args.out_csv:
        Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(args.out_csv, index=False)
        print(f"Wrote {args.out_csv}")


if __name__ == "__main__":
    main()
