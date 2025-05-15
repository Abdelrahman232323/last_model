#!/bin/bash

# Set Python to use UTF-8
export PYTHONIOENCODING=utf-8

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Create and activate virtual environment if it doesn't exist
if [ ! -d "antenv" ]; then
    python -m venv antenv
fi

# Activate virtual environment
source antenv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Start the application with Gunicorn
gunicorn -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8000 --timeout 600 --workers 2 --threads 4 