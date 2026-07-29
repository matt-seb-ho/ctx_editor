#!/usr/bin/env python
"""T2A — Tier-A pollution injection harness.

Builds *constructed* pollution: a known-false assumption injected at a known
position into a clean LiC conversation prefix, plus a surface-matched *true*
span in the same conversation. Both spans are ground truth **by construction** —
no judge, and no model of any kind, is involved in producing the labels.

Design constraints enforced here:
  * every injected span carries a **rare anchor token** verified absent from the
    entire pre-injection conversation body (user + assistant messages), so the
    downstream probe is deterministic and paraphrase-independent;
  * harmful and useful spans use the **same surface frames** across the corpus,
    so a detector cannot win by spotting "an injected-looking sentence";
  * the harmful and useful span inside one conversation never refer to the same
    referent, so they do not contradict each other and give the game away;
  * nothing is injected into the FINAL assistant message (replay strips it).

Outputs:
  data/t2a_injected/<task_dir>/<conv>/<sample_id>.json
  data/t2a_clean/<task_dir>/<conv>/<sample_id>.json
  neurips_review/autoresearch/tasks/T2A/manifest.jsonl
"""
from __future__ import annotations

import ast
import glob
import json
import os
import random
import re
import shutil
import sqlite3
import sys
from typing import Optional

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PREFIX_ROOT = os.path.join(REPO, "data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry")
OUT_INJ = os.path.join(REPO, "data/t2a_injected")
OUT_CLEAN = os.path.join(REPO, "data/t2a_clean")
MANIFEST = os.path.join(os.path.dirname(__file__), "manifest.jsonl")

RNG = random.Random(20260729)

# ONE surface frame for every injected span, harmful and useful alike. Frame
# therefore carries zero label information: a detector cannot score by spotting
# "an injected-looking sentence", because half the injected sentences are the
# ones it is supposed to KEEP.
FRAME = "Quick note so we don't lose track of this: {claim} I'll carry that forward."
FRAME_REQ = FRAME
FRAME_CHK = FRAME


def word_in(tok: str, text: str) -> bool:
    return bool(re.search(re.escape(str(tok).lower()), text.lower()))


def body_text(msgs: list[dict]) -> str:
    """User + assistant text only.

    The system message holds the DDL / format spec, so a token present only
    there is still 'rare' for our purposes: the analyzer *could* surface it
    spontaneously, and that possibility is exactly what the clean-arm base rate
    is there to measure.
    """
    return "\n".join(m["content"] for m in msgs if m.get("role") != "system")


def corrupt(v: str) -> Optional[str]:
    """Deterministic wrong variant of a true literal, kept plausible-looking."""
    s = str(v).strip()
    if re.fullmatch(r"-?\d+", s):
        return str(int(s) + 7)
    if re.fullmatch(r"-?\d*\.\d+", s):
        return f"{float(s) + 7.5:g}"
    if s.startswith("[") and s.endswith("]"):
        try:
            lst = ast.literal_eval(s)
            if isinstance(lst, list) and lst:
                lst = list(lst)
                if isinstance(lst[-1], (int, float)):
                    lst[-1] = lst[-1] + 7
                elif isinstance(lst[-1], str):
                    lst[-1] = lst[-1] + "z"
                else:
                    return None
                return repr(lst)
        except Exception:
            return None
    if s.lower() in ("true", "false"):
        return "false" if s.lower() == "true" else "true"
    if re.fullmatch(r'"[^"]*"', s) or re.fullmatch(r"'[^']*'", s):
        return s[0] + s[1:-1] + "z" + s[-1]
    if re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{2,}", s):
        # plausible wrong proper noun: keep shape, change the tail
        return s[:-1] + ("n" if s[-1].lower() != "n" else "r")
    return None


# ---------------------------------------------------------------- database ---

def db_path(db_id: str) -> Optional[str]:
    p = os.path.join(REPO, "data/spider/databases", db_id, f"{db_id}.sqlite")
    return p if os.path.exists(p) else None


def run_sql(db_id: str, sql: str):
    p = db_path(db_id)
    if not p:
        return None
    try:
        con = sqlite3.connect(p)
        con.text_factory = lambda b: b.decode("utf-8", "ignore")
        cur = con.execute(sql)
        rows = cur.fetchall()
        names = [d[0] for d in cur.description] if cur.description else []
        con.close()
        return names, rows
    except Exception:
        return None


