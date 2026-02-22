# ---- Stage 1: Build ----
FROM python:3.12-alpine AS builder

RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: Runtime ----
FROM python:3.12-alpine

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source only
COPY src/ /app/src/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Output dirs created at runtime by config.py
# Config, output, and data dirs are mounted as volumes

ENTRYPOINT ["python", "-m", "src.pipeline"]
