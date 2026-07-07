# Outputs

`trasgu` writes one CSV per fitted chunk and can combine those files into one final CSV.

## Chunk files

Chunk files are written under `output_dir`:

```text
fit_chunk_NNNN_MMMMM.csv
```

Where:

- `NNNN` is the zero-based chunk index.
- `MMMMM` is the configured `chunk_size`.

Example:

```text
fit_chunk_0023_01000.csv
```

## Columns

Chunk files contain three comma-separated values per row:

| Column | Description |
| --- | --- |
| `vine_id` | Zero-based Chimera matrix ID. |
| `n_parameters` | Number of fitted copula parameters. |
| `aic` | Akaike information criterion for the fitted model. |

## Combined file

Use:

```bash
trasgu_combine
```

The default combined output is:

```text
fit_results/final_results.csv
```

The combined file includes a header:

```text
vine_id,n_parameters,aic
```
