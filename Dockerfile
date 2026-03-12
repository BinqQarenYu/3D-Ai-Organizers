FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for ifcopenshell and trimesh
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend /app/backend

# Set environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=17831

EXPOSE 17831

# Run the uvicorn server
CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "17831"]
