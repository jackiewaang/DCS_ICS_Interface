#!/bin/bash
#SBATCH --job-name=backend-switch-poc
#SBATCH --time=00:02:00
#SBATCH --gres=gpu:1

echo "GPU allocation acquired"
sleep 30