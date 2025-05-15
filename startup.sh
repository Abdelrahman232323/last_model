#!/bin/bash

# Activate virtual environment
source /home/site/wwwroot/antenv/bin/activate

# Install requirements
pip install -r /home/site/wwwroot/requirements.txt

# Start the application
cd /home/site/wwwroot
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 