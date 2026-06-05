# RobotRL-Colab Project Rules

These rules apply inside the RobotRL-Colab project and override global defaults when they are more specific.

## Active Workspace Boundary

- RobotRL-Colab is now the active workspace for Colab restructuring.
- Treat sibling folders `..\RobotRF` and `..\RARL` as preserved references.
- Do not continue implementation, documentation edits, or run recording in `..\RobotRF` or `..\RARL` unless the user explicitly redirects the work.
- If old RobotRF/RARL content is needed, migrate or summarize it into RobotRL-Colab first, then work here.

## Flexible Handoff Recording

- For meaningful RobotRL-Colab work units, use the local skill at `skills/robotrl-colab-handoff/SKILL.md`.
- Continue `docs/recording_handoff_log.md` when it is the clearest handoff ledger.
- Do not force the global `docs/recording/YYMMDD-NNN-...md` style for this project when the append-only handoff log is the better continuation point.
- Choose the recording moment with judgment: record when a task reaches a useful boundary, pauses, fails, changes experiment direction, creates a preservation boundary, starts/stops a run, or hands work to another agent/system.
- Keep format flexible. Handoff value matters more than fixed headings.

## Colab Execution Rules

- Prefer chunked training over one long blind run.
- Preserve checkpoints, specs, eval JSON, videos, and visual approval markers at chunk boundaries.
- Treat scalar success as insufficient when visual/telemetry gates are relevant.
- If reward, success contract, observation/action space, HER semantics, or MuJoCo physics changes, branch or restart rather than pretending old checkpoints remain comparable.
