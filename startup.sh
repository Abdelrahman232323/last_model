#!/bin/bash

# Set Python to use UTF-8
export PYTHONIOENCODING=utf-8

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Function to compress directory with error handling and retries
compress_directory() {
    local source_dir="$1"
    local output_file="$2"
    local max_retries=3
    local retry_count=0
    
    # Check if source directory exists
    if [ ! -d "$source_dir" ]; then
        echo "Error: Source directory $source_dir does not exist"
        return 1
    fi
    
    # Check available disk space (minimum 1GB required)
    local available_space=$(df -k "$(dirname "$output_file")" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then
        echo "Error: Insufficient disk space"
        return 1
    fi
    
    # Ensure output directory exists
    mkdir -p "$(dirname "$output_file")"
    
    while [ $retry_count -lt $max_retries ]; do
        echo "Attempt $((retry_count + 1)) of $max_retries to compress directory..."
        
        # Use tar with lower compression level and pipe through gzip
        # Added --no-same-owner to avoid permission issues
        # Added --no-same-permissions to avoid permission issues
        tar --no-same-owner --no-same-permissions -cf - "$source_dir" | gzip -1 > "$output_file"
        
        if [ $? -eq 0 ]; then
            echo "Compression completed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo "Compression failed, retrying in 5 seconds..."
                sleep 5
                # Clean up failed attempt
                rm -f "$output_file"
            fi
        fi
    done
    
    echo "Error: Compression failed after $max_retries attempts"
    return 1
}

# Function to handle deployment compression
handle_deployment_compression() {
    local source_dir="/tmp/_preCompressedDestinationDir"
    local output_file="/home/site/wwwroot/output.tar.gz"
    
    echo "Starting deployment compression..."
    
    # Ensure source directory exists and is readable
    if [ ! -d "$source_dir" ]; then
        echo "Error: Source directory does not exist"
        return 1
    fi
    
    # Check if we have write permissions to the output directory
    if [ ! -w "$(dirname "$output_file")" ]; then
        echo "Error: No write permission to output directory"
        return 1
    fi
    
    # Attempt compression
    compress_directory "$source_dir" "$output_file"
    
    if [ $? -eq 0 ]; then
        echo "Deployment compression completed successfully"
        return 0
    else
        echo "Deployment compression failed"
        return 1
    fi
}

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Handle deployment compression if needed
if [ -d "/tmp/_preCompressedDestinationDir" ]; then
    handle_deployment_compression
fi

# Start the application with Gunicorn and Uvicorn worker
exec gunicorn -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8000 --timeout 600 --workers 2 --threads 4 