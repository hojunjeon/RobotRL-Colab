---
name: r30o-adversarial-review
description: Run a multi-model adversarial review for RobotRL-Colab r30o-lab and Colab/MCP workflow changes. Use when reviewing r30o-lab operating contracts, Colab notebooks, Drive artifact paths, visual approval, checkpoint/resume semantics, MCP setup, handoff logs, Git hygiene, or any RobotRL-Colab workflow where failures would waste GPU time or corrupt training evidence.
---

# R30O Adversarial Review

Use this skill to pressure-test RobotRL-Colab workflow changes before running live Colab GPU sessions.

The goal is not only to find problems. Every finding must include a practical fix and a verification check.

## Workflow

1. Inspect current state:
   - `git status --short`
   - current diff for `docs/colab/`, `notebooks/`, `.codex/`, `robotrl/`, `tests/`, and `docs/recording_handoff_log.md`
   - whether generated review outputs under `.omx/` are ignored
2. Launch independent reviewers:
   - Codex subagent with model `gpt-5.5`
   - Antigravity CLI with model `Claude Sonnet 4.6 (Thinking)`
   - Antigravity CLI with model `Gemini 3.5 Flash (High)`
3. Require each reviewer to return:
   - severity
   - file/line evidence
   - why it matters
   - recommended fix
   - verification test
   - prioritized remediation plan
4. As orchestrator, verify findings against source code. Mark each item:
   - confirmed
   - partially confirmed
   - not reproduced
   - out of scope
5. Produce a final report grouped by risk, not by reviewer.
6. If this is a meaningful work unit, append `docs/recording_handoff_log.md` using the project-local handoff convention.

## Review Surfaces

Always inspect these when present:

- `docs/colab/r30o_lab.md`
- `docs/colab/runbook.md`
- `docs/recording_handoff_log.md`
- `.codex/config.toml`
- `notebooks/RobotRL_Colab_Run.ipynb`
- `tests/test_colab.py`
- `robotrl/cli.py`
- `robotrl/colab.py`
- `robotrl/fetch_training.py`
- `.gitignore`
- `uv.lock` state

Read `references/review-contract.md` before writing the final report.

Use `scripts/extract_agy_review.py` to recover Antigravity print-mode results from transcript files when `agyd --prompt` returns empty stdout.

## Antigravity Model Labels

Use exact labels:

```text
Claude Sonnet 4.6 (Thinking)
Gemini 3.5 Flash (High)
```

Do not use shorthand labels like `sonnet`, `3.5flash`, or `Claude Sonnet 4.5`; they can silently fall back to another model.

Verify model resolution by checking the agy log for:

```text
Propagating selected model override to backend: label="..."
```

## Adversarial Focus

Look especially for:

- visual approval waiting before Drive sync
- unbounded notebook fallback commands
- `git pull ... || true` hiding stale code
- Drive run ID collisions or silent artifact merging
- warm-start/resume being mislabeled as full continuation
- checkpoint, replay buffer, stage index, and curriculum mismatch
- untracked `.codex/config.toml`, `uv.lock`, or docs that handoff claims as done
- tests that check only string presence instead of safety contracts
- MCP timeout shorter than expected training/approval waits
- hardcoded paths, repo URLs, branches, or run IDs
- missing Drive mount validation

## Final Report Rules

Lead with confirmed risks. Do not bury execution blockers behind model-by-model summaries.

For every confirmed issue include:

```text
Severity:
Evidence:
Why it matters:
Fix:
Verification:
Reviewer agreement:
```

End with:

- immediate stop/go recommendation
- next three fixes in order
- what was not verified live
