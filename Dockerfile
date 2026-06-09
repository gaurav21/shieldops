FROM python:3.12-slim

WORKDIR /app

# Install deps in small batches to keep memory usage low
RUN pip install --no-cache-dir fastapi==0.115.12 python-dotenv==1.2.2
RUN pip install --no-cache-dir uvicorn[standard]==0.34.3
RUN pip install --no-cache-dir httpx==0.28.1
RUN pip install --no-cache-dir pydantic==2.11.4
RUN pip install --no-cache-dir datadog==0.50.1
RUN pip install --no-cache-dir PyGithub==2.5.0

# Copy application code
COPY trigger.py .
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY static/ ./static/
COPY .env.example .

# Create data directory for persistent state
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "trigger:app", "--host", "0.0.0.0", "--port", "8000"]
