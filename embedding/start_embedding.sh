#!/bin/bash
# Loads the HPC runtime and starts the standalone embedding API.

module load Python/3.11.5-GCCcore-13.2.0
module load CUDA/12.8.0

source ../backend/venv311/bin/activate

uvicorn embedding.server:app --host 0.0.0.0 --port 8001
