"""T18 — close T17's ERGO intervals with the measured pruned-item split.

REUSES T17's build_corrected.py (runpy-exec, so PUB / POOL / D / GATED / pct come
from that file and are not restated here). The only thing T18 adds is the measured
value of `k` = how many of the pruned items ERGO actually solves, which is the sole
free parameter in T17's `kind == "pool"` branch.

k is measured by replaying ERGO against a pool containing ONLY the pruned items
(neurips_review/autoresearch/tasks/T18/pruned_pools/, which deliberately carries no
false_negatives.json sidecar so the filter cannot fire).

CAVEAT, load-bearing: k is measured under gpt-5.4-mini_2026-03-17 on TRAPI, whereas
the published row is gpt-5-mini. gpt-5-mini is unreachable (dl-openai-3 -> 401). So k
transfers as evidence, not as identity. The transfer is defended in worklog.md §"k
transfer"; the short version is that Baseline solves 0/6 of the pruned code items even
at the newer model, so the 3 solvable ones are a context effect, not a model-era effect.
"""
import runpy, json
from fractions import Fraction

T17 = "/home/t-matthewho/ac3/ctx_editor/neurips_review/autoresearch/tasks/T17/build_corrected.py"
ns = runpy.run_path(T17)          # also re-emits T17's own table + corrected_tabmain.json
POOL, D, TASKS, pct, PUB = ns["POOL"], ns["D"], ns["TASKS"], ns["pct"], ns["PUB"]

# ---------------------------------------------------------------- measured k
# ERGO on the pruned-items-only pool, replicate runs at temperature 1.0
# (`seed=` is inert on the LiC harness -- run_experiment.py never reads cfg.seed).
K_RUNS = {
    "math": [0, 0, 0],          # of 3 pruned  (3 ERGO reps; Concat User also 0/3)
    "code": [3, 2, 3],          # of 6 pruned  (3 ERGO reps; Concat 3/6, AC3-Reset 2/6, Baseline 0/6)
    "database": [],             # nothing pruned
    "actions": None,            # NO sidecar exists; the 2 excluded ids are unidentified -> unclosable
}

ERGO_NUM = {t: PUB["ERGO"][t][0] for t in TASKS}     # 16, 11, 3, 12
ERGO_KIND = {t: PUB["ERGO"][t][2] for t in TASKS}

print("\n\n" + "=" * 78)
print("T18 — ERGO row with the pruned-item split MEASURED")
print("=" * 78)
print(f"{'task':10s} {'published':>12s} {'T17 pt':>8s} {'T17 interval':>16s} "
      f"{'k (meas.)':>11s} {'T18 pt':>8s} {'T18 interval':>16s}")
out = {}
for t in TASKS:
    n, d, kind = PUB["ERGO"][t]
    pub = pct(n, d)
    if kind == "ok":                                   # database: nothing pruned
        print(f"{t:10s} {pub:12.1f} {pub:8.1f} {'exact':>16s} {'n/a':>11s} {pub:8.1f} {'exact':>16s}")
        out[t] = dict(published=pub, t18=pub, lo=pub, hi=pub, k=None, closed=True)
        continue
    kmax = POOL[t][1]
    t17_hi, t17_lo = pct(n, D[t]), pct(max(n - kmax, 0), D[t])
    runs = K_RUNS[t]
    if runs is None:                                   # actions
        print(f"{t:10s} {pub:12.1f} {t17_hi:8.1f} {f'[{t17_lo}, {t17_hi}]':>16s} "
              f"{'UNMEASURABLE':>11s} {'--':>8s} {f'[{t17_lo}, {t17_hi}]':>16s}")
        out[t] = dict(published=pub, t18=None, lo=t17_lo, hi=t17_hi, k=None, closed=False)
        continue
    klo, khi = min(runs), max(runs)
    kbar = sum(runs) / len(runs)
    pt = round(100.0 * (n - kbar) / D[t], 1)
    lo, hi = pct(n - khi, D[t]), pct(n - klo, D[t])
    print(f"{t:10s} {pub:12.1f} {t17_hi:8.1f} {f'[{t17_lo}, {t17_hi}]':>16s} "
          f"{f'{kbar:.2f}/{kmax}':>11s} {pt:8.1f} {f'[{lo}, {hi}]':>16s}")
    out[t] = dict(published=pub, t18=pt, lo=lo, hi=hi, k=kbar, kruns=runs, closed=True)

print("\nERGO row, published -> T17 point estimate -> T18 measured:")
print("  math     69.6 -> 80.0 -> 80.0   CLOSED, T17 confirmed (k=0, 3/3 reps)")
print("  code     44.0 -> 57.9 -> 43.9   T17's k=0 REFUTED (k=2.67/6); ERGO moves DOWN, not up")
print("  database 12.0 -> 12.0 -> 12.0   exact, untouched")
print("  actions  48.0 -> 52.2 ->  --    UNCLOSABLE: no sidecar, excluded ids unidentified")

# ------------------------------------------------- ordering vs the AC3 operators
AC3 = {  # T17 corrected values, unchanged by T18
    "AC3-Augment":     {"math": 80.0, "code": 52.6, "database": 32.0, "actions": 47.8},
    "AC3-Reset":       {"math": 75.0, "code": 57.9, "database": 48.0, "actions": 52.2},
    "AC3-Gated-Reset": {"math": 80.0, "code": 63.2, "database": 38.7, "actions": 66.7},
}
print("\nERGO vs the no-memory AC3 operators, on uniform pools (pp, + = ERGO ahead)")
print(f"{'':18s}" + "".join(f"{t:>26s}" for t in TASKS))
for name, cells in AC3.items():
    parts = []
    for t in TASKS:
        e = out[t]["t18"]
        if e is None:                    # actions: report the interval
            lo, hi = out[t]["lo"] - cells[t], out[t]["hi"] - cells[t]
            parts.append(f"[{lo:+.1f},{hi:+.1f}] vs {cells[t]:.1f}".rjust(26))
        else:
            parts.append(f"{e - cells[t]:+6.1f}  ({e:.1f} vs {cells[t]:.1f})".rjust(26))
    print(f"{name:18s}" + "".join(parts))

json.dump(out, open("/home/t-matthewho/ac3/ctx_editor/neurips_review/autoresearch/"
                    "tasks/T18/ergo_row_closed.json", "w"), indent=2)
