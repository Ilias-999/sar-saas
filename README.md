# SAR SaaS - System Activity Reporter Analyzer

A full-stack web application for analyzing SAR (System Activity Reporter) system performance data. Upload SAR text files and get detailed statistics and visualizations.

## Features

- 📊 Upload and parse SAR system performance data
- 📉 Calculate and display system statistics (CPU, memory, disk, network, etc.)
- 🎨 Modern web interface for visualization
- 🐳 Containerized with Docker and Docker Compose

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd sar_saas
   ```

2. **Create a `.env` file** in the project root:
   ```env
   FRONTEND_CONTAINER_NAME=sar-frontend
   FRONTEND_PORT=3000
   BACKEND_CONTAINER_NAME=sar-backend
   BACKEND_PORT=8000
   BACKEND_HOST=0.0.0.0
   ```

3. **Start the application:**
   ```bash
   docker-compose up
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Swagger API  docs: http://localhost:8000/docs

## Project Structure

```
.
├── frontend/              # React/HTML frontend with Nginx
├── backend/               # FastAPI backend service
│   ├── app/
│   │   ├── main.py       # FastAPI application
│   │   ├── parser.py     # SAR file parser
│   │   └── stats.py      # Statistics calculator
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Backend container config
├── sar-test-data/        # Sample SAR data files for testing
└── docker-compose.yml    # Docker Compose configuration
```

## Development

- Backend code changes auto-reload thanks to uvicorn hot reload
- Frontend served statically by Nginx

## Stopping the Application

```bash
docker-compose down
```

## Tech Stack

- **Backend:** FastAPI, uvicorn, Python
- **Frontend:** HTML, CSS, JavaScript, Nginx
- **Infrastructure:** Docker, Docker Compose
