# Node Backup & Restore — all-in-one runbook

**Purpose.** Back up a GCR Azure sandbox VM (`GCRAZGDLxxxx`) to Azure Blob Storage before a
maintenance window, and restore it afterwards or on a different node.

**Why this exists.** During maintenance: nodes reboot repeatedly, network access drops, and
**data in `/mnt` may be wiped**. Treat everything on the box as disposable.

This file is self-contained — copy it to any node and follow it top to bottom. Nothing else
is required.

> **Historical note.** After the June 2026 server loss, everything under `~/.claude/` was gone:
> the old backups were project-rooted and never captured session transcripts or memory.
> Step 4 below includes `~/.claude/` for exactly this reason. Don't drop it.

---

## 0. Coordinates

```bash
export STORAGE_ACCOUNT=yingxinwustorage
export CONTAINER_NAME=mshotest
export STAMP=$(date +%Y-%m-%d)            # e.g. 2026-08-12
export NODE=$(hostname)                   # e.g. GCRAZGDL1739
export PROJECT=ac3                        # <-- CHANGE THIS per node/project
export PREFIX=${PROJECT}_${NODE}_${STAMP} # every blob name starts with this
export STAGE=$HOME/backup_stage_${STAMP//-/}
```

Everything is written to `$STAGE` first, then uploaded. `$STAGE` is scratch — delete it after
you've verified the upload.

### ⚠ One container, many nodes — namespace your blobs

`mshotest` is a **flat, shared** container: no folders, no per-node isolation, and
`az storage blob upload --overwrite` will silently clobber a same-named blob. If you back up a
second node using the generic names below, you destroy the first node's backup.

**Every blob name must carry `$PREFIX`.** That single rule keeps node-A and node-B backups
side by side. Concretely:

| Node / project | Blob names |
|---|---|
| `GCRAZGDL1739` / `ac3` | `ac3_GCRAZGDL1739_2026-08-12_ctx_editor.tar.zst`, `..._home_config.tar.zst`, `..._MANIFEST.md` |
| other node / other project | `<proj>_<node>_<stamp>_<bundle>.tar.zst` |

Before uploading anything, list what's already there and confirm no name of yours is taken:

```bash
az storage blob list --container-name "$CONTAINER_NAME" --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login --query "[].name" -o tsv | sort
```

If a name you intend to write already exists, **change your `$PROJECT`/`$STAMP`, do not
`--overwrite`.** Reserve `--overwrite` for re-running *your own* upload after a failure.

> **Backups already in this container (do not overwrite):**
> `backup.tar`, `ctx_editor_full_snapshot_2026-06-12.tar.gz`,
> `project_preservation_supplementary_2026-06-12.tar.gz`, and the
> `*_2026-08-12.*` set from `GCRAZGDL1739`.

If you'd rather have hard separation than a naming convention, make your own container —
you keep the same commands, just a different `$CONTAINER_NAME`:

```bash
export CONTAINER_NAME=<yourname>-<project>
az storage container create --name "$CONTAINER_NAME" \
  --account-name "$STORAGE_ACCOUNT" --auth-mode login
```

---

## 1. Authenticate

```bash
az account show          # if this prints your subscription, you're already logged in
```

If not:

```bash
az login --use-device-code
```

`--use-device-code` is the reliable path on a headless VM — it prints a code you paste into
`https://microsoft.com/devicelogin` from your laptop. Expect subscription
**Deep Learning Group** (`2cd190bb-b42a-477c-b1bb-2f20932d8dc5`).

Confirm the container is reachable *before* spending time on tarballs:

```bash
az storage blob list \
  --container-name "$CONTAINER_NAME" \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --query "[].{name:name, bytes:properties.contentLength, modified:properties.lastModified}" \
  -o table
```

If this 403s, your `az login` didn't pick up the right tenant, or you lack
**Storage Blob Data Contributor** on the account. Fix that first — `--auth-mode login` uses
your AAD identity, not an account key.

---

## 2. Survey the node

Know what you're saving and what it costs. Virtualenvs and public datasets dominate disk but
are worthless in a backup.

```bash
df -h                                          # which disks exist, which are ephemeral
du -sh $HOME/* $HOME/.claude 2>/dev/null | sort -h
du -sh $HOME/*/*/ 2>/dev/null | sort -h | tail -25
find $HOME -maxdepth 4 -name .git -type d      # every repo
find $HOME -maxdepth 4 -name '.venv' -o -maxdepth 4 -name 'node_modules'   # the fat, skippable stuff
```

For each repo, check what would be lost if the disk vanished:

```bash
for r in $(find $HOME -maxdepth 4 -name .git -type d | xargs -n1 dirname); do
  echo "=== $r"; git -C "$r" status -sb | head -5
done
```

