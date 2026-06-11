FROM python:3.12-slim

WORKDIR /app

# System deps for PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY trigger.py .
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY static/ ./static/
COPY alembic.ini* ./
COPY .env.example .

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "trigger:app", "--host", "0.0.0.0", "--port", "8000"]
