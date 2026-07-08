# Read Chimera matrices from a Zarr v3 store with the R package "zarr".
#
# Install once with:
#   install.packages("zarr")
#
# Documentation:
#   https://r-cf.github.io/zarr/

library(zarr)

# Public read-only HTTP store. For cluster-local reads, use the local path below.
chimera_store <- "http://meteo.unican.es/work/chimera.zarr"
# chimera_store <- "/lustre/gmeteo/WORK/WWW/chimera.zarr"

n_vars <- 5
first_matrix_id <- 0  # Chimera IDs are zero-based.
n_matrices <- 10

array_name <- paste0("matrices", n_vars)
array_store <- paste0(chimera_store, "/", array_name)

# Open the array directly. This avoids relying on directory listing at the
# HTTP root, which regular web servers often disable.
z <- open_zarr(array_store)
matrices <- z[["/"]]

cat("Opened", array_store, "\n")
print(matrices)

# R array indices are one-based, so Chimera ID 0 is row 1 in R.
first_r_index <- first_matrix_id + 1
last_r_index <- first_r_index + n_matrices - 1

block <- matrices[first_r_index:last_r_index, 1:n_vars, 1:n_vars]

cat("Read", n_matrices, "matrices starting at Chimera ID", first_matrix_id, "\n")
print(dim(block))

# Show one matrix as a normal 2-D R matrix.
one_matrix <- block[1, , ]
print(one_matrix)
