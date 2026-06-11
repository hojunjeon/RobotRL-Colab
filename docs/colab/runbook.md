# RobotRL-Colab Runbook

## Purpose

RobotRL-Colab moves the active work from local Windows/WSL training into a Colab-friendly loop while preserving `RobotRF` and `RARL` as references.

The old checkpoints are not present in this clone. Treat the migrated run history as design evidence, not a resumable model state.

## Artifact Layout

Use this repository for code and lightweight evidence:

```text
runs/colab/<run_id>/
  preflight.json
  fetch_loop_spec.json
  eval_results.json
  checkpoints/          # ignored by git
  videos/               # ignored by git
  tensorboard/           # ignored by git
  logs/                  # ignored by git
```

Use Google Drive for durable heavyweight artifacts:

```text
MyDrive/RobotRL-Colab/artifacts/<run_id>/
  checkpoints/
  videos/
  tensorboard/
  logs/
```

After a dry run, chunk, or stopped run reaches a preservation boundary, copy the local run directory to Drive:

```bash
python -m robotrl.cli colab-sync \
  --run-dir runs/colab/run_001_stage1_strict_withdraw_seed7 \
  --drive-artifact-root /content/drive/MyDrive/RobotRL-Colab/artifacts
```

The sync command copies specs, eval JSON, models, checkpoints, videos, TensorBoard data, and logs when those entries exist. It also writes `drive_sync/manifest.json` locally and `drive_sync_manifest.json` under the Drive run folder.

By default, `colab-sync` fails closed for Colab-local artifact roots under `/content` unless they are under a mounted `/content/drive`, and it refuses to merge into an existing same-name destination. Use `--allow-unmounted-drive` only for local tests or an explicit non-Drive, non-default artifact root. Use `--allow-merge` only when intentionally merging into an existing Drive run folder.

## r30o-lab Runtime Split

r30o-lab uses GitHub, Colab, Drive, and Codex for different jobs:

```text
GitHub: code, docs, notebooks, and commits
Colab /content: required r30o execution and edit workspace
Google Drive: artifact store
Local Codex: 30-minute operator and reviewer through colab-mcp
```

Do not run the project directly from `/content/drive/MyDrive/...`. Use Drive for artifacts and backups only. In Colab, clone or pull into `/content/RobotRL-Colab`, install there, write run outputs there, and sync run directories to Drive at boundaries.

The r30o execution path is Colab-primary. The local Windows checkout is optional orchestration and review state, not a required staging area. If a live r30o run needs code, docs, notebook, run policy, or acceptance-criteria changes, make them inside `/content/RobotRL-Colab` through Colab MCP, run the nearest Colab-side check, then commit and push from Colab immediately before continuing.

If a real Colab MCP runtime-execution tool is available, use it to run the same shell/Python commands in Colab instead of clicking the notebook UI. If it is not available, use `notebooks/RobotRL_Colab_Run.ipynb` as the browser launcher.

For MCP-first operation, follow `docs/colab/r30o_lab.md`, especially the "Local Codex To Colab Access" start gate. Browser control is only the bootstrap fallback for opening Colab, selecting the runtime, and approving Drive mount. Once the runtime is active and `open_colab_browser_connection` succeeds, use MCP for setup, dry runs, bounded training chunks, artifact sync, and status checks.

MCP commands must return within the committed project-scoped `.codex/config.toml` `tool_timeout_sec`. Do not use a long-lived blocking MCP call as the training supervisor. For longer training, launch one bounded command, sync and inspect artifacts, then continue through another bounded command or an explicit notebook/background/manual polling contract. A live tool-list check is mandatory before relying on MCP; tool names can change, so tests only guard the docs/notebook basics and the operating contract.

## First Colab Run

After installing `.[fetch]`, record the runtime before tests or training:

```bash
python -m robotrl.cli colab-preflight \
  --output runs/colab/dry_run_stage1_strict_withdraw_seed7/preflight.json \
  --strict
```

Start with a dry run:

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

Then run a fresh baseline. For r30o-lab, prefer one bounded chunk per judgment cycle:

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

Sync the run folder to Drive after each completed chunk, pause, rejection, or approval marker update before changing direction.

Use a fresh output directory for each live run ID. `fetch-loop` rejects populated output directories even when `--allow-output-dir-reuse` is supplied. `--resume-from` only selects warm-start weights and never permits output directory reuse. `--allow-output-dir-reuse` is limited to dry-run local `fetch_loop_spec.json` / `eval_results.json` overwrites.

Visual approval is nonblocking by default. When a visual-gated bounded chunk reaches review-ready evidence, `fetch-loop` writes the pending marker path and artifact hash to `eval_results.json` and exits so `colab-sync` can upload the GIF/video, JSON, checkpoints, and manifest before approval. Use `--wait-for-visual-approval` only for a supervised blocking wait.

## Decision Rules

- Continue when progress is visible and the visual/telemetry gates are not contradicted.
- Hold when the evidence is ambiguous.
- Branch or restart when the current direction is clearly wrong.
- Do not hot-change reward, success contracts, observation/action spaces, HER semantics, or physics during a run.
- If those change, create a new run ID and record the boundary in `docs/recording_handoff_log.md`.

## Migration Notes

- `docs/RARL_migrated_README.md` preserves the old RARL README.
- `runs/` contains lightweight migrated JSON/PNG evidence.
- No old `.zip` checkpoints, videos, TensorBoard event files, or logs were present after cloning.

