# ---------------------------------------------------------
# Minimal headless container for SMEAR Estonia CO2 pipeline
# No Jupyter, no notebooks — only CLI processing.
# ---------------------------------------------------------

FROM python:3.12-slim

# Avoid interactive tzdata config
ENV DEBIAN_FRONTEND=noninteractive

# Fix Python buffering for logs
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if needed)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential && \
#     rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy Python dependency list first (cache layer)
COPY requirements.txt /app/

# Install deps
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy source code
COPY src /app/src

# Create default output dirs (bind-mounted anyway)
RUN mkdir -p /app/output/individual \
    /app/output/parquet \
    /app/output/logs \
    /app/output/plots

# Config folder will be bind-mounted; create fallback
RUN mkdir -p /app/config

# Provide a simple default entrypoint
# This makes the container behave like:
#   podman run ... smear-co2 --date YYYY-MM-DD
ENTRYPOINT ["python", "-m", "src.pipeline"]
