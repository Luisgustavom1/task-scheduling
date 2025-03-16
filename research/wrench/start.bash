#!/usr/bin/bash

echo "Launching wrench-daemon..."
wrench-daemon --num-commports 50000 --daemon-logging false &

echo "Launching workflow runner with Uvicorn hot reload..."
python3 ./simulator.py