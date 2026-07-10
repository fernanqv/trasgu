# Workflows

`trasgu` is organized around chunk-based processing.

1. Count how many chunks are needed.
2. Fit each chunk.
3. Monitor which chunk files exist.
4. Combine chunk CSV files into one final CSV.

## Recommended workflow

```bash
trasgu_examples minimal ./minimal
cd minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

`trasgu_run` is the recommended entrypoint. It launches the packaged Snakemake workflow and creates the expected chunk files before combining results.

See [Examples](examples.md) for runnable run directories that use this workflow in different situations.

## What `trasgu_run` does

`trasgu_run` is a thin wrapper around [Snakemake](https://snakemake.readthedocs.io/en/stable/). It reads the run configuration from `trasgu.yaml`, locates the packaged `trasgu` workflow, and starts Snakemake with the right Snakefile and working directory.

Snakemake is a workflow engine. In `trasgu`, it decides which chunk CSV files should exist, checks which ones are already present, and runs only the missing or outdated chunk jobs. This is why interrupted runs can usually be resumed by running `trasgu_run` again: Snakemake compares the requested final outputs with the files already on disk and schedules the work still needed.

Because `trasgu_run` delegates execution to Snakemake, `trasgu` can use any resource that Snakemake can use. Locally this means CPU cores through `--cores`; on clusters this means profiles and executors such as SLURM; and advanced users can pass extra Snakemake arguments after the `trasgu_run` options.

## The `.snakemake` directory

When `trasgu_run` starts Snakemake, Snakemake creates a `.snakemake` directory in the run directory. This directory stores workflow metadata such as locks, logs, temporary state, and cache files used to manage the run. It is normal for this directory to appear next to `trasgu.yaml`.

The `.snakemake` directory should usually be left in place. It helps Snakemake understand the state of the workflow and resume safely.

## Unlocking a run directory

Snakemake locks the working directory while a workflow is running so two workflow processes do not write the same outputs at the same time. If a job is killed, the terminal closes, or a cluster job exits abruptly, that lock can remain even though no workflow is still running.

When that happens, `trasgu_run` may report that the working directory is locked. First make sure no other `trasgu_run` or Snakemake process is still active for the same run directory. Then unlock it:

```bash
trasgu_run --unlock
```

After unlocking, start the workflow again:

```bash
trasgu_run
```

## Manual workflow

For debugging, fit one chunk directly:

```bash
trasgu_fit_chunk 0
trasgu_monitor
trasgu_combine
```

Manual chunk fitting is useful when one chunk failed and you want to reproduce it without submitting the whole workflow again.

## Rerunning partial work

Chunk output files are named with the chunk index and chunk size:

```text
fit_chunk_NNNN_MMMMM.csv
```

If a run is interrupted, rerun `trasgu_run`. Snakemake will use existing outputs when they are still valid.

Use:

```bash
trasgu_monitor
```

to list missing chunk IDs.
