FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY src /app/src

RUN mkdir -p /app/output/individual \
    /app/output/parquet \
    /app/output/logs \
    /app/output/plots \
    /app/config

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "pipeline"]
