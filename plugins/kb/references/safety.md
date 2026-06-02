# KB Registry — Safety Rules

## Path safety

- All KB paths are resolved to absolute real paths.
- Path traversal outside KB root is rejected (exit 3).
- Absolute paths are rejected for `open` commands.
- Symlinks are resolved before path checks on write operations.

## Secrets are agent guidance, not CLI-enforced

v0 does not scan staged content for secrets. Pattern matching is not a credible defense and produces too many false positives on docs that legitimately mention credential-shaped strings.

Agents must still treat "do not stage secrets" as a rule (see `AGENTS.md` in each KB). KBs that may receive sensitive material should be kept on private remotes.

## Canonical write protection

v0 does not write to `knowledge/` except during template creation.
All agent writes go to `inbox/` only.

## Binary and large files

- Plain binary files are rejected for staging.
- Extractable document formats (`.pdf`, `.docx`, `.pptx`, `.xlsx`,
  `.epub`, `.html`) are converted to Markdown via `markitdown` when it is
  available. The extracted text is staged; the original is copied to
  `sources/` only with `--keep-source`.
- Text files over 1 MB trigger a warning; rejected without `--force`.

## Git safety

- `kb stage` rejects unsupported binaries and warns on text files over 1 MB (override with `--force`).
- `kb stage` stages and commits only the newly created inbox/source files, never the whole KB.
- `kb sync` stops on any dirty working tree in v0.
- `kb remove --delete-local` refuses dirty KBs unless `--force` is explicitly provided.
- No destructive git commands (reset --hard, force push, etc.).
- Conflicts stop the operation — no auto-resolution.
