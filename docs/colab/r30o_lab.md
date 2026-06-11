# r30o-lab

r30o-lab is the operating loop where Colab runs RobotRL training and Codex checks the evidence on a 30-minute rhythm.

## Roles

```text
GitHub
  Durable source of truth for code, notebooks, docs, commits, and small evidence JSON.

Colab /content
  Required r30o workspace for installs, tests, source edits, dry runs, and training.

Google Drive
  Durable artifact store for checkpoints, videos/GIFs, TensorBoard, logs, preflight reports, eval JSON, and sync manifests.

Codex
  Local operator and reviewer: controls the open Colab runtime through colab-mcp, watches evidence, classifies R30O state, and makes r30o execution edits inside `/content/RobotRL-Colab`.
```

Do not run training directly from a Drive-mounted project folder. Drive is the backup and artifact store, not the hot training filesystem.

## Colab-Primary Source Rule

r30o execution is Colab-primary. Local Codex should control an open Colab session through `colab-mcp`; it should not require the local Windows checkout as the edit staging area for r30o runs.

For r30o-driven changes to code, docs, notebooks, run policy, or acceptance criteria:

1. Edit files inside `/content/RobotRL-Colab` through Colab MCP.
2. Run the nearest Colab-side check that can catch the change, such as tests, dry-run, preflight, or a targeted command.
3. Commit and push the Colab-side source edit to GitHub immediately.
4. Continue only from the pushed commit, or start a new run ID when the task contract changed.

The local Windows checkout may still be useful for orchestration, review, or documentation work outside the live r30o execution path. It is not required for Colab execution, and Colab should not wait for local Windows edits followed by a GitHub pull as the normal fix path.

## Local Codex To Colab Access

Local Codex does not SSH into Colab and does not talk to Drive as the training runtime. The access path is:

```text
Codex Desktop
  -> project-scoped MCP server `colab-mcp`
  -> open Colab notebook browser session
  -> attached Colab runtime
  -> shell/Python commands inside `/content/RobotRL-Colab`
```

The project-scoped MCP config is the committed, sanitized `.codex/config.toml`. Keep it free of secrets and user-local tokens so a fresh checkout can reproduce the bridge:

```toml
[mcp_servers.colab-mcp]
command = "uvx"
args = ["git+https://github.com/googlecolab/colab-mcp"]
```

This is only the local bridge. A real browser Colab notebook must still be open, signed in, connected to a runtime, and authorized for Drive mount before r30o-lab can run commands through MCP.

The configured `tool_timeout_sec` is a command timeout, not a training lease. MCP should launch bounded commands that return within `.codex/config.toml` `tool_timeout_sec`; longer training must use repeated bounded chunks, notebook/background execution, or manual polling with explicit artifact sync boundaries. Do not claim a long-lived blocking MCP training call is supervised unless the live tool and timeout actually support it.

A live tool-list check is mandatory at the start gate. Confirm the current `colab-mcp` bootstrap and notebook execution tool names in the active Codex session before relying on them; documentation and tests should not promise exact unverified tool-name stability.

Start gate before r30o-lab:

1. Restart or reload Codex from this project so `.codex/config.toml` is loaded.
2. Confirm the `colab-mcp` bootstrap tool is available.
3. Open the launcher notebook in a normal browser Colab session.
4. Select the intended runtime, usually GPU.
5. Run or approve `drive.mount('/content/drive')` in Colab.
6. Call the MCP bootstrap tool `open_colab_browser_connection`.
7. Continue only after the connection succeeds and notebook execution tools appear in Codex.
8. Use MCP to run commands in `/content/RobotRL-Colab`; use Drive only for synced artifacts.

If `open_colab_browser_connection` returns false, r30o-lab is not ready to start. The fallback is manual/browser notebook execution with the same commands, but then Codex cannot be treated as the live 30-minute runtime operator.

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
   - `Clearly wrong`: stop, make the smallest reversible source change inside `/content/RobotRL-Colab`, run the nearest check, commit and push from Colab immediately, then start a new run ID.
   - `Complete`: preserve artifacts and record the approval boundary.

## Colab MCP Mode

If a real Colab MCP runtime-execution tool is available, use it instead of browser clicks:

```text
Colab MCP executes shell/Python in the runtime.
Google Drive stores artifacts.
GitHub stores source changes.
```

In Colab MCP mode, Codex may edit files inside `/content/RobotRL-Colab`, run tests, run training, and push commits from Colab. Any Colab-side source edit must be committed and pushed immediately before the runtime can be treated as disposable or before a follow-up training run depends on that edit.

If Colab MCP is not available, use the browser launcher notebook to run the same commands. The architecture stays the same.

## MCP-First Operating Contract

Browser control is only the bootstrap fallback for opening Colab, signing in, choosing the runtime, and approving Drive mount. After the runtime is alive, Colab MCP is the preferred control plane for shell and Python commands inside `/content/RobotRL-Colab`.

Keep the notebook small:

