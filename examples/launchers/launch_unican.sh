#!/bin/bash
#SBATCH --job-name="vines8"
#SBATCH --partition=meteo_long
#SBATCH --exclude=wn055

# These values are set from the sbatch command line when needed
##SBATCH --array=0-999


# Exmple sbatch command to run this fit_info.yaml with SLURM:
# sbatch --array=4 --ntasks=16 launchers/launch_slurm.sh fit_info.yaml

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



# srun --ntasks=${SLURM_NTASKS} bash -c "
#   id=\$(( SLURM_ARRAY_TASK_ID * SLURM_NTASKS + SLURM_PROCID ))
#   echo $id
#   trasgu_fit_chunk \"\$id\"
# "
