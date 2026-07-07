# Workflows

`trasgu` is organized around chunk-based processing.

1. Count how many chunks are needed.
2. Fit each chunk.
3. Monitor which chunk files exist.
4. Combine chunk CSV files into one final CSV.

## Recommended workflow

```bash
cd examples/run_config/minimal
trasgu_count_chunks
trasgu_run --dry-run
trasgu_run
trasgu_monitor
trasgu_combine
```

`trasgu_run` is the recommended entrypoint. It launches the packaged Snakemake workflow and creates the expected chunk files before combining results.

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