def _db_value_picks(names, rows, body, ref, limit=6):
    """Distinct (column, value) pairs from the gold result whose value is a rare
    literal (absent from the conversation body and from reference_sql)."""
    picks = []
    for ci, cn in enumerate(names):
        for r in rows[:20]:
            v = r[ci]
            if v is None:
                continue
            sv = str(v).strip()
            if len(sv) < 4 or len(sv) > 40:
                continue
            if word_in(sv, body) or word_in(sv, ref):
                continue
            picks.append((cn, sv))
            break
        if len(picks) >= limit:
            break
    return picks


def build_database(sample: dict, msgs: list[dict]) -> dict:
    body = body_text(msgs)
    ref = sample["reference_sql"]
    st = json.loads(sample["schema_tables"])
    cols = {t: [c[1] for c in v["columns"]] for t, v in st.items()}
    out: dict[str, list[dict]] = {"harm_req": [], "harm_chk": [], "use_chk": [], "use_req": []}

    # HARMFUL, requirement frame — phantom output-column requirement.
    # Taxonomy: F4 "Overfit requirements" (21/48 = 44% of all observed rewrite
    # failures; 10/12 = 83% on database) and the documented #1 real Spider error
    # "SQL semantically correct but returns extra columns" (12/21 errors).
    cand = [
        (t, c)
        for t, cs in cols.items()
        for c in cs
        if len(c) >= 4
        and not re.search(r"\b" + re.escape(c.lower()) + r"\b", ref.lower())
        and not re.search(r"\b" + re.escape(c.lower()) + r"\b", body.lower())
    ]
    if cand:
        t, c = RNG.choice(sorted(cand))
        out["harm_req"].append(
            dict(
                kind="H_PHANTOM_COL",
                frame="REQ",
                anchor=c,
                text=FRAME_REQ.format(
                    claim=f"you also need `{t}.{c}` included as an extra output column in the "
                    f"final result, and rows where `{t}.{c}` is NULL filtered out."
                ),
                why="Attributes to the user a requirement never stated; the extra column makes "
                "the result set differ from reference_sql (Spider result_eq fails).",
            )
        )

    # USEFUL / HARMFUL, check frame — true vs false executed-result fact.
    # Useful side: necessary verification state, obtainable only by running the
    # query. Harmful side: taxonomy F2 "Anchored on partial wrong work".
    res = run_sql(sample["db_id"], ref)
    if res and res[1]:
        names, rows = res
        picks = _db_value_picks(names, rows, body, ref)
        if picks:
            cn, sv = picks[0]
            out["use_chk"].append(
                dict(
                    kind="U_EXEC_FACT",
                    frame="CHK",
                    anchor=sv,
                    ref_col=cn,
                    text=FRAME_CHK.format(
                        claim=f"I checked this against the data \u2014 the correct result has "
                        f"{len(rows)} row(s), and `{sv}` is one of the values that must appear "
                        f"in the `{cn}` column."
                    ),
                    why="Obtained by executing reference_sql against the restored Spider DB. True.",
                )
            )
            # false fact about a DIFFERENT referent — required, so the two
            # injected spans in one conversation never contradict each other.
            alt = picks[1] if len(picks) > 1 else None
            wrong = corrupt(alt[1]) if alt else None
            if wrong and not word_in(wrong, body):
                out["harm_chk"].append(
                    dict(
                        kind="H_WRONG_EXEC_FACT",
                        frame="CHK",
                        anchor=wrong,
                        ref_col=alt[0],
                        text=FRAME_CHK.format(
                            claim=f"I checked this against the data \u2014 the correct result has "
                            f"{len(rows)} row(s), and `{wrong}` is one of the values that "
                            f"must appear in the `{alt[0]}` column."
                        ),
                        why="Contradicts the executed reference_sql result. False by construction.",
                    )
                )
    return out


# -------------------------------------------------------------------- code ---

PHANTOM_PARAMS = ["trace_log", "strict_mode", "audit_flag", "debug_ctx", "verbose_out"]


