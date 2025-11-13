FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY main.py .

# Create temp directory for temporary files
RUN mkdir -p /app/temp

# Create bin directory structure for compatibility
RUN mkdir -p /app/bin/ffmpeg

# Expose port for Flask application
EXPOSE 5000

# Run gunicorn with specified parameters
# Use PORT environment variable if available (for Render.com), otherwise default to 5000
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 300 main:app