`## main...origin/main [ahead N]` means N commits exist only on this box.
Untracked files (`??`) exist only on this box, always.

### Rule of thumb

| Include | Exclude |
|---|---|
| Source repos **with `.git`** | `.venv/`, `node_modules/`, `__pycache__` |
| Experiment outputs / run logs | Public datasets (Spider, HF caches) |
| Uncommitted + unpushed work | Clones of public repos |
| `~/.claude/` (transcripts, memory, skills) | `~/.cache`, `~/.npm`, `~/.vscode-server` |
| Dotfiles (`.bashrc`, `.tmux.conf`, `.vim*`) | Anything already sitting in the blob |
| Gitignored dirs — these are **not** on GitHub | Older backup tarballs staged locally |

The last one on the left is the trap: a gitignored path (e.g. a nested Overleaf clone) is in
neither your GitHub backup nor your repo tarball unless you deliberately include it.

---

## 3. Push what git can hold (cheap redundancy, do it first)

A push is incremental, instant, and independent of the blob.

```bash
cd <repo> && git add -A && git commit -m "chore: checkpoint before maintenance window"
git push origin main
```

### Multiple GitHub identities

Corporate (EMU) and personal accounts need different keys on the same host. Find out which
key is which:

```bash
for k in ~/.ssh/id_*; do
  case "$k" in *.pub) continue;; esac
  printf "%-28s => " "$k"
  ssh -o IdentitiesOnly=yes -i "$k" -T git@github.com 2>&1 | head -1
done
```

Then pin the right key **per repo** (don't use a global `~/.ssh/config`, it will break the
other account since both are on `github.com`):

```bash
git -C <repo> config core.sshCommand 'ssh -i ~/.ssh/id_ed25519_deux -o IdentitiesOnly=yes'
```

A `Repository not found` or `Permission ... denied` from GitHub usually means the **wrong key
was offered**, not that access was revoked. Check identities before concluding you're locked out.

**Note:** SSH keys are not backed up (see §4). After restore you must `ssh-keygen -t ed25519`
and add the new public key at <https://github.com/settings/keys>. Repos restore fine either
way — only pushing needs the key.

---

## 4. Build the archives

`tar` + `zstd`, multithreaded, rooted at `$HOME` so paths inside are relative
(`ac3/...`, `.claude/...`). One archive per logical unit — a failed upload then costs you one
bundle, not all of them.

```bash
mkdir -p "$STAGE"
cd "$HOME"

EX="--exclude=.venv --exclude=venv --exclude=__pycache__ --exclude=.mypy_cache \
--exclude=.ruff_cache --exclude=.pytest_cache --exclude=node_modules --exclude=.ipynb_checkpoints"
```

**The bundle list below is `ac3`-specific — replace the paths with your own project's.** Only
the last one (`home_config`) is universal; keep it on every node.

```bash
# one project repo (note the extra exclude for a big public dataset)
tar -I 'zstd -T8 -3' $EX --exclude=ac3/ctx_editor/data/spider \
    -cf "$STAGE/${PREFIX}_ctx_editor.tar.zst" ac3/ctx_editor

# an outputs-only snapshot
tar -I 'zstd -T8 -3' $EX -cf "$STAGE/${PREFIX}_t14_snapshot.tar.zst" ac3/t14_snapshot

# another repo, plus odds and ends
tar -I 'zstd -T4 -3' $EX -cf "$STAGE/${PREFIX}_tau2_ctxe.tar.zst" \
    ac3/tau2_ctxe ac3/recovered ac3/recovered_t20 ac3/recovered_t2c

tar -I 'zstd -T4 -3' $EX -cf "$STAGE/${PREFIX}_msho_intern26.tar.zst" msho-intern-26

# UNIVERSAL — Claude state + dotfiles + small side repos. NO secrets (see below).
tar -I 'zstd -T8 -3' $EX --exclude=harness_understanding/code_ref \
    -cf "$STAGE/${PREFIX}_home_config.tar.zst" \
    .claude .bashrc .profile .zshrc .bash_history .bash_logout \
    .tmux.conf .tmux .vim .viminfo .config .agents
```


`-T8` = 8 compression threads. Bump toward `nproc` if you're not running anything else;
several `tar`s in parallel will saturate disk read anyway. `-3` is zstd's default level —
roughly 10× on JSON/logs at ~250 MB/s. Don't reach for `-19`; you'll spend 20× the CPU for a
few percent.

Run the big ones concurrently with `&` and `wait`, or in the background with `nohup`.

### Secrets — decide deliberately

The container may live in **someone else's storage account**. Anyone with access reads
whatever you put there. So by default, **exclude**:

