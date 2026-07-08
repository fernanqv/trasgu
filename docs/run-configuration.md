# Run configuration

Each run is configured by a `trasgu.yaml` file in the directory where the command is executed. This directory is the run directory.

Relative paths in `trasgu.yaml` are resolved from the run directory. Absolute paths are used unchanged.

## Minimal example

```yaml
data_file: ../../inputs/input6_500_gumbel_high.txt
chunk_size: 1000
```

## Fields

| Field | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data_file` | Yes | string | none | Input numerical matrix. Rows are observations and columns are variables. |
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

## Choosing `chunk_size`

Smaller chunks are easier to rerun and monitor. Larger chunks reduce scheduling overhead but produce longer individual jobs.

For local testing, start small:

```yaml
chunk_size: 1000
```

For large HPC runs, increase it after measuring:

```bash
trasgu_time_fit
```

## Choosing `max_workers`

For local runs, `trasgu_run` passes `max_workers` to Snakemake as `--cores`. Within each chunk, `trasgu` uses up to `max_workers` worker processes.

For SLURM runs, resource allocation is controlled by the Snakemake profile and cluster configuration.
