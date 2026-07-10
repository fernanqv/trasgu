# Offline Zarr

Some HPC compute nodes cannot access external HTTP resources. In that case, download the Chimera Zarr store on a node with internet access and point `trasgu.yaml` to the local copy.

See [Local Chimera Zarr](examples.md#local-chimera-zarr) for a runnable example configuration.

## Download arrays

```bash
trasgu_download_zarr /scratch/user --vars 4,5,6,7
```

This creates or updates `/scratch/user/chimera.zarr`. By default, `--vars` is `4,5,6,7`.

Variable size 8 is very large, approximately hundreds of GB, and requires interactive confirmation.

## Configure a run

```yaml
data_file: input6_500_gumbel_high.txt
chunk_size: 1000
trasgu_url: /scratch/user/chimera.zarr
```

## Verify access

```bash
trasgu_get_matrix 6 0 --url /scratch/user/chimera.zarr
```

If this command fails on a compute node, check filesystem visibility and permissions for the local Zarr path.
