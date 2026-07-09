# Environment setup

## Runtime environment

Install the locked runtime environment with `uv`:

```bash
uv sync --frozen --no-dev
```

If `uv` is not installed yet:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

## Development environment

Install development tools:

```bash
uv sync --frozen
```

## SLURM support

The SLURM executor plugin is optional:

```bash
uv sync --frozen --extra slurm
```

Use this on clusters where you plan to run:

```bash
trasgu_run --profile slurm
```

## Editable pip install

For local package development:

```bash
pip install -e .
```

If you need test tools with pip-based CI, install the project and then install the required tools separately:

```bash
pip install -e .
pip install pytest ruff black
```
