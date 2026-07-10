# Examples

Packaged examples are copied with `trasgu_examples`. Run examples are self-contained directories: each one contains its own `trasgu.yaml` and local input files.

```bash
trasgu_examples --list
trasgu_examples minimal ./minimal
cd minimal
```

## Choosing an example

| Situation | Example | Shows |
| --- | --- | --- |
| First local run | `minimal` | Basic `trasgu.yaml`, default remote Chimera store, default output paths. |
| CSV input or selected columns | `csv_columns` | Comma-separated `data_file` plus the `columns` option. |
| Local or offline Chimera store | `local_chimera` | `trasgu_url` pointing to a local `chimera.zarr`. |
| Custom fitting controls | `custom_controls` | `controls_file` with a pickled `pyvinecopulib.FitControlsVinecop` object. |
| Larger local run | `parallel_debug` | Larger input, larger `chunk_size`, `max_workers`, and `debug`. |
| Cluster profiles | `profiles` | Snakemake profile files for SLURM-style execution. |

## Minimal local run

```bash
trasgu_examples minimal ./minimal
cd minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
```

Use this first. Intermediate chunks are written to `.trasgu_minimal`, and the default combined output is `fit_minimal.csv`.

## CSV input with selected columns

```bash
trasgu_examples csv_columns ./csv-columns
cd csv-columns
```

This example uses a comma-separated input file with eight columns and selects four variables:

```yaml
data_file: input8_100_gauss_low.csv
columns: [1, 3, 5, 7]
chunk_size: 1000
```

## Local Chimera Zarr

```bash
trasgu_examples local_chimera ./local-chimera
cd local-chimera
```

This example uses `trasgu_url` to point to a local Chimera Zarr store:

```yaml
trasgu_url: /scratch/user/chimera.zarr
```

Use this after downloading Chimera with `trasgu_download_zarr /scratch/user`, or when running on compute nodes without external HTTP access.

## Custom controls

```bash
trasgu_examples custom_controls ./custom-controls
cd custom-controls
```

This example loads a pickled `pyvinecopulib.FitControlsVinecop` object from `controls_file`:

```yaml
controls_file: controls.pkl
```

The copied directory also includes `controls_management.py`, the helper script used to create `controls.pkl`.

## Larger local run

```bash
trasgu_examples parallel_debug ./parallel-debug
cd parallel-debug
```

This example uses a larger input and more workers:

```yaml
data_file: input7_500_gumbel_high.txt
chunk_size: 20000
max_workers: 16
debug: true
```

Use it after validating installation and data access with the minimal run. It is a better starting point for tuning `chunk_size` and `max_workers` on a local workstation.

## Snakemake profiles

Copy cluster profile examples separately:

```bash
trasgu_examples profiles ./profiles
```

Use them with a run directory:

```bash
trasgu_examples minimal ./minimal
cd minimal
trasgu_run --profile ../profiles/unican.yaml --dry-run
```
