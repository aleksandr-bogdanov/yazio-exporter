# CLAUDE.md

## Commands

```bash
just setup          # uv sync --all-extras
just test           # run all tests
just test -v        # verbose
just lint           # ruff check src/ tests/
just fmt            # ruff format src/ tests/
just run <args>     # uv run yazio-exporter <args>
just build          # uv build
just clean          # remove build artifacts
```

## IMPORTANT: Pre-commit Checklist

Before EVERY commit, you MUST run these commands and verify they pass:
1. `just fmt` — auto-format all code
2. `just lint` — zero warnings required
3. `just test` — all tests must pass

Do NOT commit if any of these fail.

## Publishing

PyPI publishing is automated via `.github/workflows/publish.yml` using Trusted Publishing (OIDC — no API tokens).

- Triggers on GitHub release published
- Two jobs: `build` (sdist + wheel) → `publish` (upload via OIDC)
- Uses GitHub environment `pypi` with `id-token: write` permission
- Trusted Publisher configured on pypi.org for this repo

To release:
```bash
git tag v0.X.0
git push origin v0.X.0
gh release create v0.X.0 --title "v0.X.0" --generate-notes
```

## Rules

- Never hardcode user credentials in source code
- Token files must have 0600 permissions
- Progress/status messages go to stderr, not stdout
- All dates use YYYY-MM-DD format (ISO 8601)
- Sort output chronologically by date
- Handle missing/null API values gracefully (skip, don't crash)
- Keep `requests` as the only non-stdlib runtime dependency