1. Mount Drive.
2. Environment setup.
3. Training command. This is the only cell that should be edited repeatedly.
4. Save artifacts to Drive.

Do not add a new cell for every run attempt. The durable history is `docs/recording_handoff_log.md`, `fetch_loop_spec.json`, `eval_results.json`, Drive sync manifests, and Git commits when code or policy changes.

### Daily Usage Reset Start

When Colab daily usage is available again, start with a clean MCP-attached runtime:

1. Use browser control only if needed to open the Drive-hosted launcher, select a GPU runtime, and complete `drive.mount`.
2. Attach Colab MCP to the active runtime before running project commands.
3. In `/content`, clone or fast-forward pull `https://github.com/hojunjeon/RobotRL-Colab.git`.
4. In `/content/RobotRL-Colab`, run setup and preflight:

```bash
python -m pip install -U pip
python -m pip install -e '.[fetch]'
python -m robotrl.cli colab-preflight \
  --output runs/colab/<run_id>/preflight.json \
  --strict
python -m unittest discover -s tests
```

5. Run a dry-run if the code, dependencies, or runtime changed since the last accepted boundary.
6. Start only one bounded training chunk before the first R30O judgment. Prefer `--max-iterations 1` unless the operator explicitly chooses a longer unattended run.
7. Immediately sync the run directory to Drive with `colab-sync`.

The start-of-day goal is not to spend the whole quota blindly. It is to prove that the runtime, install, current Git commit, output directory, and Drive sync path are correct before using most of the available GPU time.

### Automated r30o-lab Cycle

Codex operates the loop from the local PC, using Colab MCP for runtime commands and Drive/Git evidence for decisions:

1. Run or continue one bounded chunk in Colab.
2. Sync artifacts to Drive.
3. Read `preflight.json`, `fetch_loop_spec.json`, `eval_results.json`, checkpoint paths, rollout GIF/video paths, visual approval markers, and sync manifests.
4. Classify exactly one state:
   - `Progress`: continue the same run direction.
   - `Still ambiguous`: keep collecting evidence; do not change code.
   - `Clearly wrong`: stop the current direction, sync artifacts, make the smallest code/config change inside `/content/RobotRL-Colab`, run the nearest Colab-side check, commit and push from Colab immediately, then start a new run ID from a fresh policy or clearly labeled warm start.
   - `Complete`: preserve artifacts, record the acceptance boundary, and stop the training loop.
5. Append a factual handoff entry when the boundary is useful to reconstruct later.

Do not push Git commits for every pure training chunk. Push immediately from Colab when code, notebook, docs, run policy, or acceptance criteria change. Heavy artifacts stay in Drive.

Treat `--resume-from` as a warm start from saved model weights unless the full training state is explicitly preserved. Do not call it an uninterrupted continuation when replay buffer state, runtime process state, or task contract changed.

Use a fresh output directory for every live run ID. `fetch-loop` fails if the output directory already contains run artifacts, even when `--allow-output-dir-reuse` is supplied. `--resume-from` only marks an intentional warm start from saved weights; it does not permit output directory reuse. `--allow-output-dir-reuse` is limited to dry-run local `fetch_loop_spec.json` / `eval_results.json` overwrites.

The default visual approval path is nonblocking visual approval. When a visual-gated chunk reaches review-ready evidence, `fetch-loop` records the pending marker path and video/GIF hash in `eval_results.json`, exits, and lets `colab-sync` upload the evidence before approval. `--wait-for-visual-approval` is only for a supervised blocking wait; do not use it for the normal MCP chunk-and-sync loop.

### User Intervention

If the user interrupts with a new direction while training is running:

1. Do not immediately overwrite code or kill the run unless the user asks for an emergency stop.
2. Use MCP to sync the current run directory to Drive at the nearest safe boundary.
3. Record the current command, run ID, checkpoint, latest eval row, latest GIF/video, and whether the process was stopped or left running.
4. Compare the user direction against the current task contract:
   - Same reward, environment, success gate, observation/action space, HER meaning, and physics: continue or warm-start from the current checkpoint may be acceptable.
   - Any task-defining change: create a new run ID and treat previous checkpoints as evidence or optional transfer, not as the same run.
5. If code/config changes are needed for r30o execution, make them inside `/content/RobotRL-Colab` through MCP, run the nearest tests or dry-run there, then commit and push from Colab immediately.
6. Update only the training cell or MCP command template for the next run. Do not create a trail of stale notebook cells.

User intervention is a decision boundary. The handoff entry should name it as an operator override and state whether the next run is fresh, warm-started, or continuing the same contract.

## Artifact Boundary

A boundary is worth recording when one of these happens:

- Drive mount succeeds for the first time.
- `colab-preflight` writes `preflight.json`.
- A dry run or training chunk syncs to Drive.
- R30O classifies the evidence.
- A run is paused, rejected, approved, or restarted.
- Code/config changes are pushed for the next Colab cycle.

Use `docs/recording_handoff_log.md` for these boundaries.