def build_code(sample: dict, msgs: list[dict]) -> dict:
    body = body_text(msgs)
    starter = (sample.get("starter_code") or "").strip()
    meta = sample.get("metadata")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    fname = (meta or {}).get("func_name")
    if not fname:
        m = re.search(r"def\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", starter)
        fname = m.group(1) if m else None
    out: dict[str, list[dict]] = {"harm_req": [], "harm_chk": [], "use_chk": [], "use_req": []}

    # HARMFUL, requirement frame — phantom required parameter.
    # Taxonomy: F4 "Overfit requirements" + F5 "Schema/detail lost" — together
    # 10/12 = 83% of observed code rewrite failures (phantom parameters and
    # wrong return type).
    for p in PHANTOM_PARAMS:
        if not word_in(p, body):
            out["harm_req"].append(
                dict(
                    kind="H_PHANTOM_PARAM",
                    frame="REQ",
                    anchor=p,
                    text=FRAME_REQ.format(
                        claim=f"the function also has to take a required `{p}` parameter and "
                        f"return a tuple `(result, {p})` rather than the bare result."
                    ),
                    why="Never requested; a required extra parameter makes the grader's call "
                    "signature fail outright.",
                )
            )
            break

    # USEFUL, requirement frame — the true graded interface. LiC's code task
    # never shows starter code (documented failure mode "Missing Function
    # Signatures"), so this is genuinely novel, correct, necessary state.
    if fname and starter and not word_in(fname, body):
        sig = re.sub(r"\s+", " ", starter).rstrip(":").strip()
        out["use_req"].append(
            dict(
                kind="U_TRUE_SIG",
                frame="REQ",
                anchor=fname,
                text=FRAME_REQ.format(
                    claim=f"the graded interface is `{sig}` — the function must be named "
                    f"`{fname}` and take exactly those arguments."
                ),
                why="Read verbatim off the benchmark starter_code. True by construction.",
            )
        )

    # USEFUL / HARMFUL, check frame — true vs false public test case.
    try:
        tcs = json.loads(sample["public_test_cases"])
    except Exception:
        tcs = []
    usable = []
    for tc in tcs:
        inp = re.sub(r"\s+", ", ", str(tc.get("input", "")).strip())
        o = str(tc.get("output", "")).strip()
        if not inp or not o or len(o) > 40 or word_in(o, body):
            continue
        usable.append((inp, o))
    if usable:
        inp, o = usable[0]
        out["use_chk"].append(
            dict(
                kind="U_TRUE_TEST",
                frame="CHK",
                anchor=o,
                text=FRAME_CHK.format(claim=f"I checked the expected behaviour \u2014 for the input `{inp}` the "
                                  f"function must return `{o}`."),
                why="A benchmark public test case. True by construction.",
            )
        )
        ainp, ao = usable[1] if len(usable) > 1 else (None, None)
        wrong = corrupt(ao) if ao else None
        if wrong and not word_in(wrong, body):
            out["harm_chk"].append(
                dict(
                    kind="H_WRONG_TEST",
                    frame="CHK",
                    anchor=wrong,
                    text=FRAME_CHK.format(
                        claim=f"I checked the expected behaviour \u2014 for the input `{ainp}` the "
                        f"function must return `{wrong}`."
                    ),
                    why="Contradicts the benchmark public test case. False by construction.",
                )
            )
    return out


# ------------------------------------------------------------------ driver ---

def assistant_slots(msgs: list[dict]) -> list[int]:
    """Assistant positions eligible for injection; the final one is excluded
    because replay strips it before any strategy runs."""
    idx = [i for i, m in enumerate(msgs) if m.get("role") == "assistant"]
    return idx[:-1]


_ALT = {"n": 0}


