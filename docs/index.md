# trasgu

`trasgu` fits vine copulas over structured matrices from the Chimera project. It is designed for large matrix collections: work is split into chunks, each chunk is fitted independently, and the resulting CSV files can be monitored and combined.

The package is CLI-first and can run locally through Snakemake or on HPC systems with SLURM.

## Typical workflow

```bash
cd examples/run_config/minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

Each run directory contains a `trasgu.yaml` file. Relative paths in that file are resolved from the run directory.

## What to read first

- [Getting started](getting-started.md): run the bundled minimal example.
- [Run configuration](run-configuration.md): understand every `trasgu.yaml` field.
- [CLI reference](cli-reference.md): see commands, options, and examples.
- [SLURM and HPC](slurm-hpc.md): run with the packaged SLURM profile.
- [Offline Zarr](offline-zarr.md): prepare clusters without internet access.
