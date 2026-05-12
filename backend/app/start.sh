#!/bin/bash

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 11005
