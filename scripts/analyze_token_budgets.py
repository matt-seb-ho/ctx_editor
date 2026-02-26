#!/usr/bin/env python3
"""Analyze token counts for fully specified prompts + system prompts in t30_dp.json.

Outputs per-task stats (min, max, mean, median, p90) and overall stats.
Also writes a dev subset JSON with the longest-token example per task.

Usage:
    python scripts/analyze_token_budgets.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

import tiktoken

# Add project root to path so we can import lic
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lic.tasks import get_task

# Tokenizer (gpt-4o / o200k_base covers gpt-5-mini family too)
enc = tiktoken.encoding_for_model("gpt-4o")


def count_tokens(text: str) -> int:
    return len(enc.encode(text))


def main():
    data_file = PROJECT_ROOT / "data" / "t30_dp.json"
    with open(data_file) as f:
        samples = json.load(f)

    print(f"Loaded {len(samples)} samples from {data_file.name}\n")

    # Cache task instances
    task_cache = {}

    # Collect per-sample results
    results = []
    per_task = defaultdict(list)

    for sample in samples:
        task_name = sample["task"]
        if task_name not in task_cache:
            task_cache[task_name] = get_task(task_name)
        task = task_cache[task_name]

        full_prompt = task.populate_fully_specific_prompt(sample)
        system_prompt = task.generate_system_prompt(sample)

        prompt_tokens = count_tokens(full_prompt)
        system_tokens = count_tokens(system_prompt)
        total_tokens = prompt_tokens + system_tokens

        entry = {
            "task_id": sample["task_id"],
            "task": task_name,
            "prompt_tokens": prompt_tokens,
            "system_tokens": system_tokens,
            "total_tokens": total_tokens,
        }
        results.append(entry)
        per_task[task_name].append(entry)

    # Print per-task stats
    print("=" * 80)
    print(f"{'Task':<12} {'N':>4} {'Min':>6} {'Mean':>7} {'Median':>7} {'P90':>6} {'Max':>6}  "
          f"{'Sys Min':>7} {'Sys Max':>7}")
    print("-" * 80)

    overall_totals = []
    longest_per_task = {}

    for task_name in sorted(per_task.keys()):
        entries = per_task[task_name]
        totals = [e["total_tokens"] for e in entries]
        sys_tokens = [e["system_tokens"] for e in entries]
        overall_totals.extend(totals)

        sorted_totals = sorted(totals)
        p90_idx = int(len(sorted_totals) * 0.9)
        p90 = sorted_totals[min(p90_idx, len(sorted_totals) - 1)]

        print(
            f"{task_name:<12} {len(entries):>4} {min(totals):>6} {mean(totals):>7.0f} "
            f"{median(totals):>7.0f} {p90:>6} {max(totals):>6}  "
            f"{min(sys_tokens):>7} {max(sys_tokens):>7}"
        )

        # Track longest example per task
        longest = max(entries, key=lambda e: e["total_tokens"])
        longest_per_task[task_name] = longest["task_id"]

    # Overall stats
    sorted_all = sorted(overall_totals)
    p90_idx = int(len(sorted_all) * 0.9)
    p90 = sorted_all[min(p90_idx, len(sorted_all) - 1)]

    print("-" * 80)
    print(
        f"{'OVERALL':<12} {len(overall_totals):>4} {min(overall_totals):>6} "
        f"{mean(overall_totals):>7.0f} {median(overall_totals):>7.0f} "
        f"{p90:>6} {max(overall_totals):>6}"
    )
    print("=" * 80)

    # Budget recommendations
    avg = mean(overall_totals)
    mx = max(overall_totals)
    print(f"\nBudget recommendations (user prompt tokens only, excludes system prompt):")
    prompt_only = [e["prompt_tokens"] for e in results]
    avg_prompt = mean(prompt_only)
    max_prompt = max(prompt_only)
    med_prompt = median(prompt_only)

    print(f"  Prompt-only stats: avg={avg_prompt:.0f}, median={med_prompt:.0f}, max={max_prompt}")
    print(f"  1.5x avg prompt:  {int(avg_prompt * 1.5)}")
    print(f"  1.5x max prompt:  {int(max_prompt * 1.5)}")
    print(f"  2.0x avg prompt:  {int(avg_prompt * 2.0)}")

    # Per-task prompt-only recommendations
    print(f"\nPer-task prompt-only stats:")
    for task_name in sorted(per_task.keys()):
        entries = per_task[task_name]
        p_tokens = [e["prompt_tokens"] for e in entries]
        print(
            f"  {task_name:<12} avg={mean(p_tokens):>6.0f}  "
            f"median={median(p_tokens):>6.0f}  max={max(p_tokens):>5}"
        )

    # Write dev subset (longest per task)
    longest_ids = set(longest_per_task.values())
    dev_samples = [s for s in samples if s["task_id"] in longest_ids]

    # Sort by task name for consistency
    dev_samples.sort(key=lambda s: s["task"])

    dev_file = PROJECT_ROOT / "data" / "t30_dp_longest_per_task.json"
    with open(dev_file, "w") as f:
        json.dump(dev_samples, f, indent=2)

    print(f"\nWrote dev subset ({len(dev_samples)} samples) to {dev_file.name}:")
    for task_name, task_id in sorted(longest_per_task.items()):
        entry = next(e for e in results if e["task_id"] == task_id)
        print(f"  {task_name:<12} {task_id}  ({entry['total_tokens']} total tokens)")


if __name__ == "__main__":
    main()
