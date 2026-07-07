# Development

## Install development tools

```bash
uv sync --frozen
```

## Run tests

```bash
pytest
```

## Run linting

```bash
ruff check .
```

## CLI help tests

The test suite checks that every public CLI command supports `--help` and documents the expected run-directory behavior.

When adding a new entrypoint in `pyproject.toml`, add it to the CLI help tests and to [CLI reference](cli-reference.md).

## Documentation

Documentation source files live in `docs/` and are configured by `mkdocs.yml`.

Serve locally:

```bash
mkdocs serve
```

Build locally:

```bash
mkdocs build --strict
```
