# Troubleshooting

## `trasgu.yaml` is not found

Most commands must be run from a run directory containing `trasgu.yaml`.

```bash
cd examples/run_config/minimal
trasgu_run --dry-run
```

## `data_file` is not found

Paths in `trasgu.yaml` are resolved from the run directory. Check the path from there:

```bash
ls ../../inputs/input6_500_gumbel_high.txt
```

## Zarr access fails

If `trasgu_url` is not set, `trasgu` uses the remote Chimera Zarr store. On clusters, compute nodes may not have internet access.

Use a local Zarr copy:

```yaml
trasgu_url: /scratch/user/chimera.zarr
```

Then verify:

```bash
trasgu_get_matrix 6 0 --url /scratch/user/chimera.zarr
```

## Chunks are missing

Check progress:

```bash
trasgu_monitor
```

Rerun the workflow:

```bash
trasgu_run
```

For one chunk:

```bash
trasgu_fit_chunk 23
```

## Snakemake directory is locked

Unlock from the run directory:

```bash
trasgu_run --unlock
```

Then rerun:

```bash
trasgu_run
```

## Combined results are incomplete

`trasgu_combine` warns when chunks are missing. Run:

```bash
trasgu_monitor
```

before combining final results.
