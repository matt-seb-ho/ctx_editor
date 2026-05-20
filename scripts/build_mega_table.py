"""Assemble the model × benchmark × method mega table from all
known output directories.

Coverage scanned:
- LiC: Phase 1 (DeepSeek), Phase 2 (gpt-5.4, Kimi), R3 (gpt-5.4 Rewrite,
  Kimi Rewrite-retry).
- CollabLLM: Phase 3a (DeepSeek + gpt-4o-mini user), R2 (DeepSeek +
  DeepSeek user), R3 (gpt-5.4 + Kimi with DeepSeek user).
- WildChat (Huang): Phase 3b (gpt-5-mini), R2 (Kimi + DeepSeek), R3
  (Rewrite/s3 on all three).
- tau2: deferred.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

OUTS = Path("/home/v-homatthew/ctx_editor/outputs")
OUT_PATH = Path("/home/v-homatthew/ctx_editor/docs/reports/post_may18_r3_mega_table.md")

# --- LiC + CollabLLM cell discovery ---

# (root_dir, regex, variant_label, model_label, benchmark, task_subkey?)
LIC_DIRS = [
    ("post_neurips_ac3_phase1", r"^baseline_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Baseline", "DeepSeek", "LiC"),
    ("post_neurips_ac3_phase1", r"^omit_assistant_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "AO", "DeepSeek", "LiC"),
    ("post_neurips_ac3_phase1", r"^append_analysis_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Augment", "DeepSeek", "LiC"),
    ("post_neurips_ac3_phase1", r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Reset", "DeepSeek", "LiC"),
    ("post_neurips_ac3_phase1", r"^context_edit_v2_gated(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Gated-Reset", "DeepSeek", "LiC"),
    ("post_neurips_ac3_phase1", r"^ac3_rewrite_lic_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Rewrite", "DeepSeek", "LiC"),

    ("post_neurips_ac3_phase2/gpt5_4", r"^baseline_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Baseline", "gpt-5.4", "LiC"),
    ("post_neurips_ac3_phase2/gpt5_4", r"^omit_assistant_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "AO", "gpt-5.4", "LiC"),
    ("post_neurips_ac3_phase2/gpt5_4", r"^append_analysis_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Augment", "gpt-5.4", "LiC"),
    ("post_neurips_ac3_phase2/gpt5_4", r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Reset", "gpt-5.4", "LiC"),

    ("post_neurips_ac3_phase2/kimi_k2_6_foundry", r"^baseline_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Baseline", "Kimi-K2.6", "LiC"),
    ("post_neurips_ac3_phase2/kimi_k2_6_foundry", r"^omit_assistant_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "AO", "Kimi-K2.6", "LiC"),
    ("post_neurips_ac3_phase2/kimi_k2_6_foundry", r"^append_analysis_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Augment", "Kimi-K2.6", "LiC"),
    ("post_neurips_ac3_phase2/kimi_k2_6_foundry", r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Reset", "Kimi-K2.6", "LiC"),

    ("post_may18_r3_lic_rewrite_fills", r"^ac3_rewrite_lic_gpt5_4_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Rewrite", "gpt-5.4", "LiC"),
    ("post_may18_r3_lic_rewrite_kimi_retry", r"^ac3_rewrite_lic_kimi_k2_6_foundry_(?P<task>[a-z_]+)_v2_conv\d+_\d+$", "Rewrite", "Kimi-K2.6", "LiC"),
]

COLLAB_DIRS = [
    # CollabLLM Phase 3a (gpt-4o-mini user-sim, less interesting)
    # R2 (DeepSeek user-sim) — DeepSeek assistant
    ("post_neurips_r2_collabllm_user_deepseek", r"^collabllm_baseline_(?P<task>math-hard|bigcodebench)_rep\d+_\d+$", "Baseline", "DeepSeek", "CollabLLM"),
    ("post_neurips_r2_collabllm_user_deepseek", r"^collabllm_assistant_omit_(?P<task>math-hard|bigcodebench)_rep\d+_\d+$", "AO", "DeepSeek", "CollabLLM"),
    ("post_neurips_r2_collabllm_user_deepseek", r"^collabllm_ac3_augment_v8_(?P<task>math-hard|bigcodebench)_rep\d+_\d+$", "Augment", "DeepSeek", "CollabLLM"),
    ("post_neurips_r2_collabllm_user_deepseek", r"^collabllm_ac3_reset_v8_(?P<task>math-hard|bigcodebench)_rep\d+_\d+$", "Reset", "DeepSeek", "CollabLLM"),
    # R3 — gpt-5.4 + Kimi
    ("post_may18_r3_collabllm_fills", r"^collabllm_baseline_gpt5_4_(?P<task>math-hard|bigcodebench)_\d+$", "Baseline", "gpt-5.4", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_assistant_omit_gpt5_4_(?P<task>math-hard|bigcodebench)_\d+$", "AO", "gpt-5.4", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_ac3_augment_v8_gpt5_4_(?P<task>math-hard|bigcodebench)_\d+$", "Augment", "gpt-5.4", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_ac3_reset_v8_gpt5_4_(?P<task>math-hard|bigcodebench)_\d+$", "Reset", "gpt-5.4", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_baseline_kimi_k2_6_(?P<task>math-hard|bigcodebench)_\d+$", "Baseline", "Kimi-K2.6", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_assistant_omit_kimi_k2_6_(?P<task>math-hard|bigcodebench)_\d+$", "AO", "Kimi-K2.6", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_ac3_augment_v8_kimi_k2_6_(?P<task>math-hard|bigcodebench)_\d+$", "Augment", "Kimi-K2.6", "CollabLLM"),
    ("post_may18_r3_collabllm_fills", r"^collabllm_ac3_reset_v8_kimi_k2_6_(?P<task>math-hard|bigcodebench)_\d+$", "Reset", "Kimi-K2.6", "CollabLLM"),
    # CollabLLM Rewrite (compaction) on DeepSeek — R3 fill-in
    ("post_may18_r3_collabllm_fills", r"^collabllm_compaction_deepseek_(?P<task>math-hard|bigcodebench)_\d+$", "Rewrite", "DeepSeek", "CollabLLM"),
]


def collect_cells(specs):
    cells = []
    for root, pat_str, variant, model, bench in specs:
        pat = re.compile(pat_str)
        root_path = OUTS / root
        if not root_path.exists():
            continue
        for d in sorted(root_path.iterdir()):
            if not d.is_dir():
                continue
            m = pat.match(d.name)
            if not m:
                continue
            rfile = d / "results.json"
            if not rfile.exists():
                continue
            rows = json.load(open(rfile))
            n_total = len(rows)
            n_correct = sum(1 for r in rows if r.get("is_correct"))
            n_evaluated = sum(1 for r in rows if r.get("num_turns", 0) > 0)
            cells.append({
                "bench": bench, "model": model, "variant": variant,
                "task": m.group("task"),
                "n_total": n_total, "n_correct": n_correct,
                "n_evaluated": n_evaluated,
                "out": str(d),
            })
    return cells


# --- WildChat (Huang) — win-rate based ---

HUANG_DIRS = [
    # Phase 3b — gpt-5-mini
    ("post_neurips_ac3_phase3_huang", "gpt-5-mini"),
    # R2 — Kimi + DeepSeek
    ("post_neurips_r2_huang_models", "auto"),  # extract model from dir name
    # R3 — gpt-5-mini + DeepSeek + Kimi (variant s3 + Kimi augment)
    ("post_may18_r3_wildchat_fills", "auto"),
]


def collect_huang_cells():
    cells = []
    # (variant_token, label_short)
    VARIANT_HINTS = [("s15", "Reset"), ("s3", "Rewrite"), ("augment", "Augment"), ("s2", "Gated-Reset")]

    for root, model_hint in HUANG_DIRS:
        root_path = OUTS / root
        if not root_path.exists():
            continue
        for d in sorted(root_path.iterdir()):
            if not d.is_dir():
                continue
            name = d.name
            variant = None
            for token, label in VARIANT_HINTS:
                # token at the start or after underscore
                if name.startswith(token + "_") or f"_{token}_" in name:
                    variant = label
                    break
            if variant is None:
                continue
            # model
            if model_hint != "auto":
                model = model_hint
            else:
                # parse from name (e.g. s15_Kimi_K2_6_seed42_..., s3_DeepSeek_V4_Flash_seed42_..., augment_Kimi_K2_6_seed42_...)
                model_part = re.sub(r"^(s15|s3|augment|s2)_", "", name)
                model_part = re.split(r"_seed\d+_", model_part)[0]
                model_map = {"Kimi_K2_6": "Kimi-K2.6", "DeepSeek_V4_Flash": "DeepSeek", "gpt_5_mini": "gpt-5-mini"}
                model = model_map.get(model_part, model_part)
            # Parse metrics
            metrics_path = d / "metrics.json"
            if not metrics_path.exists():
                continue
            try:
                rows = [json.loads(l) for l in (d / "turn_results.jsonl").open()]
            except FileNotFoundError:
                continue
            if not rows:
                continue
            # Find judgment key matching variant token
            cmp_key = None
            for k in rows[0].get("judgments", {}):
                if k.startswith("ao_vs_") and k.endswith(("_s15", "_s3", "_augment", "_s2")):
                    cmp_key = k
                    break
            if not cmp_key:
                continue
            variant_label = cmp_key.split("_vs_")[1]
            wins = sum(1 for r in rows if r.get("judgments", {}).get(cmp_key, {}).get("quality_winner") == variant_label)
            total = sum(1 for r in rows if r.get("judgments", {}).get(cmp_key, {}).get("quality_winner"))
            if total == 0:
                continue
            cells.append({
                "bench": "WildChat (win-rate vs AO, quality)",
                "model": model, "variant": variant,
                "task": "—",
                "n_total": total,
                "n_correct": wins,
                "n_evaluated": total,
                "out": str(d),
            })
    return cells


def render(cells, render_huang_cells):
    md = ["# Post-NeurIPS Mega Table (R3 snapshot)\n",
          "Model × benchmark × method matrix across LiC / CollabLLM / WildChat.",
          "All numbers below are accuracy% (LiC, CollabLLM) or s15/s3/augment **wins vs AO** quality% (WildChat).",
          "Cells without a value have not been run yet.\n"]

    # LiC + CollabLLM accuracy table
    benches = ["LiC", "CollabLLM"]
    variants_order = ["Baseline", "AO", "Augment", "Reset", "Gated-Reset", "Rewrite"]

    for bench in benches:
        bcells = [c for c in cells if c["bench"] == bench]
        if not bcells:
            continue
        # Aggregate across task replicates (conv0/1/2 etc.) within a (model, variant, task) cell
        agg: dict = defaultdict(lambda: [0, 0])  # (model, variant, task) -> [correct, eval]
        models_seen = set()
        tasks_seen = set()
        for c in bcells:
            key = (c["model"], c["variant"], c["task"])
            agg[key][0] += c["n_correct"]
            agg[key][1] += c["n_evaluated"]
            models_seen.add(c["model"])
            tasks_seen.add(c["task"])
        # Order
        if bench == "LiC":
            tasks = ["math", "code", "database", "actions"]
            models = ["DeepSeek", "gpt-5.4", "Kimi-K2.6"]
        else:  # CollabLLM
            tasks = ["math-hard", "bigcodebench"]
            models = ["DeepSeek", "gpt-5.4", "Kimi-K2.6"]
        # Filter to seen
        tasks = [t for t in tasks if t in tasks_seen]
        models = [m for m in models if m in models_seen]
        md.append(f"\n## {bench}\n")
        # One sub-table per task
        for task in tasks:
            md.append(f"\n### {bench} / {task}\n")
            md.append("| Variant | " + " | ".join(models) + " |")
            md.append("|---|" + "---|" * len(models))
            for v in variants_order:
                row = [f"**{v}**"]
                for m in models:
                    cc, ne = agg.get((m, v, task), [None, None])
                    if cc is None or ne is None or ne == 0:
                        row.append("—")
                    else:
                        row.append(f"{cc/ne*100:.1f}% (n={ne})")
                md.append("| " + " | ".join(row) + " |")
            md.append("")

    # WildChat win-rate table
    if render_huang_cells:
        md.append("\n## WildChat (Huang) — wins vs AO on quality\n")
        agg: dict = defaultdict(lambda: [0, 0])
        for c in render_huang_cells:
            key = (c["model"], c["variant"])
            agg[key][0] += c["n_correct"]
            agg[key][1] += c["n_evaluated"]
        wildchat_variants = ["Reset", "Augment", "Rewrite", "Gated-Reset"]
        wildchat_models = ["gpt-5-mini", "DeepSeek", "Kimi-K2.6"]
        md.append("| Variant | " + " | ".join(wildchat_models) + " |")
        md.append("|---|" + "---|" * len(wildchat_models))
        for v in wildchat_variants:
            row = [f"**{v}**"]
            for m in wildchat_models:
                cc, ne = agg.get((m, v), [None, None])
                if cc is None or ne is None or ne == 0:
                    row.append("—")
                else:
                    row.append(f"{cc/ne*100:.1f}% (n={ne})")
            md.append("| " + " | ".join(row) + " |")
        md.append("")
    return "\n".join(md)


def main():
    lic_collab_cells = collect_cells(LIC_DIRS + COLLAB_DIRS)
    huang_cells = collect_huang_cells()
    text = render(lic_collab_cells, huang_cells)
    OUT_PATH.write_text(text)
    print(text)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
