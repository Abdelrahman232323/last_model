#!/bin/bash

# Set Python to use UTF-8
export PYTHONIOENCODING=utf-8

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start the application with Gunicorn and Uvicorn worker
exec gunicorn -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8000 --timeout 600 --workers 2 --threads 4 