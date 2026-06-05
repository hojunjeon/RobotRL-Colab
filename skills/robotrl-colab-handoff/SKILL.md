---
name: robotrl-colab-handoff
description: Use for RobotRL-Colab handoff recording. Append factual, project-specific entries to docs/recording_handoff_log.md when a meaningful Colab or RobotRL work unit reaches a useful boundary, without forcing a rigid template.
metadata:
  short-description: Flexible RobotRL-Colab handoff logging
---

# RobotRL-Colab Handoff

Use this skill for RobotRL-Colab project recording.

This project has an established handoff ledger at:

```text
docs/recording_handoff_log.md
```

Prefer continuing that ledger over creating a new `docs/recording/YYMMDD-NNN-...md` file when the work belongs to the ongoing RobotRL/R30O/Colab restructuring story.

## When To Record

Do not record mechanically after every prompt. Record when a meaningful work unit reaches a useful boundary, such as:

- a Colab workspace, notebook, run lane, or Drive artifact boundary is created;
- a run is started, stopped, rejected, approved, or paused;
- evaluation/video/telemetry changes the decision state;
- a preservation rule is established or changed;
- a bug, failed direction, or workaround is understood;
- work is handed off to another agent/system;
- the current state would be expensive to reconstruct later.

Skip recording for tiny conversational turns with no project state change.

## How To Write

Use the shape that best preserves the facts. Do not force a fixed template.

Useful sections often include Evidence, Decision, Changes, Verification, Next, Blockers, or Artifacts. Use only the sections that help.

For Colab work, include:

- whether the run used local Colab disk or Drive;
- checkpoint and artifact paths;
- whether the run was fresh or resumed;
- what was intentionally not migrated or not changed;
- whether scalar metrics were backed by video or telemetry.

## Numbering

When appending to `docs/recording_handoff_log.md`, use the next section number:

```text
## NNN - YYYY-MM-DD KST - concise title
```

Use KST dates for this project unless the user says otherwise.

