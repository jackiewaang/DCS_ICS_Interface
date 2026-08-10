#!/bin/bash

module load Python/3.11.5-GCCcore-13.2.0
source venv311/bin/activate

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 11005
