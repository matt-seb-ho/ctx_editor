import json
from pathlib import Path
R=Path('/home/t-matthewho/ac3/ctx_editor')
def res(p):
    p=R/p
    if not (p/'results.json').exists(): return None
    return {x['sample_id']: bool(x['is_correct']) for x in json.load(open(p/'results.json'))}
def ids(f):
    return {x['task_id'] for x in json.load(open(R/f))}

ARMS_DB=[('fully-specified single turn (ceiling)','outputs/T24/db_fullspec'),
   ('AO / assistant omission (design oracle)','outputs/T24/db_ao'),
   ('Concat User (design oracle)','outputs/T24/db_concat'),
   ('Baseline (full context, sharded)','outputs/T1/main/db_baseline'),
   ('AC3-Reset','outputs/T1/main/db_reset'),
   ('AC3-Gated-Reset','outputs/T1/main/db_gated'),
   ('MT-OSC w=4','outputs/T1/main/db_mtosc_w4'),
   ('Summarisation 1/turn','outputs/T1/main/db_summarize1'),
   ('Summarisation 2/turn','outputs/T1/main/db_summarize2')]
ARMS_CODE=[('fully-specified single turn (ceiling)','outputs/T24/code_fullspec'),
   ('AO / assistant omission (design oracle)','outputs/T24/code_ao'),
   ('Concat User (design oracle)','outputs/T24/code_concat'),
   ('Baseline (full context, sharded)','outputs/T1/main/code_baseline'),
   ('AC3-Reset','outputs/T1/main/code_reset'),
   ('Summarisation 1/turn','outputs/T1/main/code_summarize1'),
   ('Summarisation 2/turn','outputs/T1/main/code_summarize2')]
POOLS={'database':[('full LiC pool',None),('htn50_52 (3-model matrix pool)','data/htn50_52_database_subset.json'),("dev subset (paper tab:main pool)",'data/dev_database_subset.json')],
       'code':[('full LiC pool',None),('htn50_52 (3-model matrix pool)','data/htn50_52_code_subset.json'),("dev subset (paper tab:main pool)",'data/dev_code_subset.json')]}

for task,arms in [('database',ARMS_DB),('code',ARMS_CODE)]:
    print('='*88); print('LiC-'+task+'  (gpt-5.4-mini, end-to-end sharded, v2 evaluator, raw accuracy)')
    hdr=[p[0] for p in POOLS[task]]
    print(f'{"arm":42s}' + ''.join(f'{h[:22]:>24s}' for h in hdr))
    base={}
    for name,d in arms:
        r=res(d)
        if r is None: print(f'{name:42s}  [not finished]'); continue
        cells=[]
        for pn,pf in POOLS[task]:
            keys=set(r) if pf is None else (set(r)&ids(pf))
            v=[r[k] for k in keys]
            cells.append(f'{100*sum(v)/len(v):.1f}% ({sum(v)}/{len(v)})')
        print(f'{name:42s}' + ''.join(f'{c:>24s}' for c in cells))
