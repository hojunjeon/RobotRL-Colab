# RobotRL-Colab

RobotRL-Colab is the Colab-oriented continuation of the RobotRF -> RARL robot-arm learning work.

This repository is the new active workspace. The sibling folders `..\RobotRF` and `..\RARL` are preserved references; do not continue implementation there unless the user explicitly redirects the work.

## Current State

- Source migrated from `..\RARL`.
- Python package name remains `robotrl` for import and CLI compatibility.
- Historical lightweight run evidence was migrated under `runs/`.
- Model checkpoints, videos, TensorBoard event files, and logs were not available in the Git clone and are not present here.
- The latest migrated handoff state is in `docs/recording_handoff_log.md`: run007 was rejected at internal stage 02 and run008 strict withdraw gate had been started.

## Colab Operating Model

Do not try to recover an old policy unless an external checkpoint is supplied. Start from the migrated code and run fresh Colab chunks:

```text
train chunk -> save checkpoint -> evaluate -> inspect metrics/video -> continue or branch
```

For r30o-lab, keep the responsibilities split:

```text
GitHub = source of truth for code, docs, notebooks, and commits
Colab /content = required r30o execution and edit workspace
Google Drive = durable artifact store
Local Codex = 30-minute operator through colab-mcp
```

Do not run training directly from a Drive-mounted project checkout. Clone or pull into `/content/RobotRL-Colab`, run there, then sync artifacts to Drive at dry-run, chunk, pause, rejection, or approval boundaries.

For r30o execution, the local Windows checkout is optional orchestration and review state. It is not required as an edit staging area. When a Colab run needs code, docs, notebook, run policy, or acceptance-criteria changes, make those edits inside `/content/RobotRL-Colab` through Colab MCP, run the nearest Colab-side check, then commit and push from Colab immediately before continuing or treating the runtime as disposable.

The practical Colab default is:

```bash
python -m robotrl.cli fetch-loop \
  --curriculum single-random-to-return \
  --max-iterations 1 \
  --chunk-timesteps 50000 \
  --n-envs 6 \
  --learning-starts 10000 \
  --checkpoint-interval 50000 \
  --eval-episodes 20 \
  --success-threshold 0.8 \
  --seed 7 \
  --visual-approval-timeout-seconds 1800 \
  --visual-approval-poll-interval-seconds 30 \
  --output-dir runs/colab/run_001_stage1_strict_withdraw_seed7
```

Use a dry run before any real training:

```bash
python -m robotrl.cli fetch-loop \
  --dry-run \
  --curriculum single-random-to-return \
  --chunk-timesteps 50000 \
  --n-envs 6 \
  --learning-starts 10000 \
  --checkpoint-interval 50000 \
  --eval-episodes 20 \
  --success-threshold 0.8 \
  --seed 7 \
  --visual-approval-timeout-seconds 1800 \
  --visual-approval-poll-interval-seconds 30 \
  --output-dir runs/colab/dry_run_stage1_strict_withdraw_seed7
```

## Colab Setup

Open `notebooks/RobotRL_Colab_Run.ipynb` in Colab, mount Google Drive, clone this repository, install `.[fetch]`, run tests or a dry run, then start a chunked training run.

Recommended Drive artifact root:

```text
/content/drive/MyDrive/RobotRL-Colab/artifacts/
```

During training, write active output to Colab local disk when possible, then copy run artifacts to Drive at chunk boundaries. Drive is the checkpoint backup, not the hot training filesystem.

If a real Colab MCP runtime-execution tool is available, prefer it over browser clicks for running shell/Python commands in Colab. Local Codex reaches Colab through the committed project-scoped `.codex/config.toml` `colab-mcp` bridge and a live browser Colab notebook session; see `docs/colab/r30o_lab.md` for the required start gate. The architecture remains the same: Colab clones from GitHub into `/content/RobotRL-Colab`, training and r30o-driven edits happen there, artifacts go to Drive, and every Colab-side source edit is committed and pushed back to GitHub immediately.

Colab MCP commands must be bounded enough to return within `.codex/config.toml` `tool_timeout_sec` rather than acting as long-lived blocking training supervisors. For longer training, run one bounded chunk that returns, sync artifacts, and continue through notebook/background/manual polling. A live tool-list check is mandatory before each MCP-operated session; docs and tests guard the operating contract, not exact future MCP tool names.

For visual-gated runs, the default is nonblocking visual approval: when a bounded chunk reaches review-ready evidence, `fetch-loop` records the pending approval marker and artifact hash, exits, and lets `colab-sync` upload the evidence before human or reviewer approval. Use `--wait-for-visual-approval` only for an explicitly supervised blocking wait.

Use a fresh output directory for every live `fetch-loop` run ID. `--allow-output-dir-reuse` is only for dry-run local `fetch_loop_spec.json` / `eval_results.json` overwrite; it does not permit live run append, even with `--resume-from`.

Sync a completed dry run or training chunk to Drive with:

```bash
python -m robotrl.cli colab-sync \
  --run-dir runs/colab/run_001_stage1_strict_withdraw_seed7 \
  --drive-artifact-root /content/drive/MyDrive/RobotRL-Colab/artifacts
```

`colab-sync` refuses Colab-local artifact roots under `/content` unless they are under a mounted `/content/drive`, and refuses to merge into an existing same-name destination unless `--allow-merge` is supplied. Local tests or explicit non-Drive, non-default artifact roots may use `--allow-unmounted-drive`; do not use that flag to bypass a missing Colab Drive mount.

## Important Files

- `robotrl/`: migrated RobotRL package and Fetch training logic.
- `tests/`: migrated regression tests.
- `docs/recording_handoff_log.md`: project handoff ledger.
- `docs/colab/runbook.md`: Colab operating guide.
- `docs/colab/r30o_lab.md`: r30o-lab role split and operating loop.
- `docs/RARL_migrated_README.md`: preserved migrated RARL README.
- `skills/robotrl-colab-handoff/SKILL.md`: local flexible handoff skill for this repo.

## Verification

Local smoke checks:

```powershell
python -m robotrl.cli colab-preflight --output .omx\colab_preflight.json
python -m unittest discover -s tests
python -m robotrl.cli fetch-loop --dry-run --curriculum single-random-to-return --chunk-timesteps 50000 --n-envs 6 --learning-starts 10000 --checkpoint-interval 50000 --eval-episodes 20 --success-threshold 0.8 --seed 7 --visual-approval-timeout-seconds 1800 --visual-approval-poll-interval-seconds 30 --output-dir runs\colab\dry_run_stage1_strict_withdraw_seed7
python -m robotrl.cli colab-sync --run-dir runs\colab\dry_run_stage1_strict_withdraw_seed7 --drive-artifact-root .omx\drive_artifacts --dry-run
```

Colab smoke checks:

```bash
python -m robotrl.cli colab-preflight --output runs/colab/dry_run_stage1_strict_withdraw_seed7/preflight.json --strict
python -m unittest discover -s tests
python -m robotrl.cli fetch-loop --dry-run --curriculum single-random-to-return --chunk-timesteps 50000 --n-envs 6 --learning-starts 10000 --checkpoint-interval 50000 --eval-episodes 20 --success-threshold 0.8 --seed 7 --visual-approval-timeout-seconds 1800 --visual-approval-poll-interval-seconds 30 --output-dir runs/colab/dry_run_stage1_strict_withdraw_seed7
python -m robotrl.cli colab-sync --run-dir runs/colab/dry_run_stage1_strict_withdraw_seed7 --drive-artifact-root /content/drive/MyDrive/RobotRL-Colab/artifacts
```