def choose_pair(o: dict):
    """One harmful + one useful span per conversation.

    Two pair designs, alternated so both are ~half the corpus:
      * MATCHED  - harmful and useful make the *same kind of claim* about
        *different referents*, one true and one false (wrong-vs-right executed
        fact / wrong-vs-right test case). This is the tightest test: claim type,
        frame, length and position distribution are all held fixed and only the
        truth value differs.
      * MIXED    - a phantom-requirement harmful span (the dominant observed
        failure mode, F4) paired with a true useful span.
    """
    matched = []
    if o["harm_chk"] and o["use_chk"]:
        matched.append((o["harm_chk"][0], o["use_chk"][0], "MATCHED"))
    mixed = []
    if o["harm_req"] and o["use_chk"]:
        mixed.append((o["harm_req"][0], o["use_chk"][0], "MIXED"))
    if o["harm_req"] and o["use_req"]:
        mixed.append((o["harm_req"][0], o["use_req"][0], "MIXED"))
    if o["harm_chk"] and o["use_req"]:
        mixed.append((o["harm_chk"][0], o["use_req"][0], "MIXED"))
    _ALT["n"] += 1
    order = (matched, mixed) if _ALT["n"] % 2 else (mixed, matched)
    for bucket in order:
        if bucket:
            return RNG.choice(bucket)
    return None


def main() -> int:
    tasks = {"database_v2": "database", "code_v2": "code"}
    subsets = {
        k: {d["task_id"]: d for d in json.load(open(os.path.join(REPO, p)))}
        for k, p in [
            ("database_v2", "data/htn50_52_database_subset.json"),
            ("code_v2", "data/htn50_52_code_subset.json"),
        ]
    }
    convs = ["conv0", "conv1"]
    if os.path.isdir(OUT_INJ):
        shutil.rmtree(OUT_INJ)
    if os.path.isdir(OUT_CLEAN):
        shutil.rmtree(OUT_CLEAN)
    man = open(MANIFEST, "w")
    stats: dict[str, int] = {}
    for tdir, tname in tasks.items():
        for conv in convs:
            src = os.path.join(PREFIX_ROOT, tdir, conv)
            dst_i = os.path.join(OUT_INJ, tdir, conv)
            dst_c = os.path.join(OUT_CLEAN, tdir, conv)
            os.makedirs(dst_i, exist_ok=True)
            os.makedirs(dst_c, exist_ok=True)
            for f in sorted(glob.glob(os.path.join(src, "*.json"))):
                if "false_negatives" in f:
                    continue
                tr = json.load(open(f))
                sid = tr["sample_id"]
                sample = subsets[tdir].get(sid)
                if sample is None:
                    stats["no_sample"] = stats.get("no_sample", 0) + 1
                    continue
                msgs = tr["trace"]["messages"]
                shutil.copyfile(f, os.path.join(dst_c, os.path.basename(f)))

                built = (build_database if tname == "database" else build_code)(sample, msgs)
                chosen = choose_pair(built)
                if chosen is None:
                    stats[f"{tname}_no_pair"] = stats.get(f"{tname}_no_pair", 0) + 1
                    continue
                harm, use, design = chosen
                slots = assistant_slots(msgs)
                if len(slots) < 2:
                    stats[f"{tname}_too_short"] = stats.get(f"{tname}_too_short", 0) + 1
                    continue
                a, b = sorted(RNG.sample(slots, 2))
                h_idx, u_idx = (a, b) if RNG.random() < 0.5 else (b, a)

                new_msgs = [dict(m) for m in msgs]
                new_msgs[h_idx]["content"] = new_msgs[h_idx]["content"].rstrip() + "\n\n" + harm["text"]
                new_msgs[u_idx]["content"] = new_msgs[u_idx]["content"].rstrip() + "\n\n" + use["text"]
                tr["trace"] = dict(tr["trace"])
                tr["trace"]["messages"] = new_msgs
                json.dump(tr, open(os.path.join(dst_i, os.path.basename(f)), "w"), indent=1)

                man.write(
                    json.dumps(
                        dict(
                            task=tname,
                            task_dir=tdir,
                            conv=conv,
                            sample_id=sid,
                            pair_design=design,
                            n_assistant_slots=len(slots),
                            harmful=dict(harm, msg_index=h_idx, slot_rank=slots.index(h_idx)),
                            useful=dict(use, msg_index=u_idx, slot_rank=slots.index(u_idx)),
                        )
                    )
                    + "\n"
                )
                for k, v in [
                    (f"{tname}_ok", 1),
                    (f"{tname}|{harm['kind']}", 1),
                    (f"{tname}|{use['kind']}", 1),
                    (f"{tname}_{design}", 1),
                ]:
                    stats[k] = stats.get(k, 0) + v
    man.close()
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
