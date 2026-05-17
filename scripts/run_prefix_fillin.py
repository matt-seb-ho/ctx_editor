"""Run additional vanilla-sharded ctx-editor passes targeted at problems that
don't yet have 3 valid prefixes (per the valid_prefix_tally.json sidecar).

For each (model, task) cell with short problems, this script:
  1. Builds a temporary data file containing only the short problems.
  2. Invokes ctx-editor with the existing baseline config, pointing
     task.data_file at the temp file. Uses a unique logging.output_dir.
  3. Runs N additional passes (default 1). After all passes finish, re-run
     scripts/tally_valid_prefixes.py to see how the gap shrank.

Foundry-side models share one rate-limit bucket per model. To stay below
the 250-RPM cap during fast LiC turns, we serialize foundry model runs
across the four pipelines (one model at a time). gpt-5.4 runs in parallel
since it has its own endpoint pool.

Usage:
    python scripts/run_prefix_fillin.py            # one extra pass per cell
    python scripts/run_prefix_fillin.py --passes 2 # two extra passes per cell
    python scripts/run_prefix_fillin.py --user-model deepseek-v4-flash-foundry
                                                    # switch user-sim model
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TALLY_PATH = PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla" / "valid_prefix_tally.json"

# Map model_key (as used in tally) to (model config, load balancer, max_concurrent).
MODELS = {
    "gpt5_4":                    ("gpt5_4",                    "multi_endpoint",         20),
    "deepseek_v4_flash_foundry": ("deepseek_v4_flash_foundry", "multi_endpoint_foundry", 8),
    "kimi_k2_6_foundry":         ("kimi_k2_6_foundry",         "multi_endpoint_foundry", 6),
    "gpt5_5_foundry":            ("gpt5_5_foundry",            "multi_endpoint_foundry", 8),
}

TASK_TO_BASE_DATA = {
    "math_v2":     "data/htn50_52_math_subset.json",
    "code_v2":     "data/htn50_52_code_subset.json",
    "database_v2": "data/htn50_52_database_subset.json",
    "actions_v2": "data/htn50_52_actions_subset.json",
}

RUN_TAG = "post_neurips_lic_vanilla_fillin"
TEMP_DATA_DIR = PROJECT_ROOT / "outputs" / RUN_TAG / "subsets"
LOG_DIR = PROJECT_ROOT / "outputs" / RUN_TAG / "logs"
TEMP_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_tally():
    with TALLY_PATH.open() as f:
        return json.load(f)


def build_subset(task_cfg: str, sample_ids: list[str], suffix: str) -> Path:
    """Create a temporary JSON data file containing only the requested samples."""
    base_path = PROJECT_ROOT / TASK_TO_BASE_DATA[task_cfg]
    with base_path.open() as f:
        all_samples = json.load(f)
    keep = {s for s in sample_ids}
    sub = [s for s in all_samples if s.get("task_id") in keep]
    if len(sub) != len(keep):
        missing = keep - {s.get("task_id") for s in sub}
        print(f"  WARNING: {len(missing)} requested samples missing from base: {sorted(missing)[:3]}…", file=sys.stderr)
    out_path = TEMP_DATA_DIR / f"{task_cfg}__{suffix}.json"
    out_path.write_text(json.dumps(sub, indent=2))
    return out_path


def launch_one(model_key: str, task_cfg: str, data_file: Path, pass_idx: int,
               user_model_override: str | None) -> dict:
    model_cfg, lb, mc = MODELS[model_key]
    label = f"fillin_p{pass_idx}__{model_key}__{task_cfg}"
    logfile = LOG_DIR / f"{label}.log"
    start_ts = int(time.time())
    exp_name = f"baseline_sharded_{model_key}_{task_cfg}_fillin{pass_idx}_{start_ts}"
    out_override = f"outputs/{RUN_TAG}/{exp_name}"

    cmd = [
        "ctx-editor",
        "experiment=baseline",
        f"model={model_cfg}",
        f"task={task_cfg}",
        f"task.data_file={data_file.relative_to(PROJECT_ROOT)}",
        "user_mode=sharded",
        f"load_balancer={lb}",
        f"execution.max_concurrent={mc}",
        f"experiment_name={exp_name}",
        f"logging.output_dir={out_override}",
        "logging.verbose=false",
        f"metadata.branch={RUN_TAG}",
    ]
    if user_model_override:
        cmd.append(f"model.user.model={user_model_override}")

    print(f"[{time.strftime('%H:%M:%S')}] BEGIN {label} ({len(json.loads(data_file.read_text()))} samples, mc={mc})")
    with logfile.open("w") as f:
        rc = subprocess.run(cmd, cwd=PROJECT_ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    elapsed = int(time.time()) - start_ts
    print(f"[{time.strftime('%H:%M:%S')}] DONE  {label} (rc={rc}, {elapsed}s) → {out_override}")
    return {"label": label, "rc": rc, "out_dir": out_override, "elapsed": elapsed}


async def main_async(args):
    tally = load_tally()
    per = tally["per_model_task"]

    # Build the work list grouped by model: each model's tasks are run sequentially
    # within that model's pipeline. Pipelines for different models run in parallel
    # (different rate buckets, except for the three foundry models which share an
    # endpoint — those we serialize).
    by_model = {m: [] for m in MODELS}
    for key, v in per.items():
        try:
            model_key, task_cfg = key.split("__")
        except ValueError:
            continue
        if model_key not in MODELS:
            continue
        needs = [p for p in v["needs_more"] if p["valid_now"] < 3]
        if not needs:
            continue
        sample_ids = [p["sample_id"] for p in needs]
        by_model[model_key].append((task_cfg, sample_ids))

    print("=== fill-in plan ===")
    for m, items in by_model.items():
        for t, ids in items:
            print(f"  {m:30s} {t:12s} {len(ids)} problems short")

    if args.dry_run:
        return

    # For each model, materialize subset files first.
    work = {}
    for m, items in by_model.items():
        ws = []
        for t, ids in items:
            for pi in range(1, args.passes + 1):
                p = build_subset(t, ids, f"{m}_pass{pi}")
                ws.append((t, p, pi))
        work[m] = ws

    # Launchers as coroutines that each call subprocess in a thread.
    def pipeline_for(model_key):
        for (task_cfg, data_path, pass_idx) in work[model_key]:
            launch_one(model_key, task_cfg, data_path, pass_idx, args.user_model)

    # We want gpt5_4 in parallel with a serialized chain of the three foundry models.
    loop = asyncio.get_running_loop()
    pa = loop.run_in_executor(None, pipeline_for, "gpt5_4")
    async def foundry_chain():
        for model_key in ("deepseek_v4_flash_foundry", "kimi_k2_6_foundry", "gpt5_5_foundry"):
            await loop.run_in_executor(None, pipeline_for, model_key)
    pb = foundry_chain()
    await asyncio.gather(pa, pb)
    print("All fill-in passes done.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passes", type=int, default=1)
    parser.add_argument("--user-model", default=None,
                        help="Override the user-sim model (e.g. 'DeepSeek-V4-Flash').")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
