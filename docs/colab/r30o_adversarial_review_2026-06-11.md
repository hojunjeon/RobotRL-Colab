# r30o-lab Adversarial Review - 2026-06-11

## Scope

Reviewed the current uncommitted r30o-lab MCP-first workflow, project-local MCP config, notebook fallback, Drive artifact sync, visual approval path, checkpoint/resume semantics, tests, and handoff state.

Reviewers:

- Codex `gpt-5.5`
- Antigravity `Claude Sonnet 4.6 (Thinking)`
- Antigravity `Gemini 3.5 Flash (High)`
- Local orchestrator verification

Antigravity model labels were verified in logs by `Propagating selected model override to backend`.

## Verdict

Not ready for live Colab GPU time.

The direction is correct, but the current workflow can still stall before evidence reaches Drive, mix run artifacts, or run stale/unbounded notebook commands. Fix the P0/P1 items before spending a new Colab quota window on training.

## Confirmed Findings

### P0 - Visual approval can block before Drive sync

Evidence:

- `robotrl/fetch_training.py` waits inside `fetch-loop` for visual approval before returning.
- The notebook runs `colab-sync` only after `fetch-loop`.
- The MCP-first docs expect Codex to inspect Drive artifacts after a bounded chunk.

Why it matters:

If a rollout is ready for approval, the process can sit in approval polling while the GIF remains only in Colab local disk. Local Codex cannot inspect Drive evidence that has not been synced.

Fix:

- Prefer nonblocking chunk mode: one chunk writes `pending` evidence and exits, then `colab-sync` uploads artifacts, then approval is handled as a separate step.
- Add an approval CLI that writes a valid `.approved.json` marker from a video path and criteria.

Verification:

- Test that `fetch-loop --max-iterations 1` with visual approval required returns promptly and leaves syncable pending evidence.
- Test that the post-sync approval command writes a marker matching the video hash.

### P0 - Notebook fallback still violates the bounded-run contract

Evidence:

- `docs/colab/runbook.md` now recommends `--max-iterations 1`.
- `notebooks/RobotRL_Colab_Run.ipynb` still has the real training command commented out and does not provide a safe fresh/continue pair.
- Current tests only check for broad command presence.

Why it matters:

If MCP is unavailable and the notebook fallback is used, the operator can either stop after dry-run with no next executable path or manually uncomment a stale command that runs longer than intended.

Fix:

- Replace the fallback training section with explicit fresh chunk and continue chunk templates.
- Include `--max-iterations 1`.
- Include `--resume-from {RUN_DIR}/latest_model.zip` for continue.

Verification:

- Extend `tests/test_colab.py` to require `--max-iterations 1`, a resume template, and no suppressed git pull failure.

### P0 - Git pull failure is hidden in the notebook

Evidence:

- Notebook setup uses `git pull --ff-only || true`.

Why it matters:

Colab can continue with stale, divergent, or dirty code while the handoff log claims a current Git boundary.

Fix:

- Remove `|| true`.
- Print `git rev-parse HEAD` after pull and record the commit in `preflight.json` or `fetch_loop_spec.json`.

Verification:

- Test the notebook source does not contain `git pull --ff-only || true`.

### P1 - Drive artifact destinations can silently merge

Evidence:

- `sync_colab_run_artifacts` derives destination only from `source_run_dir.name`.
- It uses `copytree(..., dirs_exist_ok=True)` and overwrites/merges without a collision gate.
- Local reproduction with two different `run_same` sources produced a mixed destination and a manifest pointing only to the second source.

Why it matters:

Run evidence can become non-attributable. A later R30O decision may inspect files from multiple runs as if they were one run.

Fix:

- Reject existing destination by default.
- Add explicit `--allow-merge` only when the operator wants to update the same run.
- Add source commit, run id, and file hashes to the manifest.

Verification:

- Unit test that two different sources with the same folder name fail on the second sync unless merge is explicitly allowed.

### P1 - Resume is not a full continuation

Evidence:

- `SAC.load(..., env=env)` loads model weights but not replay buffer or process state.
- Current workflow language already says warm-start, but execution templates do not enforce safe reuse of an existing output directory.

Why it matters:

Rerunning a populated `RUN_DIR` without `--resume-from` can overwrite artifacts and mix eval history. Running with `--resume-from` is still a warm start unless full training state is saved.

Fix:

- Fail fast when `output_dir` contains run artifacts and neither `--resume-from` nor an explicit fresh-run override is provided.
- Consider saving/loading replay buffer for true continuation, but treat it as an explicit larger artifact policy decision.

Verification:

- Unit test that populated `output_dir` without resume is rejected.
- Unit test that warm-start metadata is recorded in `fetch_loop_spec.json`.

### P2 - MCP config and lockfile contract is unresolved

Evidence:

- `.codex/config.toml` is untracked.
- `uv.lock` is untracked.
- Docs and handoff log describe project-scoped MCP as configured.

Why it matters:

Fresh clones will not reproduce the claimed MCP behavior unless `.codex/config.toml` is committed. If it is local-only, the docs should say so.

Fix:

- Decide explicitly:
  - commit sanitized `.codex/config.toml` and pin `colab-mcp`, or
  - document MCP as local opt-in and remove durable handoff claims.
- Commit or ignore `uv.lock` intentionally.

Verification:

- Fresh clone can run `codex mcp list` and see `colab-mcp`, or docs state manual setup.

### P2 - Tests do not guard the workflow contract

Evidence:

- `tests/test_colab.py` checks broad string presence but not bounded execution, no `|| true`, collision handling, or resume templates.

Fix:

- Add notebook contract tests.
- Add Drive collision tests.
- Add populated output-dir safety tests.

## Model Discussion

Consensus:

- All reviewers agreed that the current workflow is not ready for live Colab training.
- All reviewers converged on the same top risks: visual approval before sync, notebook drift, Git/staleness, artifact collision, and resume ambiguity.

Differences:

- Codex emphasized output-dir reuse and continuation semantics.
- Sonnet emphasized uncommitted project state, untracked `.codex/config.toml`, `uv.lock`, and notebook fallback usability.
- Gemini emphasized runtime failure modes: Drive mount validation, MCP timeout, replay buffer continuity, and approval pipeline deadlock.

Orchestrator judgment:

- Treat visual approval deadlock and artifact collision as execution blockers.
- Treat Git/notebook drift as Colab quota blockers.
- Treat replay-buffer continuation as important but second-phase unless the next plan depends on exact uninterrupted SAC/HER continuation.

## Remediation Order

1. Make bounded chunk completion syncable before approval.
2. Fix notebook fallback: no `|| true`, safe fresh/continue chunk templates, `--max-iterations 1`.
3. Reject Drive destination collisions by default.
4. Add output-dir reuse safety and warm-start metadata.
5. Decide `.codex/config.toml` and `uv.lock` tracking policy.
6. Add regression tests for the above.

## Not Verified

- Live Colab runtime attachment through MCP.
- Real Google Drive mount and sync latency.
- Full `.[fetch]` test matrix in Colab.
- Replay-buffer save/load performance and Drive cost.
