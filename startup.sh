#!/bin/bash

# Set Python to use UTF-8
export PYTHONIOENCODING=utf-8

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Azure App Service specific settings
export WEBSITE_RUN_FROM_PACKAGE=1
export SCM_DO_BUILD_DURING_DEPLOYMENT=true
export PYTHON_VERSION=3.11

# Memory optimization for Basic B3 (7GB RAM)
export GUNICORN_CMD_ARGS="--max-requests=1000 --max-requests-jitter=50 --timeout=300 --keep-alive=5"
export PYTHONMALLOC=malloc
export PYTHONHASHSEED=0

# Create necessary directories
mkdir -p /home/site/wwwroot/data
mkdir -p /home/site/wwwroot/model

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to compress directory with error handling and retries
compress_directory() {
    local source_dir="$1"
    local output_file="$2"
    local max_retries=3
    local retry_count=0
    
    log_message "Starting compression of $source_dir to $output_file"
    
    # Check if source directory exists
    if [ ! -d "$source_dir" ]; then
        log_message "Error: Source directory $source_dir does not exist"
        return 1
    fi
    
    # Check available disk space (minimum 1GB required)
    local available_space=$(df -k "$(dirname "$output_file")" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then
        log_message "Error: Insufficient disk space"
        return 1
    fi
    
    # Ensure output directory exists
    mkdir -p "$(dirname "$output_file")"
    
    while [ $retry_count -lt $max_retries ]; do
        log_message "Attempt $((retry_count + 1)) of $max_retries to compress directory..."
        
        # Use tar with lower compression level and pipe through gzip
        tar --no-same-owner --no-same-permissions -cf - "$source_dir" | gzip -1 > "$output_file"
        
        if [ $? -eq 0 ]; then
            log_message "Compression completed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                log_message "Compression failed, retrying in 5 seconds..."
                sleep 5
                # Clean up failed attempt
                rm -f "$output_file"
            fi
        fi
    done
    
    log_message "Error: Compression failed after $max_retries attempts"
    return 1
}

# Function to handle deployment compression
handle_deployment_compression() {
    local source_dir="/tmp/_preCompressedDestinationDir"
    local output_file="/home/site/wwwroot/output.tar.gz"
    
    log_message "Starting deployment compression..."
    
    # Ensure source directory exists and is readable
    if [ ! -d "$source_dir" ]; then
        log_message "Error: Source directory does not exist"
        return 1
    fi
    
    # Check if we have write permissions to the output directory
    if [ ! -w "$(dirname "$output_file")" ]; then
        log_message "Error: No write permission to output directory"
        return 1
    fi
    
    # Attempt compression
    compress_directory "$source_dir" "$output_file"
    
    if [ $? -eq 0 ]; then
        log_message "Deployment compression completed successfully"
        return 0
    else
        log_message "Deployment compression failed"
        return 1
    fi
}

# Clean up any existing deployment artifacts
log_message "Cleaning up existing deployment artifacts..."
rm -rf /home/site/wwwroot/output.tar.gz
rm -rf /tmp/_preCompressedDestinationDir

# Install dependencies
log_message "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify Python version
log_message "Verifying Python version..."
python --version

# Verify critical packages
log_message "Verifying critical packages..."
python -c "import fastapi; import uvicorn; import torch; print(f'FastAPI version: {fastapi.__version__}')"

# Handle deployment compression if needed
if [ -d "/tmp/_preCompressedDestinationDir" ]; then
    handle_deployment_compression
fi

# Calculate optimal worker count based on CPU cores (4 cores for B3)
# Using (2 * CPU cores) + 1 formula, but capped at 4 for B3
WORKERS=4
THREADS=4

# Start the application with optimized Gunicorn settings for B3
log_message "Starting application with Gunicorn..."
exec gunicorn \
    -k uvicorn.workers.UvicornWorker \
    main:app \
    --bind=0.0.0.0:8000 \
    --timeout=300 \
    --workers=$WORKERS \
    --threads=$THREADS \
    --worker-class=uvicorn.workers.UvicornWorker \
    --worker-connections=1000 \
    --max-requests=1000 \
    --max-requests-jitter=50 \
    --keep-alive=5 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output \
    --enable-stdio-inheritance 