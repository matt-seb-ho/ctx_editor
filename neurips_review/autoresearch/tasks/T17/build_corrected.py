"""T17 — rebuild tab:main on uniform, pool-filtered denominators.

Zero API calls. Inputs are (a) the published percentages in
writing/overleaf_repo/neurips/neurips_2026_conference.tex, (b) the
numerator/denominator pairs recovered for each cell from source documents and
from exact rational reconstruction, (c) the pool-filter sidecars in
data/baseline_traces_v2/.

Correct (uniform) denominators = |pool| - |user_sim_induced_ids|:
    math 23-3=20 · code 25-6=19 · database 25-0=25 · actions 25-2=23
"""
import json
from fractions import Fraction

POOL = {"math": (23, 3), "code": (25, 6), "database": (25, 0), "actions": (25, 2)}
D = {t: n - k for t, (n, k) in POOL.items()}          # 20, 19, 25, 23
TASKS = ["math", "code", "database", "actions"]

def pct(n, d):
    return round(100.0 * n / d, 1)

# ---------------------------------------------------------------- published
# (numerator, denominator_used, kind)
#   kind "ok"    denominator already == D[task]
#   kind "pool"  denominator is the UNFILTERED pool -> pruned items were scored
#   kind "sub"   denominator is BELOW D[task] (1 item dropped post hoc)
PUB = {
 "Baseline (full context)":  {"math":(12,20,"ok"), "code":(3,19,"ok"),  "database":(1,25,"ok"),  "actions":(8,23,"ok")},
 "\\quad + Memory":          {"math":(11,20,"ok"), "code":(4,19,"ok"),  "database":(1,25,"ok"),  "actions":(8,23,"ok")},
 "AO":                       {"math":(17,20,"ok"), "code":(14,18,"sub"),"database":(8,25,"ok"),  "actions":(19,23,"ok")},
 "Concat User":              {"math":(16,19,"sub"),"code":(13,19,"ok"), "database":(8,25,"ok"),  "actions":(20,23,"ok")},
 "ERGO":                     {"math":(16,23,"pool"),"code":(11,25,"pool"),"database":(3,25,"ok"),"actions":(12,25,"pool")},
 "AC3-Augment":              {"math":(16,20,"ok"), "code":(10,18,"sub"),"database":(8,25,"ok"),  "actions":(11,23,"ok")},
 "\\quad + Memory (Augment)":{"math":(18,20,"ok"), "code":(13,19,"ok"), "database":(11,25,"ok"), "actions":(11,23,"ok")},
 "AC3-Reset":                {"math":(15,20,"ok"), "code":(11,18,"sub"),"database":(12,25,"ok"), "actions":(12,23,"ok")},
 "\\quad + Memory (Reset)":  {"math":(17,20,"ok"), "code":(13,19,"ok"), "database":(11,25,"ok"), "actions":(12,23,"ok")},
}
# Gated-Reset is a mean over N=3; per-run n/d read off tex:496-504.
GATED = {"math":[(15,20),(16,20),(17,20)],
         "code":[(13,18),(12,19),(11,19)],
         "database":[(11,25),(8,25),(10,25)],
         "actions":[(17,25),(14,25),(15,25)]}

def cell_published(n, d):
    return pct(n, d)

def cell_corrected(n, d, kind, task):
    """Return (point_estimate, lo, hi). Point estimate uses k=0 (pruned items
    were failures for this arm), which is the assumption the pool filter itself
    encodes and the only case we can observe empirically (Gated-Reset actions
    headline run: 17/25 raw == 17/23 filtered)."""
    Dt = D[task]
    if kind == "ok":
        v = pct(n, Dt); return v, v, v
    if kind == "pool":
        k = POOL[task][1]                       # number of pruned items scored
        hi = pct(n, Dt)                         # k=0  : none of them were solved
        lo = pct(max(n - k, 0), Dt)             # k=max: all of them were solved
        return hi, lo, hi
    if kind == "sub":
        # one item was dropped from the denominator post hoc. Restoring it as a
        # failure gives n/Dt; if the drop was a genuine harness error the cell
        # legitimately stays where it is.
        return pct(n, Dt), pct(n, Dt), pct(n, d)
    raise ValueError(kind)

rows = []
for name, cells in PUB.items():
    pubs, cors, los, his, kinds = {}, {}, {}, {}, {}
    for t in TASKS:
        n, d, kind = cells[t]
        pubs[t] = cell_published(n, d)
        c, lo, hi = cell_corrected(n, d, kind, t)
        cors[t], los[t], his[t], kinds[t] = c, lo, hi, kind
    rows.append((name, pubs, cors, los, his, kinds, cells))

# Gated-Reset row
g_pub, g_cor, g_lo, g_hi, g_kind, g_cells = {}, {}, {}, {}, {}, {}
for t in TASKS:
    runs = GATED[t]
    g_pub[t] = round(sum(pct(n, d) for n, d in runs) / 3, 1)
    Dt = D[t]
    hi = round(sum(pct(n, Dt) for n, _ in runs) / 3, 1)
    k = POOL[t][1] if any(d != Dt for _, d in runs) and t == "actions" else 0
    if t == "actions":
        lo = round(sum(pct(max(n - 2, 0), Dt) for n, _ in runs) / 3, 1)
        kind = "pool"
    elif t == "code":
        lo = hi; kind = "sub"          # run1 used n=18 (one item dropped)
    else:
        lo = hi; kind = "ok"
    g_cor[t], g_lo[t], g_hi[t], g_kind[t] = hi, lo, hi, kind
    g_cells[t] = (sum(n for n, _ in runs), 3 * runs[0][1], kind)
rows.append(("AC3-Gated-Reset", g_pub, g_cor, g_lo, g_hi, g_kind, g_cells))

MARK = {"ok": "", "pool": "*", "sub": "†"}
print("PUBLISHED vs CORRECTED (uniform n = 20/19/25/23)\n")
hdr = f"{'Strategy':26s} " + " ".join(f"{t:>22s}" for t in TASKS)
print(hdr); print("-" * len(hdr))
for name, pubs, cors, los, his, kinds, cells in rows:
    parts = []
    for t in TASKS:
        d = cors[t] - pubs[t]
        s = f"{pubs[t]:5.1f}->{cors[t]:5.1f} ({d:+5.1f}){MARK[kinds[t]]}"
        parts.append(f"{s:>22s}")
    print(f"{name.replace(chr(92)+'quad ',''):26s} " + " ".join(parts))
print("\n* pruned items were scored against ERGO/Gated-actions; point estimate assumes")
print("  they were failures for that arm (k=0). Interval below.")
print("† one item dropped post hoc from a 19- or 20-denominator cell.\n")
print("INTERVALS on the * and † cells")
for name, pubs, cors, los, his, kinds, cells in rows:
    for t in TASKS:
        if kinds[t] != "ok":
            print(f"  {name.replace(chr(92)+'quad ',''):22s} {t:9s} published {pubs[t]:5.1f}   corrected [{los[t]:5.1f}, {his[t]:5.1f}]")
json.dump({r[0]: {"published": r[1], "corrected": r[2], "lo": r[3], "hi": r[4], "kind": r[5]} for r in rows},
          open("/home/t-matthewho/ac3/ctx_editor/neurips_review/autoresearch/tasks/T17/corrected_tabmain.json", "w"), indent=2)
