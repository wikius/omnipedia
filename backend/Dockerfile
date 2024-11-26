# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim-bookworm

# Install UV and build dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# Copy the rest of the application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]