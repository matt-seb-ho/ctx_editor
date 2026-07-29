# BLOCK-spider — get Spider SQLite databases on disk

**Status: RESOLVED (SUCCESS)** — 2026-07-29, autonomous overnight session.

Total elapsed: ~10 minutes. Downloaded, extracted, verified, and smoke-tested end-to-end.

---

## 1. What the code actually needs

`src/lic/tasks/database/task_database_v2.py:159` →
```python
spider_db_dir = get_data_path("data/spider/databases")
...
eval_exec_match_sync(str(spider_db_dir / db_id / f"{db_id}.sqlite"), pred, gold, ...)
```

`eval_exec_match_sync` (same file, L62-67) does **not** use only that one file. It takes
`os.path.dirname(db)` and globs **every** `*.sqlite` in that directory, then requires the
prediction to agree with gold on **all** of them:

```python
db_dir = os.path.dirname(db)
db_paths = [os.path.join(db_dir, b) for b in os.listdir(db_dir) if ".sqlite" in b]
```

That is the **test-suite execution accuracy** semantics of Zhong et al. (EMNLP 2020,
arXiv:2010.02840) — i.e. the correct artifact is the *test-suite* database bundle, not the
plain 1-sqlite-per-db_id Spider `database/` dir. V1 (`task_database.py:57`) passes the
directory directly; V2 passes `<db_id>/<db_id>.sqlite` and re-derives the dir. Equivalent.

So the required layout is:
```
data/spider/databases/<db_id>/<db_id>.sqlite      # canonical, must exist
data/spider/databases/<db_id>/<db_id>vXXXX.sqlite # test-suite variants, all globbed
```

## 2. Which db_ids are needed

Union across all three eval subsets = **17 db_ids** (not the full ~200 Spider set):

| subset | #samples | #db_ids |
|---|---|---|
| `data/test_database_subset_t3.json` | 48 | 17 |
| `data/dev_database_subset.json` | 25 | 15 |
| `data/htn50_52_database_subset.json` | 50 | 17 |

The 17: `battle_death, car_1, concert_singer, course_teach, dog_kennels,
employee_hire_evaluation, flight_2, museum_visit, network_1, orchestra, pets_1,
poker_player, student_transcripts_tracking, tvshow, voter_1, world_1, wta_1`

(These are all Spider **dev**-split DBs, which is why the dev-only bundle suffices.)

## 3. Sources tried

| # | Source | Result |
|---|---|---|
| 1 | Local disk sweep — `find /home/t-matthewho -iname "*.sqlite"`, `find /datadisk ...`, `~/misc`, `outputs/` | **Fail.** Only hit was `~/.local/share/copilot-api/copilot-api.sqlite`. `/datadisk` contains only `docker/` and `lost+found`. No blob mount present. |
| 2 | HF datasets API — `huggingface.co/api/datasets?search=spider` (50 repos), then `?full=true` file listings for the 9 plausible ones (`xlangai/spider`, `ZR00/Spider_EDL`, `jm0727/spider`, `jm0727/spider-val`, `CM/spider`, `sert121/SpiderSQL`, `karlen532/spider`, `alagaesia/spider_dev`, `naman1011/spider`) | **Fail.** Zero `.zip/.sqlite/.tar.gz/.db/.7z` siblings across all of them — parquet/json only, as expected. |
| 3 | HF spaces API — `?search=spider` (60 results) and `?search=text-to-sql` (40 results) | **Fail.** Results were overwhelmingly `nitrosocke-spider-verse-diffusion` clones and small text2sql demos; nothing vendoring Spider sqlite files. |
| 4 | **`blob_staging/supplementary.tar.gz`** (289 MB, from the Azure blob recovery) | **Partial — the decisive clue.** `tar tvzf` showed `lic/data/spider/databases` is a **dangling symlink** → `/home/v-homatthew/collabmem/src/lic/data/spider/temp/database`, so the DBs themselves were never preserved. **But** the sibling `lic/data/spider/readme.txt` was preserved and names the exact provenance the original run used. |
| 5 | **`github.com/taoyds/test-suite-sql-eval` Google Drive** (pointed to by that readme) | **SUCCESS.** File id `1mkCx2GOFIqNesD4y8TDAO1yX1QZORP5w`, 1.27 GB zip, 3999 files, 5.1 GB uncompressed. |

