# KB Registry — Safety Rules

## Path safety

- All KB paths are resolved to absolute real paths.
- Path traversal outside KB root is rejected (exit 3).
- Absolute paths are rejected for `open` commands.
- Symlinks are resolved before path checks on write operations.

## Secret scanning

Before staging content, the CLI scans for likely secrets:

- AWS access keys (`AKIA...`)
- AWS secret access key assignments
- Private keys (`BEGIN PRIVATE KEY`)
- GitHub tokens (`ghp_`, `gho_`, `ghs_`, `github_pat_`)
- OpenAI/Anthropic API keys (`sk-`, `sk-ant-`)
- Generic credential patterns (`password=`, `token=`, `secret=`, `api_key=`)

If detected:
- Rejected by default (exit 3).
- `--force` overrides the check.
- A metric event is recorded with `safety_rejected: true`.
- Secret values are never printed in output.

## Canonical write protection

v0 does not write to `knowledge/` except during template creation.
All agent writes go to `inbox/` only.

## Binary and large files

- Binary files are rejected for staging.
- Files over 1 MB trigger a warning; rejected without `--force`.

## Git safety

- `kb stage` stages and commits only the newly created inbox note, never the whole KB.
- `kb sync` stops on any dirty working tree in v0.
- `kb remove --delete-local` refuses dirty KBs unless `--force` is explicitly provided.
- No destructive git commands (reset --hard, force push, etc.).
- Conflicts stop the operation — no auto-resolution.
