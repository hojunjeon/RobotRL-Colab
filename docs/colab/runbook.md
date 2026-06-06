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

Then run a fresh baseline:

```bash
python -m robotrl.cli fetch-loop \
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
  --output-dir runs/colab/run_001_stage1_strict_withdraw_seed7
```

Sync the run folder to Drive after each completed chunk, pause, rejection, or approval marker update before changing direction.

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

