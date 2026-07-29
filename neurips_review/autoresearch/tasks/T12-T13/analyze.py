#!/usr/bin/env python
"""T12/T13 analysis: order sensitivity, cheatsheet divergence, batch dose-response."""
import json, os, re, sys, itertools, statistics as st

ROOT = "/home/t-matthewho/ac3/ctx_editor"
D = f"{ROOT}/neurips_review/autoresearch/tasks/T12-T13"
ORDS = ["ord0", "ord1001", "ord1002", "ord1003"]


def load_results(p):
    with open(p) as f:
        d = json.load(f)
    return d["results"] if isinstance(d, dict) else d


def acc(p):
    r = load_results(p)
    c = sum(1 for x in r if x.get("is_correct"))
    return c, len(r), 100.0 * c / len(r)


def adj(p):
    """FN-adjusted accuracy from run_summary.json (canonical headline number)."""
    try:
        with open(f"{p}/run_summary.json") as f:
            d = json.load(f)
    except FileNotFoundError:
        return None
    m = d.get("metrics", d)
    a = d.get("adjusted_accuracy", m.get("adjusted_accuracy"))
    return 100.0 * a if a is not None and a <= 1.0 else a


def summary(p):
    with open(f"{p}/run_summary.json") as f:
        return json.load(f)


def content_words(text):
    return set(w for w in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split() if len(w) > 3)


def bullets(text):
    """Count list items regardless of marker style (-, *, 1., •)."""
    return [l for l in text.splitlines()
            if re.match(r"\s*([-*•]|\d+[.)])\s+\S", l)]


def sign_test(n_pos, n_neg):
    """Two-sided exact binomial sign test p-value for discordant pairs."""
    from math import comb
    n = n_pos + n_neg
    if n == 0:
        return 1.0
    k = min(n_pos, n_neg)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def cheat(p):
    with open(p) as f:
        d = json.load(f)
    return d["content"]


def integrity(task):
    """Flag run dirs whose metrics.json, run_summary.json and results.json disagree.

    A mismatch means two processes wrote the same output dir (see worklog §7).
    """
    import glob
    bad = []
    for d in sorted(glob.glob(f"{ROOT}/outputs/T12_T13/{task}/*")):
        try:
            m = json.load(open(f"{d}/metrics.json"))["correct"]
            s = json.load(open(f"{d}/run_summary.json"))["metrics"]["correct"]
            r = sum(1 for x in load_results(f"{d}/results.json") if x["is_correct"])
        except (FileNotFoundError, KeyError):
            continue
        if not (m == s == r):
            bad.append((os.path.basename(d), m, s, r))
    if bad:
        print("\n*** INTEGRITY FAILURE — these dirs were written by >1 process ***")
        for b in bad:
            print(f"   {b[0]}: metrics={b[1]} summary={b[2]} results={b[3]}")
    else:
        print("integrity check: all run dirs internally consistent")
    return not bad