### The recovered provenance note (verbatim, from `supplementary.tar.gz:lic/data/spider/readme.txt`)
```
Please download the database from the google drive link mentioned in the repo-level readme
and decompress in this directory.

https://github.com/taoyds/test-suite-sql-eval?tab=readme-ov-file

After this step, "test-suite-sql-eval/database/atis/atis.sqlite" should be a valid file path.
```
This confirms the original LiC-database numbers were computed against the **test-suite**
bundle, so using it here reproduces the original evaluation semantics exactly. Good.

## 4. Exact commands that worked

```bash
# gdown is not in the venv and the venv has no pip; install via uv
uv pip install --python .venv/bin/python gdown

# 1.27 GB, ~30 s
mkdir -p /tmp/spiderdl && cd /tmp/spiderdl
/home/t-matthewho/ac3/ctx_editor/.venv/bin/gdown 1mkCx2GOFIqNesD4y8TDAO1yX1QZORP5w \
  -O testsuitedatabases.zip

# strip the macOS resource-fork junk (__MACOSX/._*.sqlite would otherwise be globbed
# by eval_exec_match_sync's `if ".sqlite" in basename` check and break evaluation)
unzip -q -o testsuitedatabases.zip -x "__MACOSX/*" -d /tmp/spiderdl/extracted

mv /tmp/spiderdl/extracted/database \
   /home/t-matthewho/ac3/ctx_editor/data/spider/databases
```

> **Gotcha worth remembering:** the `-x "__MACOSX/*"` exclusion is load-bearing. The filter in
> `eval_exec_match_sync` is a substring test (`".sqlite" in basename`), not a suffix test, so
> AppleDouble sidecars named `._concert_singer.sqlite` would be picked up as databases and
> the `assert g_flag != "exception"` on the gold query would fire.

## 5. Final on-disk layout

```
/home/t-matthewho/ac3/ctx_editor/data/spider/databases/     4.9 GB, 29 db_id dirs
├── academic/  advising/  atis/  geography/  imdb/  restaurants/  scholar/  yelp/   (other tasks, unused)
├── cre_Doc_Template_Mgt/  real_estate_properties/  singer/                          (spider dev, unused by our subsets)
├── battle_death/                 28 *.sqlite   incl. battle_death.sqlite
├── car_1/                        60 *.sqlite   incl. car_1.sqlite
├── concert_singer/               32 *.sqlite
├── course_teach/                 25 *.sqlite
├── dog_kennels/                  48 *.sqlite
├── employee_hire_evaluation/     27 *.sqlite
├── flight_2/                     56 *.sqlite
├── museum_visit/                 35 *.sqlite
├── network_1/                    29 *.sqlite
├── orchestra/                    28 *.sqlite
├── pets_1/                       27 *.sqlite
├── poker_player/                 31 *.sqlite
├── student_transcripts_tracking/ 55 *.sqlite
├── tvshow/                       25 *.sqlite
├── voter_1/                      27 *.sqlite
├── world_1/                      46 *.sqlite
├── wta_1/                        33 *.sqlite
└── readme.txt
```

**Coverage: 17 / 17 needed db_ids present, each with its canonical `<db_id>/<db_id>.sqlite`.**

### Git safety
`data/` is gitignored, so nothing here can be committed by accident:
```
$ git check-ignore -v data/spider/databases
.gitignore:217:/data/	data/spider/databases
$ git status --short
(clean)
```
Disk after: `/dev/root 991G used 36G avail 956G (4%)`.

## 6. Verification (verbatim output)

Script: 5 gold SQL queries from `data/dev_database_subset.json`, spanning 5 distinct db_ids,
run through (a) `_exec_on_db_sync` (the raw execution path) and (b) `eval_exec_match_sync`
with `pred == gold` over the **full test suite** for that db_id, plus a negative control.

