# r30o-lab

r30o-lab is the operating loop where Colab runs RobotRL training and Codex checks the evidence on a 30-minute rhythm.

## Roles

```text
GitHub
  Durable source of truth for code, notebooks, docs, and small evidence JSON.

Colab /content
  Runtime workspace for installs, tests, dry runs, and training.

Google Drive
  Durable artifact store for checkpoints, videos/GIFs, TensorBoard, logs, preflight reports, eval JSON, and sync manifests.

Codex
  Operator and reviewer: watches evidence, classifies R30O state, changes code when needed, and pushes source changes.
```

Do not run training directly from a Drive-mounted project folder. Drive is the backup and artifact store, not the hot training filesystem.

## Preferred Loop

1. Open the launcher notebook in Colab.
2. Mount Drive.
3. Clone or pull `https://github.com/hojunjeon/RobotRL-Colab.git` into `/content/RobotRL-Colab`.
4. Install with `python -m pip install -e '.[fetch]'`.
5. Write `preflight.json` before tests or training.
6. Run a dry run in `/content/RobotRL-Colab/runs/colab/...`.
7. Sync the run directory to `/content/drive/MyDrive/RobotRL-Colab/artifacts`.
8. Codex reads the synced evidence and classifies the state:
   - `Progress`: continue the same run direction.
   - `Still ambiguous`: continue the same run direction and do not change code.
   - `Clearly wrong`: stop, make the smallest reversible code/config change, push it to GitHub, then start a new run ID.
   - `Complete`: preserve artifacts and record the approval boundary.

## Colab MCP Mode

If a real Colab MCP runtime-execution tool is available, use it instead of browser clicks:

```text
Colab MCP executes shell/Python in the runtime.
Google Drive stores artifacts.
GitHub stores source changes.
```

In Colab MCP mode, Codex may edit files inside `/content/RobotRL-Colab`, run tests, run training, and push commits from Colab. Any code change made in Colab must be committed and pushed before the runtime can be treated as disposable.

If Colab MCP is not available, use the browser launcher notebook to run the same commands. The architecture stays the same.

## Artifact Boundary

A boundary is worth recording when one of these happens:

- Drive mount succeeds for the first time.
- `colab-preflight` writes `preflight.json`.
- A dry run or training chunk syncs to Drive.
- R30O classifies the evidence.
- A run is paused, rejected, approved, or restarted.
- Code/config changes are pushed for the next Colab cycle.

Use `docs/recording_handoff_log.md` for these boundaries.
