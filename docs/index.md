# trasgu

`trasgu` fits vine copulas over large collections of structured matrices from the [Chimera](https://research.tudelft.nl/en/datasets/chimera-a-database-with-regular-vine-matrices-on-4-to-8-nodes/) project. Its goal is to make many matrix fits practical: split the collection into chunks, fit those chunks independently, and run the work locally or in parallel on HPC systems. The resulting CSV files can be monitored and combined.

The package is CLI-first and can run locally through Snakemake or on HPC systems with SLURM.

Each run is controlled by a `trasgu.yaml` file. The main planning decision is `chunk_size`, which defines how many Chimera matrices are fitted in each independent chunk.

## Typical workflow

```bash
trasgu_examples minimal ./minimal
cd minimal
trasgu_count_chunks
trasgu_time_fit
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

Use `trasgu_count_chunks` to see how many chunks the current `trasgu.yaml` will create, and `trasgu_time_fit` to estimate how long one configured chunk will take. Relative paths in `trasgu.yaml` are resolved from the run directory.

## What to read first

- [Getting started](getting-started.md): install `trasgu`, inspect `trasgu.yaml`, and run the bundled minimal example.
- [Run configuration](run-configuration.md): understand every `trasgu.yaml` field and choose a practical `chunk_size`.
- [Examples](examples.md): choose a runnable example for CSV input, selected columns, local Chimera data, custom controls, local parallelism, or cluster profiles.
- [CLI reference](cli-reference.md): see commands, options, and examples.
- [SLURM and HPC](slurm-hpc.md): run with the packaged SLURM profile.
- [Offline Zarr](offline-zarr.md): prepare clusters without internet access.