```
~/.ssh          private keys
~/.env          API tokens (HF_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY, ...)
~/.azure        cached AAD tokens
~/.claude.json  OAuth/account state
```

All four are cheap to recreate: `ssh-keygen` + paste the pubkey into GitHub, `az login`,
re-fetch tokens. That's minutes, versus leaking a credential.

If you must carry them, encrypt first — never plain:

```bash
tar -I 'zstd -T4 -3' -cf - .ssh .env .azure .claude.json \
  | openssl enc -aes-256-cbc -pbkdf2 -salt -out "$STAGE/${PREFIX}_secrets.tar.zst.enc"
# restore: openssl enc -d -aes-256-cbc -pbkdf2 -in <file>.enc | tar -I zstd -xf - -C $HOME
```

Sanity-scan before uploading either way:

```bash
grep -rIl -E 'sk-[A-Za-z0-9]{20}|hf_[A-Za-z0-9]{20}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' \
  ~/.claude ~/.config ~/.bash_history 2>/dev/null
```

---

## 5. Verify locally, then checksum

Catching a bad archive now is far cheaper than discovering it after the node is gone.

```bash
cd "$STAGE"
for f in *.tar.zst; do printf "%-52s " "$f"; zstd -t "$f" 2>&1 | tail -1; done

# spot-check that excludes worked and the important paths are actually inside
tar -tf ${PREFIX}_ctx_editor.tar.zst | grep -c '\.venv/'                 # expect 0
tar -tf ${PREFIX}_ctx_editor.tar.zst | grep -c 'writing/overleaf_repo/'  # expect > 0
tar -tf ${PREFIX}_home_config.tar.zst | grep -cE '^\.(ssh|env|azure)'    # expect 0
tar -tf ${PREFIX}_home_config.tar.zst | grep -c '\.claude/projects/.*\.jsonl'

md5sum    *.tar.zst > ${PREFIX}_MD5SUMS.txt
sha256sum *.tar.zst > ${PREFIX}_SHA256SUMS.txt
```

Write a `${PREFIX}_MANIFEST.md` next to them recording: node name, date, what each archive
holds, **what you deliberately excluded and why**, and the git state (branch, SHA,
ahead/behind, uncommitted files) of every repo. Six months later the exclusion list is the
part you'll actually need.

---

## 6. Upload

Names carry `$PREFIX`, so they can't collide with another node's set. `--overwrite` is then
only ever re-writing your own file after a failed attempt.

```bash
cd "$STAGE"
for f in *.tar.zst ${PREFIX}_MD5SUMS.txt ${PREFIX}_SHA256SUMS.txt ${PREFIX}_MANIFEST.md; do
  echo "=== $f"
  az storage blob upload \
    --account-name "$STORAGE_ACCOUNT" --container-name "$CONTAINER_NAME" \
    --name "$f" --file "$f" \
    --auth-mode login --overwrite --no-progress -o none || echo "FAILED: $f"
done
```

Also upload this guide itself, so a bare node can bootstrap from the container alone:

```bash
az storage blob upload --account-name "$STORAGE_ACCOUNT" --container-name "$CONTAINER_NAME" \
  --name BACKUP_RESTORE_GUIDE.md --file BACKUP_RESTORE_GUIDE.md --auth-mode login --overwrite
```

Multi-GB uploads take a while; run under `tmux` or `nohup` so a dropped SSH session doesn't
kill them. `az` chunks large blobs and retries internally, but a killed process is still a
killed process. If one fails, re-run just that file — uploads are idempotent.

---

## 7. Verify the upload — do not skip

Azure stores an MD5 for blobs uploaded in one shot. Compare remote against local:

```bash
az storage blob list \
  --container-name "$CONTAINER_NAME" --account-name "$STORAGE_ACCOUNT" --auth-mode login \
  --query "[?starts_with(name,'$PREFIX')].{name:name, bytes:properties.contentLength, md5:properties.contentSettings.contentMd5}" \
  -o table
```

Sizes must match `ls -l` exactly. The `md5` column is **base64**, not hex — convert a local
hash to compare:

```bash
openssl dgst -md5 -binary ${PREFIX}_ctx_editor.tar.zst | base64
```

For blobs uploaded in chunks (roughly >256 MB) the `md5` field comes back **empty**. That's
normal and expected — Azure only stores `Content-MD5` for single-shot puts. Verify those by
downloading them back and hashing:

```bash
mkdir -p /tmp/rt && cd /tmp/rt
for f in <the big ones>; do
  az storage blob download --account-name "$STORAGE_ACCOUNT" --container-name "$CONTAINER_NAME" \
    --name "$f" --file "$f" --auth-mode login --no-progress -o none
done
md5sum *.tar.zst                       # compare against ${PREFIX}_MD5SUMS.txt
cd - && rm -rf /tmp/rt
```

