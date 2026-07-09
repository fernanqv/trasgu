# Run configuration

Each run is configured by a `trasgu.yaml` file in the directory where the command is executed. This directory is the run directory.

Relative paths in `trasgu.yaml` are resolved from the run directory. Absolute paths are used unchanged.

`trasgu` fits a matrix collection by splitting it into chunks. The configuration decides what data to fit, where intermediate chunk outputs go, and how much work each chunk contains.

## Minimal example

```yaml
data_file: ../../inputs/input6_500_gumbel_high.txt
chunk_size: 1000
```

## Fields

| Field | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data_file` | Yes | string | none | Input numerical matrix. Rows are observations and columns are variables. Supported formats are whitespace-delimited text, CSV, TSV, and NumPy `.npy`. |
| `columns` | No | list of integers | all columns | 1-based column indices to select from `data_file`, in the order to use them. |
| `chunk_size` | No | integer | `30000` | Number of Chimera matrices fitted per chunk. |
| `output_dir` | No | string | `.trasgu_<run>` | Advanced option for the chunk work directory. Relative paths are resolved from the run directory. |
| `max_workers` | No | integer | `1` | Number of local worker processes used inside each chunk. |
| `controls_file` | No | string | built-in controls | Pickled `pyvinecopulib.FitControlsVinecop` object. |
| `trasgu_url` | No | string | remote Chimera Zarr | URL or local path to a Chimera Zarr store. |
| `debug` | No | boolean | `false` | Enables debug logging when true. |

## Path handling

These fields accept run-directory-relative paths:

- `data_file`
- `output_dir`
- `controls_file`
- `trasgu_url`, when it is a local path rather than a URL

Example:

```yaml
data_file: ../../inputs/input6_500_gumbel_high.txt
output_dir: fit_results
controls_file: ../../controls/controls.pkl
trasgu_url: /scratch/user/chimera.zarr
```

If `output_dir` is omitted, chunk CSV files are written to `.trasgu_<run>`.
The combined CSV is written next to `trasgu.yaml` as `fit_<run>.csv` by default.

## Chimera matrix counts

`trasgu` infers the number of variables from the columns in `data_file` and selects the matching Chimera matrix collection.

| Variables | Chimera matrices |
| --- | ---: |
| 4 | 12 |
| 5 | 480 |
| 6 | 23,040 |
| 7 | 2,580,480 |
| 8 | 660,602,880 |

These totals are used by `trasgu_count_chunks` together with `chunk_size`.

## Input data formats

`data_file` must point to a 2D numerical matrix. Rows are observations and columns are variables.
Trasgu supports at most 8 variables after any column selection.

Supported formats:

- `.txt`, `.dat`, or any other text extension with whitespace-separated values
- `.csv` with comma-separated values
- `.tsv` with tab-separated values
- `.npy` NumPy arrays

Text files may contain comment lines starting with `#`. Header rows are not supported unless they are commented.

Use `columns` to select a subset of variables from wider input files. Column indices are 1-based and preserve the order provided:

```yaml
data_file: data.csv
columns: [1, 3, 5, 7]
```

If `columns` is omitted and the input has more than 8 variables, Trasgu raises an error and asks you to choose a supported subset.

## Choosing `chunk_size`

`chunk_size` is the main lever for planning a run. It controls how many Chimera matrices are fitted in each independent chunk.

Smaller chunks are easier to rerun and monitor. Larger chunks reduce scheduling overhead but produce longer individual jobs. On HPC systems, this also controls the granularity of the jobs submitted by the workflow.

For local testing, start small:

```yaml
chunk_size: 1000
```

Before running the full workflow, inspect the configured split:

```bash
trasgu_count_chunks
```

Then estimate the runtime for one configured chunk:

```bash
trasgu_time_fit
```

`trasgu_count_chunks` prints how many chunks the current `trasgu.yaml` will produce. `trasgu_time_fit` samples 100 matrices and scales the result to the configured `chunk_size` and `max_workers`.

A practical loop is:

1. Set an initial `chunk_size` in `trasgu.yaml`.
2. Run `trasgu_count_chunks`.
3. Run `trasgu_time_fit`.
4. Adjust `chunk_size` until the number of chunks and estimated time per chunk fit your local or HPC constraints.

## Choosing `max_workers`

For local runs, `trasgu_run` passes `max_workers` to Snakemake as `--cores`. Within each chunk, `trasgu` uses up to `max_workers` worker processes.

For SLURM runs, resource allocation is controlled by the Snakemake profile and cluster configuration.
