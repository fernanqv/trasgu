# Examples

Example run directories live under `examples/run_config/`.

## Minimal local run

```text
examples/run_config/minimal
```

Use this first. It contains a small run configuration. Intermediate chunks are written to `.trasgu_minimal`, and the default combined output is `fit_minimal.csv`.

```bash
cd examples/run_config/minimal
trasgu_run --dry-run
```

## Local Chimera Zarr

```text
examples/run_config/local_chimera
```

This example uses `trasgu_url` to point to a local Chimera Zarr store.

## Custom controls

```text
examples/run_config/custom_controls
```

This example loads a pickled `pyvinecopulib.FitControlsVinecop` object from `controls_file`.

## Larger run

```text
examples/run_config/big
```

This example uses a larger input and more workers. Use it after validating installation and data access with the minimal run.

## Snakemake profiles

Example profiles live under:

```text
examples/snakemake_profiles
```

Use these as references for cluster-specific Snakemake configuration.
