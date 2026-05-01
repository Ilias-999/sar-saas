# Build arguments
ARG PYTHON_VERSION=3.12
ARG WORKDIR=/app

FROM python:${PYTHON_VERSION}-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_RELOAD=false

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

WORKDIR /app

# Expose port
EXPOSE ${APP_PORT}

# Start uvicorn server
CMD ["sh", "-c", "uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT}"]
