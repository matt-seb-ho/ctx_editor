import json, math
from pathlib import Path
R=Path('/home/t-matthewho/ac3/ctx_editor')

def ids(f, key='task_id'):
    d=json.load(open(R/f))
    out=set()
    for x in d:
        for k in ('task_id','sample_id','id','qa_id'):
            if k in x: out.add(x[k]); break
    return out

def res(p):
    return {x['sample_id']: bool(x['is_correct']) for x in json.load(open(R/p))}

pools = {
 'dev_database_subset (paper tab:main pool, top-25 hardest)': 'data/dev_database_subset.json',
 'htn50_52_database_subset (3-model matrix pool, top-50 hardest)': 'data/htn50_52_database_subset.json',
}
poolsc = {
 'dev_code_subset (paper pool, top-25 hardest)': 'data/dev_code_subset.json',
 'htn50_52_code_subset (3-model matrix pool)': 'data/htn50_52_code_subset.json',
}

for task, arms, pl in [('database', ['db_baseline','db_reset','db_gated'], pools),
                       ('code', ['code_baseline','code_reset'], poolsc)]:
    print('='*70); print('TASK', task)
    base = res(f'outputs/T1/main/{arms[0]}/results.json')
    print(f'  full pool n={len(base)}  acc={sum(base.values())/len(base)*100:.1f}%')
    for name,f in pl.items():
        P=ids(f)
        inter = [k for k in base if k in P]
        print(f'  pool "{name}": file n={len(P)}, overlap with T1 run = {len(inter)}')
        if not inter:
            print('     sample id examples pool:', list(P)[:3]); print('     run:', list(base)[:3])
            continue
        for a in arms:
            r = res(f'outputs/T1/main/{a}/results.json')
            sub=[r[k] for k in inter if k in r]
            print(f'     {a:14s} restricted acc = {sum(sub)/len(sub)*100:.1f}%  ({sum(sub)}/{len(sub)})')
        # complement
        comp=[k for k in base if k not in P]
        print(f'     baseline on COMPLEMENT (n={len(comp)}): {sum(base[k] for k in comp)/len(comp)*100:.1f}%')
