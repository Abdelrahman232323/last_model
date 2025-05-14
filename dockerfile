# Use a minimal base image
FROM python:3.10-slim

# Avoid bytecode generation and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements for better caching
COPY requirements.txt .

# Install Python dependencies (CPU-optimized torch)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set environment variable for FastAPI
ENV MODULE_NAME=main
ENV VARIABLE_NAME=app

# Expose port for container
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