Only after this passes should you delete `$STAGE`.


---

## 8. Restore on a fresh node

```bash
export STORAGE_ACCOUNT=yingxinwustorage
export CONTAINER_NAME=mshotest
az login --use-device-code

mkdir -p ~/restore && cd ~/restore

# 1. see what's there, and pick the PREFIX belonging to the node you want back
az storage blob list --container-name "$CONTAINER_NAME" --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login --query "[].name" -o tsv | sort

export PREFIX=ac3_GCRAZGDL1739_2026-08-12      # <-- set to the set you're restoring

# 2. read that set's manifest first — it says what is and isn't in these archives
az storage blob download --account-name "$STORAGE_ACCOUNT" --container-name "$CONTAINER_NAME" \
  --name ${PREFIX}_MANIFEST.md --file ${PREFIX}_MANIFEST.md --auth-mode login --no-progress
cat ${PREFIX}_MANIFEST.md

# 3. pull every blob in that set (and only that set)
for f in $(az storage blob list --container-name "$CONTAINER_NAME" \
             --account-name "$STORAGE_ACCOUNT" --auth-mode login \
             --query "[?starts_with(name,'$PREFIX')].name" -o tsv); do
  az storage blob download --account-name "$STORAGE_ACCOUNT" --container-name "$CONTAINER_NAME" \
    --name "$f" --file "$f" --auth-mode login --no-progress -o none && echo "got $f"
done

md5sum -c ${PREFIX}_MD5SUMS.txt      # every line must say OK
```

Extract (archives are `$HOME`-rooted, so extract *into* `$HOME`):

```bash
for f in ${PREFIX}_*.tar.zst; do tar -I zstd -xf "$f" -C "$HOME"; done
```

`tar` overwrites same-named files. On a node with existing work, extract to a scratch dir
(`-C ~/restore/tree`) and merge by hand instead.

### Post-restore checklist

```bash
# 1. secrets (not in the backup, by design)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "$(whoami)@$(hostname)"
cat ~/.ssh/id_ed25519.pub          # add at https://github.com/settings/keys
printf 'HF_TOKEN=...\n' > ~/.env   # plus OPENAI_API_KEY / ANTHROPIC_API_KEY as needed

# 2. per-repo SSH key pinning, if you use two GitHub identities (§3)

# 3. rebuild environments
cd ~/ac3/ctx_editor && pip install -e ".[all]"     # or: uv sync

# 4. re-fetch excluded public data
#    ctx_editor: data/spider  (see src/lic/data/spider/readme.txt)

# 5. confirm repos are intact
for r in ~/ac3/ctx_editor ~/ac3/tau2_ctxe ~/msho-intern-26; do
  echo "=== $r"; git -C "$r" log --oneline -1; git -C "$r" status -sb | head -3
done

# 6. confirm Claude state came back
ls ~/.claude/projects/*/  | head
ls ~/.claude/projects/*/memory/MEMORY.md 2>/dev/null
```

---

## Quick reference

| Task | Command |
|---|---|
| Log in | `az login --use-device-code` |
| List blobs | `az storage blob list -c $CONTAINER_NAME --account-name $STORAGE_ACCOUNT --auth-mode login -o table` |
| Upload | `az storage blob upload --account-name $STORAGE_ACCOUNT -c $CONTAINER_NAME -n F -f F --auth-mode login --overwrite` |
| Download | `az storage blob download --account-name $STORAGE_ACCOUNT -c $CONTAINER_NAME -n F -f F --auth-mode login` |
| Delete | `az storage blob delete --account-name $STORAGE_ACCOUNT -c $CONTAINER_NAME -n F --auth-mode login` |
| Compress | `tar -I 'zstd -T8 -3' -cf out.tar.zst DIR` |
| Test | `zstd -t out.tar.zst` |
| List contents | `tar -tf out.tar.zst` |
| Extract | `tar -I zstd -xf out.tar.zst -C $HOME` |

## Failure modes worth remembering

- **A shared container has no folders.** `--overwrite` with a generic name destroys another
  node's backup. Prefix every blob with `<project>_<node>_<date>`.
- **Gitignored directories are invisible to your GitHub backup.** Nested clones (e.g. an
  Overleaf-connected repo inside a project) exist only on disk. Tar them explicitly.
- **`~/.claude/` is not part of any project.** Project-rooted tarballs miss it entirely, and
  session transcripts are unrecoverable once the node is gone.
- **Wrong SSH key reads as revoked access.** Test each key against `git@github.com` before
  assuming a repo is unreachable.
- **`/mnt` is wiped by maintenance.** Never stage a backup there.
- **An unverified upload is not a backup.** Check sizes and round-trip the chunked (>256 MB)
  archives before deleting the staging directory.

