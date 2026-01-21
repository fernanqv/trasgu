#!/bin/bash
#SBATCH --job-name="vines8"
#SBATCH --partition=geocean_priority
##SBATCH --time=03:59:00
##SBATCH --cpus-per-task=1
##SBATCH --mem-per-cpu=512MB
##SBATCH --exclude=geocean0[7-8]

# These values are set from the sbatch command line when needed
#SBATCH --array=0-999


# Exmple sbatch command to run this fit_info.yaml with SLURM:
# sbatch --array=4 --ntasks=16 launchers/launch_slurm.sh fit_info.yaml

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 fit_config.yaml" >&2
  exit 1
fi

config_path=$1
if [[ ! -f "$config_path" ]]; then
  echo "ERROR: Config file not found: $config_path" >&2
  exit 2
fi

config_path=$(realpath "$config_path")

chimera_fit_chunk --config $config_path $SLURM_ARRAY_TASK_ID



# srun --ntasks=${SLURM_NTASKS} bash -c "
#   id=\$(( SLURM_ARRAY_TASK_ID * SLURM_NTASKS + SLURM_PROCID ))
#   echo $id
#   python fit_vinecop_chunk.py \"\$id\" --config $config_path
# "


