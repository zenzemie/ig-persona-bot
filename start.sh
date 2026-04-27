#!/bin/bash

# Ensure we are in the right directory
cd /app

# Start a dummy HTTP server to satisfy health checks (e.g., on Hugging Face Spaces)
python -m http.server 7860 &

# Run the agent
python agent.py
