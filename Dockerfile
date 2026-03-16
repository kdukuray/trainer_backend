FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies + gunicorn
RUN uv sync --frozen --no-dev && \
    uv pip install gunicorn

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.prod.sh

EXPOSE 8000

# Entrypoint runs migrations before starting server
ENTRYPOINT ["./entrypoint.prod.sh"]

# Production server with Gunicorn
# Uses WEB_CONCURRENCY env var if set (Render sets this), otherwise 4 workers
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "config.wsgi:application"]