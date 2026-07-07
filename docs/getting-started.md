# Getting started

This guide runs the bundled minimal example from a fresh checkout.

## Install

```bash
git clone https://github.com/geoocean/trasgu.git
cd trasgu
uv sync --frozen --no-dev
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

## Run the minimal example

```bash
cd examples/run_config/minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

The workflow writes chunk files to `fit_results/` and combines them into `fit_results/final_results.csv`.

## Check the result

```bash
head fit_results/final_results.csv
```

Expected columns:

```text
vine_id,n_parameters,aic
```

## Run without activating the environment

From the run directory, use `uv run` and point it to the project root:

```bash
uv run --project ../../.. --frozen trasgu_run --dry-run
```