def report(task):
    out = f"{ROOT}/outputs/T12_T13/{task}"
    mem = f"{D}/memories/{task}"
    print(f"\n{'='*78}\nTASK: {task}\n{'='*78}")
    integrity(task)

    # ---- reference ----
    ref = None
    if os.path.exists(f"{out}/ref_nomem/results.json"):
        ref = acc(f"{out}/ref_nomem/results.json")
        print(f"Augment, NO memory        : {ref[0]:2d}/{ref[1]} = {ref[2]:5.1f}%")

    # ---- T12 online arms ----
    print("\n-- T12: online (continual) memory, one cell per trajectory ordering --")
    online = {}
    for o in ORDS:
        p = f"{out}/mem_{o}/results.json"
        if os.path.exists(p):
            online[o] = acc(p)
            print(f"  {o:8s} {online[o][0]:2d}/{online[o][1]} = {online[o][2]:5.1f}%")
    if len(online) >= 2:
        v = [x[2] for x in online.values()]
        n = list(online.values())[0][1]
        print(f"  mean +/- std (n_orderings={len(v)}) : {st.mean(v):.1f} +/- "
              f"{st.stdev(v) if len(v)>1 else 0:.1f} pp   range {min(v):.1f}-{max(v):.1f} "
              f"(spread {max(v)-min(v):.1f}pp = {round((max(v)-min(v))*n/100)} instances of {n})")
        if ref:
            print(f"  delta vs no-memory        : {st.mean(v)-ref[2]:+.1f}pp")

    # ---- instance-level instability across orderings ----
    if len(online) >= 3:
        per = {}
        for o in online:
            for x in load_results(f"{out}/mem_{o}/results.json"):
                per.setdefault(x["sample_id"], []).append(bool(x["is_correct"]))
        unstable = [k for k, v in per.items() if 0 < sum(v) < len(v)]
        print(f"  instance-level instability: {len(unstable)}/{len(per)} instances flip "
              f"correctness across orderings ({100.0*len(unstable)/len(per):.0f}%)")
        if ref:
            refmap = {x["sample_id"]: bool(x["is_correct"])
                      for x in load_results(f"{out}/ref_nomem/results.json")}
            pos = neg = 0
            for k, v in per.items():
                for c in v:
                    if c and not refmap.get(k):
                        pos += 1
                    elif (not c) and refmap.get(k):
                        neg += 1
            print(f"  paired vs no-memory (pooled over orderings): memory fixes {pos}, "
                  f"memory breaks {neg}, sign-test p = {sign_test(pos, neg):.4f}")

    # ---- T13 inductive arms ----
    print("\n-- T13: offline (frozen, disjoint learn set) memory --")
    frozen = {}
    clean = {}
    LEARN = set(x["task_id"] for x in json.load(open(f"{ROOT}/data/lic_mem_learn_set.json")))
    for o in ORDS:
        p = f"{out}/frozen_{o}/results.json"
        if os.path.exists(p):
            r = load_results(p)
            frozen[o] = acc(p)
            cl = [x for x in r if x["sample_id"] not in LEARN]
            ov = [x for x in r if x["sample_id"] in LEARN]
            cc = sum(1 for x in cl if x.get("is_correct"))
            oc = sum(1 for x in ov if x.get("is_correct"))
            clean[o] = 100.0 * cc / max(1, len(cl))
            print(f"  {o:8s} all {frozen[o][0]:2d}/{frozen[o][1]} = {frozen[o][2]:5.1f}%"
                  f" | clean {cc:2d}/{len(cl)} = {clean[o]:5.1f}%"
                  f" | on-overlap {oc}/{len(ov)}")
    if frozen:
        v = [x[2] for x in frozen.values()]
        cv = list(clean.values())
        print(f"  mean +/- std (n_orderings={len(v)}) : all {st.mean(v):.1f} +/- "
              f"{st.stdev(v) if len(v)>1 else 0:.1f} pp | clean {st.mean(cv):.1f} +/- "
              f"{st.stdev(cv) if len(cv)>1 else 0:.1f} pp")
        if ref:
            r = load_results(f"{out}/ref_nomem/results.json")
            cl = [x for x in r if x["sample_id"] not in LEARN]
            ov = [x for x in r if x["sample_id"] in LEARN]
            cc = sum(1 for x in cl if x.get("is_correct"))
            oc = sum(1 for x in ov if x.get("is_correct"))
            print(f"  no-memory : all {ref[0]}/{ref[1]} = {ref[2]:.1f}% | "
                  f"clean {cc}/{len(cl)} = {100.0*cc/len(cl):.1f}% | on-overlap {oc}/{len(ov)}")
            print(f"  CLEAN-SUBSET DELTA (offline memory - no memory) = "
                  f"{st.mean(cv) - 100.0*cc/len(cl):+.1f}pp")

    # ---- cheatsheet divergence ----
    for label, pat in [("online", "{o}_cheatsheet.json"), ("offline", "offline_{o}_cheatsheet.json")]:
        cs = {}
        for o in ORDS:
            p = f"{mem}/{pat.format(o=o)}"
            if os.path.exists(p):
                cs[o] = cheat(p)
        if len(cs) < 2:
            continue
        print(f"\n-- cheatsheet spread ({label}) --")
        for o, c in cs.items():
            print(f"  {o:8s} {len(c.split()):4d} words, {len(bullets(c)):3d} bullets")
        js = []
        for a, b in itertools.combinations(cs, 2):
            A, B = content_words(cs[a]), content_words(cs[b])
            j = len(A & B) / len(A | B)
            js.append(j)
            print(f"  Jaccard(content words) {a:8s} vs {b:8s} = {j:.3f}")
        print(f"  mean pairwise Jaccard = {st.mean(js):.3f}")

    # ---- batch dose-response (online arms only) ----
    print("\n-- T13 dose-response: accuracy by batch index, pooled over orderings --")
    order_files = {o: [x["task_id"] for x in json.load(
        open(f"{D}/data/dev_{task}_{o}.json"))] for o in ORDS
        if os.path.exists(f"{D}/data/dev_{task}_{o}.json")}
    byb = {}
    for o in online:
        r = {x["sample_id"]: x["is_correct"] for x in load_results(f"{out}/mem_{o}/results.json")}
        ids = [i for i in order_files[o] if i in r]
        for idx, sid in enumerate(ids):
            b = idx // 5
            byb.setdefault(b, []).append(bool(r[sid]))
    for b in sorted(byb):
        v = byb[b]
        print(f"  batch {b+1} (mem from {5*b:2d} prior eval instances): "
              f"{sum(v):2d}/{len(v):2d} = {100.0*sum(v)/len(v):5.1f}%")


if __name__ == "__main__":
    for t in (sys.argv[1:] or ["database", "math"]):
        try:
            report(t)
        except FileNotFoundError as e:
            print(f"[{t}] incomplete: {e}")
