FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY main.py .

# Copy FFmpeg binaries
COPY bin/ ./bin/

# Create temp directory for temporary files
RUN mkdir -p /app/temp

# Set execute permissions for FFmpeg binaries
RUN chmod +x /app/bin/ffmpeg/ffmpeg /app/bin/ffmpeg/ffprobe

# Expose port for Flask application
EXPOSE 5000

# Run gunicorn with specified parameters
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "main:app"]
