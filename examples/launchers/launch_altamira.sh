#!/bin/bash
#SBATCH --job-name="wps"
#SBATCH --partition=wncompute_ifca

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

trasgu_fit_chunk --config $config_path $SLURM_ARRAY_TASK_ID