# trasgu

`trasgu` is a CLI-first toolkit for fitting vine copulas over structured [Chimera](https://research.tudelft.nl/en/datasets/chimera-a-database-with-regular-vine-matrices-on-4-to-8-nodes/) Zarr matrices. It splits large Chimera matrix collections into chunks, fits each chunk independently, monitors progress, and combines the results into CSV output.

It supports local execution through Snakemake and HPC execution through SLURM profiles.

## Installation

```bash
git clone https://github.com/fernanqv/trasgu.git
cd trasgu
uv sync --frozen --no-dev
```

### GitHub Codespaces

You can try `trasgu` in GitHub Codespaces without installing Python or `uv` locally.

1. Open the repository on GitHub.
2. Click **Code** -> **Codespaces** -> **Create codespace on main**.
3. Wait for the Dev Container setup to finish. It installs `uv` and syncs the locked runtime environment automatically.
4. Run the minimal example:

```bash
cd examples/run_config/minimal
trasgu_run --dry-run
```

The Codespace terminal already uses the project `.venv`, so `trasgu` commands should work without activating the environment manually.

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

For SLURM execution, install the optional SLURM extra:

```bash
uv sync --frozen --extra slurm
```

## Quickstart

```bash
cd examples/run_config/minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

The run writes chunk CSV files to `.trasgu_minimal/` and combines them into `fit_minimal.csv` next to `trasgu.yaml`.

You can also run commands without activating the environment:

```bash
cd examples/run_config/minimal
uv run --project ../../.. --frozen trasgu_run --dry-run
```

## Configuration

Each run directory contains a `trasgu.yaml` file. Relative paths in `trasgu.yaml` are resolved from the run directory.

Minimal example:

```yaml
data_file: ../../inputs/input6_500_gumbel_high.txt
chunk_size: 1000
```

## CLI commands

- `trasgu_run`: run the packaged Snakemake workflow.
- `trasgu_count_chunks`: print the number of chunks.
- `trasgu_time_fit`: estimate time per configured chunk.
- `trasgu_monitor`: show chunk completion status.
- `trasgu_combine`: combine chunk CSV files.
- `trasgu_fit_chunk`: manually fit one chunk.
- `trasgu_get_matrix`: print one Chimera matrix.
- `trasgu_download_zarr`: download Chimera Zarr arrays for offline execution.

All commands support `--help`.

## Documentation

The documentation source lives in `docs/` and is configured by `mkdocs.yml`.

Build locally:

```bash
pip install mkdocs-material
mkdocs build --strict
```

Serve locally:

```bash
mkdocs serve
```

Start with:

- [Getting started](docs/getting-started.md)
- [Run configuration](docs/run-configuration.md)
- [CLI reference](docs/cli-reference.md)
- [SLURM and HPC](docs/slurm-hpc.md)
- [Troubleshooting](docs/troubleshooting.md)

## Development

```bash
uv sync --frozen
pytest
ruff check .
```
