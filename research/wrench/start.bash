#!/usr/bin/bash

echo "Launching wrench-daemon..."
wrench-daemon --num-commports 50000 &

echo "Launching workflow runner with Uvicorn hot reload..."
uvicorn wrench.simulator:main --reload --host 0.0.0.0 --port 8000