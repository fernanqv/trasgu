# SLURM and HPC

`trasgu` can run on SLURM clusters through Snakemake profiles.

## Install SLURM support

The SLURM executor plugin is optional:

```bash
uv sync --frozen --extra slurm
```

## Packaged SLURM profile

From a run directory:

```bash
trasgu_run --profile slurm
```

This resolves the packaged profile at `trasgu_workflow/profiles/slurm`.

## Custom Snakemake profile

```bash
trasgu_run --profile /path/to/snakemake-profile
```

Extra Snakemake arguments can be appended:

```bash
trasgu_run --profile /path/to/snakemake-profile --printshellcmds
```

## Before submitting

Run a dry run:

```bash
trasgu_run --profile slurm --dry-run
```

Check that:

- `trasgu.yaml` points to accessible input data.
- the chunk work directory (`.trasgu_<run>` by default, or `output_dir` if configured) is on storage visible to compute nodes.
- `trasgu_url` is reachable from compute nodes, or points to a local Zarr copy.
- The requested variable size exists in the Chimera Zarr store.
