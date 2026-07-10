# Getting started

This guide installs `trasgu` from a fresh checkout, copies a packaged minimal example, inspects the run configuration, and runs it.

`trasgu` is designed to fit many Chimera matrices efficiently. A run starts with a `trasgu.yaml` file, and the first practical question is how to split the matrix collection into chunks so the work can be fitted independently and, when needed, in parallel.

If you only want to try `trasgu`, GitHub Codespaces provides a ready-to-use environment. See [GitHub Codespaces](codespaces.md).

## Install

```bash
git clone https://github.com/fernanqv/trasgu.git
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

## Inspect the run configuration

The minimal example is a run directory: it contains the `trasgu.yaml` file used by the CLI commands and the input file it references.

```bash
trasgu_examples minimal ./minimal
cd minimal
cat trasgu.yaml
```

The file points to the input data and sets the number of Chimera matrices fitted per chunk:

```yaml
data_file: input6_500_gumbel_high.txt
chunk_size: 1000
```

`chunk_size` controls the job size. Smaller chunks are easier to rerun and monitor; larger chunks reduce scheduling overhead but take longer per job.

## Run the minimal example

```bash
trasgu_count_chunks
trasgu_time_fit
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

`trasgu_count_chunks` prints how many chunks this `trasgu.yaml` will create. `trasgu_time_fit` estimates the time for one configured chunk from a small sample before the full run starts.

The workflow writes chunk files to `.trasgu_minimal/` and combines them into `fit_minimal.csv` next to `trasgu.yaml`.

After this works, see [Examples](examples.md) to choose a run directory for CSV input, selected columns, local Chimera data, custom controls, local parallelism, or cluster execution.

## Check the result

```bash
head fit_minimal.csv
```

Expected columns:

```text
vine_id,n_parameters,aic
```

## Run without activating the environment

From the run directory, use `uv run` and point it to the project root:

```bash
uv run --project .. --frozen trasgu_run --dry-run
```
