#!/usr/bin/env bash
set -e

script_dir=$(cd "$(dirname "$0")" && pwd)
chimera=/gpfs/users/fernandezv/chimera/chimera.zarr
run_dir=$(mktemp -d)
trap 'rm -rf "$run_dir"' EXIT

for n_columns in 4 5 6 7 8; do
    columns=$(seq -s, 1 "$n_columns")
    printf 'data_file: %s\ncolumns: [%s]\ntrasgu_url: %s\n' \
        "$script_dir/ship_wave.txt" "$columns" "$chimera" > "$run_dir/trasgu.yaml"

    echo "=== First $n_columns columns ==="
    (cd "$run_dir" && trasgu_time_fit)
    echo
done
