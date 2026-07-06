#!/bin/bash
#SBATCH --job-name="wps"
#SBATCH --partition=wncompute_ifca

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 run_directory" >&2
  exit 1
fi

run_dir=$1
if [[ ! -f "$run_dir/trasgu.yaml" ]]; then
  echo "ERROR: trasgu.yaml not found in run directory: $run_dir" >&2
  exit 2
fi

run_dir=$(realpath "$run_dir")
project_dir=$(dirname "$(dirname "$(dirname "$(realpath "$0")")")")
cd "$run_dir" || exit 3

uv run --project "$project_dir" --frozen trasgu_fit_chunk "$SLURM_ARRAY_TASK_ID"
