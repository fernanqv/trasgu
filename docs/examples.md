# Examples

Example run directories live under `examples/run_config/`. Each directory contains a `trasgu.yaml` file for one common situation.

## Choosing an example

| Situation | Example | Shows |
| --- | --- | --- |
| First local run | `examples/run_config/minimal` | Basic `trasgu.yaml`, default remote Chimera store, default output paths. |
| CSV input or selected columns | `examples/run_config/csv_columns` | Comma-separated `data_file` plus the `columns` option. |
| Local or offline Chimera store | `examples/run_config/local_chimera` | `trasgu_url` pointing to a local `chimera.zarr`. |
| Custom fitting controls | `examples/run_config/custom_controls` | `controls_file` with a pickled `pyvinecopulib.FitControlsVinecop` object. |
| Larger local run | `examples/run_config/parallel_local` | Larger input, larger `chunk_size`, `max_workers`, and `debug`. |
| Cluster execution | `examples/snakemake_profiles` | Snakemake profile files for SLURM-style execution. |

## Minimal local run

```text
examples/run_config/minimal
```

Use this first. It contains a small run configuration. Intermediate chunks are written to `.trasgu_minimal`, and the default combined output is `fit_minimal.csv`.

```bash
cd examples/run_config/minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
```

Use `trasgu_monitor` to inspect which chunk files exist, and `trasgu_combine` to combine chunk CSV files into the final CSV if needed.

## CSV input with selected columns

```text
examples/run_config/csv_columns
```

This example uses a comma-separated input file with eight columns and selects four variables:

```yaml
data_file: ../../inputs/input8_100_gauss_low.csv
columns: [1, 3, 5, 7]
chunk_size: 1000
```

Use this when your input data has more variables than you want to fit, or when you want to confirm how CSV parsing and 1-based column selection work.

## Local Chimera Zarr

```text
examples/run_config/local_chimera
```

This example uses `trasgu_url` to point to a local Chimera Zarr store:

```yaml
trasgu_url: /scratch/user/chimera.zarr
```

Use this after downloading Chimera with `trasgu_download_zarr /scratch/user`, or when running on compute nodes without external HTTP access.

## Custom controls

```text
examples/run_config/custom_controls
```

This example loads a pickled `pyvinecopulib.FitControlsVinecop` object from `controls_file`.

The repository includes `examples/controls/controls.pkl` and the helper script used to create it:

```text
examples/controls/controls_management.py
```

Use this when you need to change the vine fitting controls, such as the family set, selection criterion, or parametric method.

## Larger local run

```text
examples/run_config/parallel_local
```

This example uses a larger input and more workers:

```yaml
data_file: ../../inputs/input7_500_gumbel_high.txt
chunk_size: 20000
max_workers: 16
debug: true
```

Use it after validating installation and data access with the minimal run. It is a better starting point for tuning `chunk_size` and `max_workers` on a local workstation.

## Snakemake profiles

Example profiles live under:

```text
examples/snakemake_profiles
```

Use these as references for cluster-specific Snakemake configuration. They are not run directories by themselves; use them with a run configuration:

```bash
cd examples/run_config/minimal
trasgu_run --profile ../../snakemake_profiles/unican.yaml --dry-run
```
