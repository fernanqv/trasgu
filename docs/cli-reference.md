# CLI reference

All commands support `--help`.

Most commands should be run from a directory containing `trasgu.yaml`.

## `trasgu_run`

Run the packaged Snakemake workflow.

```bash
cd examples/run_config/minimal
trasgu_run --dry-run
trasgu_run
trasgu_run --profile slurm
trasgu_run --profile /path/to/snakemake-profile --printshellcmds
trasgu_run --unlock
```

Options:

| Option | Description |
| --- | --- |
| `--profile PROFILE` | Use a Snakemake profile. Use `slurm` for the packaged SLURM profile. |
| `-n`, `--dry-run` | Show the Snakemake plan without running jobs. |
| `--unlock` | Unlock the Snakemake working directory. |

Unknown arguments are passed through to Snakemake.

## `trasgu_count_chunks`

Print the number of chunks for the current configuration.

```bash
trasgu_count_chunks
```

## `trasgu_time_fit`

Estimate the time needed to fit one full chunk.

```bash
trasgu_time_fit
```

The estimate samples 100 matrices and scales to the configured `chunk_size` and `max_workers`.

## `trasgu_monitor`

Show progress based on chunk CSV files.

```bash
trasgu_monitor
trasgu_monitor --watch 30
```

## `trasgu_combine`

Combine chunk CSV files into a single output file.

```bash
trasgu_combine
trasgu_combine --output custom_results.csv
trasgu_combine --delete
```

Options:

| Option | Description |
| --- | --- |
| `-o`, `--output` | Name or path of the combined CSV. Relative paths are resolved from the run directory. |
| `--delete` | Delete chunk CSV files after a successful merge. |

## `trasgu_fit_chunk`

Fit one chunk manually.

```bash
trasgu_fit_chunk 0
trasgu_fit_chunk 23
```

This command is used internally by Snakemake and is useful for debugging or rerunning one missing chunk.

## `trasgu_get_matrix`

Print one Chimera structure matrix.

```bash
trasgu_get_matrix 6 0
trasgu_get_matrix 7 42
trasgu_get_matrix 6 0 --url /scratch/user/chimera.zarr
trasgu_get_matrix 6 0 --numpy
```

The first argument is the number of variables, which selects the `matricesN` Chimera array. The second argument is the zero-based matrix ID. This command does not read `trasgu.yaml`. Use `--numpy` to print only a copyable `np.array(...)` expression.

## `trasgu_download_zarr`

Download Chimera Zarr arrays for offline or no-network execution.

```bash
trasgu_download_zarr /scratch/user
trasgu_download_zarr /scratch/user --vars 4,5,6,7
trasgu_download_zarr /scratch/user --vars 6 --url http://example.org/chimera.zarr
```

The local store is created or updated as `chimera.zarr` inside the destination directory.

Variable size 8 is very large and requires interactive confirmation.
