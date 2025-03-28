# Use a Python 3.10+ base image
FROM python:3.10-slim  

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip before installing dependencies
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for Flask
ENV FLASK_APP=api.py

# Expose the correct port
ENV PORT=10000

# Start the application
CMD gunicorn -b 0.0.0.0:$PORT api:app
