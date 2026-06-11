# R30O Adversarial Review Contract

## Severity

- `P0`: next Colab run can stall, corrupt evidence, use stale code, or lose artifacts.
- `P1`: workflow can waste substantial GPU time or produce misleading handoff state.
- `P2`: reproducibility, debugging, or operator clarity problem that should be fixed soon.
- `P3`: polish or future hardening.

## Minimum Evidence

Each finding needs at least one concrete source:

- file and line reference;
- reproduced command output;
- failed or missing test;
- exact model/log evidence for tool behavior.

Do not accept a reviewer finding only because it sounds plausible. Verify against local files when cheap.

## Common Fix Patterns

- Visual approval deadlock: make bounded chunk return and sync artifacts before approval, or add a pre-wait sync hook.
- Notebook drift: add tests that assert safety flags and forbid `|| true`.
- Drive artifact collision: reject existing destination by default; allow merge only with explicit opt-in.
- Resume ambiguity: label `--resume-from` as warm-start unless replay buffer and task contract are preserved.
- MCP reproducibility: either commit sanitized project-scoped config and pin versions, or document it as local opt-in.
- Handoff mismatch: do not record a boundary as done until the state is committed/pushed or explicitly labeled local-only.

## Final Verdict Language

Use direct language:

- `Ready for live Colab run` only when no P0/P1 execution blockers remain.
- `Ready for dry-run only` when setup can be checked but training should not start.
- `Not ready for Colab GPU time` when approval, artifact, or stale-code risks remain.