```
db_dir: /home/t-matthewho/ac3/ctx_editor/data/spider/databases exists: True

--- tvshow ---
gold: SELECT T1.country FROM TV_Channel AS T1 JOIN cartoon AS T2 ON T1.id = T2.Channel WHERE T2.written_by = 'Todd Casey'
raw exec flag: result | nrows: 2
first rows: [('United Kingdom',), ('Italy',)]
eval_exec_match_sync(gold,gold) = 1  (0.02s over full test suite)

--- dog_kennels ---
gold: SELECT count(*) FROM Professionals WHERE professional_id NOT IN ( SELECT professional_id FROM Treatments )
raw exec flag: result | nrows: 1
first rows: [(7,)]
eval_exec_match_sync(gold,gold) = 1  (0.03s over full test suite)

--- battle_death ---
gold: SELECT name , RESULT FROM battle WHERE bulgarian_commander != 'Boril'
raw exec flag: result | nrows: 6
first rows: [('Battle of Adrianople', 'Bulgarian victory'), ('Battle of Serres', 'Bulgarian victory'), ('Battle of Rusion', 'Bulgarian victory')]
eval_exec_match_sync(gold,gold) = 1  (0.03s over full test suite)

--- car_1 ---
gold: SELECT T1.CountryName FROM COUNTRIES AS T1 JOIN CONTINENTS AS T2 ON T1.Continent = T2.ContId JOIN CAR_MAKERS AS T3 ON T1.CountryId = T3.Country WHERE T2.Continent = 'europe' GROUP BY T1.CountryName HAVING count(*) >= 3;
raw exec flag: result | nrows: 2
first rows: [('france',), ('germany',)]
eval_exec_match_sync(gold,gold) = 1  (0.04s over full test suite)

--- network_1 ---
gold: SELECT student_id FROM Friend INTERSECT SELECT liked_id FROM Likes
raw exec flag: result | nrows: 8
first rows: [(1101,), (1247,), (1304,)]
eval_exec_match_sync(gold,gold) = 1  (0.03s over full test suite)

--- negative control ---
pred 'SELECT 1' vs gold: 0
```

All 5 gold queries execute and return non-empty row sets; all 5 score 1 against themselves
across the entire test suite (25-60 DBs each); the negative control correctly scores 0.
Eval cost is negligible (~0.03 s/sample), so the test-suite semantics add no meaningful
runtime overhead.

## 7. End-to-end smoke (3 samples, TRAPI)

```bash
. .venv/bin/activate && ctx-editor experiment=baseline model=gpt5_4_mini_trapi \
  task=database_v2 load_balancer=trapi execution.max_concurrent=3 task.limit=3
```
The sample-count key is **`task.limit`** (defined in `src/ctx_editor/config/task/database_v2.yaml`,
default `null`). There is no `execution`-level sample cap.

```
[experiment][INFO] - Loaded 3 samples for task config 'database_v2'
[TaskDatabaseV2] active — task_specific extraction + sync eval
Running samples: 100%|██████████| 3/3 [00:28<00:00,  9.57s/sample]
[experiment][INFO] - Results: 1/3 correct (33.33%)
[experiment][INFO] - Average score: 0.333
[experiment][INFO] - Total cost: $0.0889
Accuracy: 33.33% (1/3)   Average Turns: 3.7   Average User Tokens: 60
Results saved to: outputs/2026-07-29/09-43-09
```
No `FileNotFoundError`, no eval exceptions — real graded scores. **Harness unblocked.**

### Follow-up found during the smoke run (fixed, worth propagating)

With `load_balancer=trapi`, the default `false_negative_analysis.model: gpt-5-mini`
(from `config.yaml`) is not a model the TRAPI balancer serves, so FN analysis silently
degrades on every incorrect sample:

```
[experiment][WARNING] - False negative analysis failed for sharded-spider-val-467-medium:
  No endpoints configured for model 'gpt-5-mini'.
  Available models: ['gpt-5.4-mini_2026-03-17', 'gpt-4o_2024-11-20']
```

Verified working override — **use this form for all TRAPI database runs**:
```bash
. .venv/bin/activate && ctx-editor experiment=baseline model=gpt5_4_mini_trapi \
  task=database_v2 load_balancer=trapi execution.max_concurrent=3 task.limit=3 \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17
```
Confirming run (`outputs/2026-07-29/09-43-50`):
```
[experiment][INFO] - Results: 2/3 correct (66.67%)
False negative analysis: 100%|██████████| 1/1 [00:01<00:00,  1.86s/sample]
[ctx_editor.identify_false_negatives][INFO] - False negative analysis saved to:
  outputs/2026-07-29/09-43-50/false_negatives.json
Accuracy: 66.67% (2/3)
Adjusted Accuracy: 66.67% (2/3)  [0 user-sim-induced excluded, 0 non-answer-attempts]
```
(1/3 vs 2/3 between the two runs is ordinary 3-sample sampling noise, not a config effect.)

## 8. Reproducing this on a fresh machine

Two commands, ~1 minute, no credentials required:
```bash
uv pip install --python .venv/bin/python gdown
.venv/bin/gdown 1mkCx2GOFIqNesD4y8TDAO1yX1QZORP5w -O /tmp/testsuitedatabases.zip \
  && unzip -q /tmp/testsuitedatabases.zip -x "__MACOSX/*" -d /tmp/tsdb \
  && mkdir -p data/spider && mv /tmp/tsdb/database data/spider/databases
```
No operator action is required. Nothing to escalate.
