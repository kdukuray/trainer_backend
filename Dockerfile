FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required by opencv-python-headless on slim images
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (gunicorn is included in pyproject.toml).
# pyproject.toml pins torch/torchvision to the CPU-only PyTorch index,
# so uv will never pull the multi-gigabyte CUDA build.
RUN uv sync --frozen --no-dev

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.prod.sh

EXPOSE 8000

# Entrypoint runs migrations before starting server
ENTRYPOINT ["./entrypoint.prod.sh"]

# Production server with Gunicorn
# Uses WEB_CONCURRENCY env var if set (Render sets this), otherwise 2 workers
# (keeping workers low avoids OOM on Render's starter instances)
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "config.wsgi:application"]