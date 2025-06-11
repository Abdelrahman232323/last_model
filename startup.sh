#!/bin/bash

# Set UTF-8 encoding for Python I/O
export PYTHONIOENCODING=utf-8

# Environment variables for better performance and cleaner logging
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Upgrade pip and install required packages
pip install --upgrade pip
pip install -r requirements.txt

# Start the FastAPI app using Gunicorn with Uvicorn workers
exec gunicorn main:app \
    --workers 2 \
    --threads 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 600
