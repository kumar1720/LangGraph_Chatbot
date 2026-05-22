# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve using FastAPI and Python
FROM python:3.11-slim
WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY app/ ./app
COPY app.py .

# Copy compiled React static assets from Stage 1 builder
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Expose FastAPI server port
EXPOSE 8000

# Set environment fallback defaults
ENV PORT=8000

# Copy start script
COPY start.sh .
RUN chmod +x start.sh

# Start command
CMD ["./start.sh"]

