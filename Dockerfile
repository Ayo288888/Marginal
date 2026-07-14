# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environmental variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage cache
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy rest of the backend and frontend files
COPY backend /app/backend
COPY frontend /app/frontend

# Expose server port
EXPOSE 8000

# Set working directory to backend for uvicorn execution
WORKDIR /app/backend

# Start uvicorn serving the FastAPI app on the specified port
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
