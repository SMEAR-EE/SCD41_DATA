# Container Deployment

The pipeline runs in Docker or Podman without requiring a local Python install.

## 1. Configure Volumes

Edit `docker-compose.yaml` to mount your raw data directories. The container needs three volume types:

| Volume | Purpose | Mode |
|--------|---------|------|
| `./config:/app/config` | Sensor configuration | Read-only |
| `./output:/app/output` | Pipeline outputs (CSV, Parquet, logs, plots) | Read-write |
| `/host/path/to/data:/data/scd41` | Raw SCD41 sensor files | Read-only |
| `/host/path/to/data:/data/lgr` | Raw LGR sensor files | Read-only |

Example `docker-compose.yaml` volumes:
```yaml
volumes:
  - ./config:/app/config:ro
  - ./output:/app/output
  - /mnt/sensors/SCD41:/data/scd41:ro
  - /mnt/sensors/LGR:/data/lgr:ro
```

## 2. Update Config Paths

The `input_dir` paths in `config/sensors.yaml` must reference the **container-side** mount points, not host paths:

```yaml
sensors:
  - name: CO2_SCT1_2M
    input_dir: /data/scd41/CO2-SCT1-2M   # ← container path, not host path
    sensor_type: scd41
    # ...
  - name: LGR_30M
    input_dir: /data/lgr                   # ← container path
    sensor_type: lgr_csv
    # ...
```

## 3. Build and Run

**Docker:**
```bash
docker compose build
docker compose up        # foreground (see logs)
docker compose up -d     # detached
docker compose logs -f   # follow logs if detached
```

**Podman:**
```bash
podman-compose build
podman-compose up
```

The image uses a multi-stage Alpine build (~50 MB) for minimal disk usage.

## 4. Output

Results appear in `./output/` on the host (mounted volume). The pipeline creates subdirectories automatically:
- `output/sensors/` — per-sensor CSVs and Parquet
- `output/merged/` — merged datasets
- `output/validation/` — validation reports
- `output/logs/` — processing logs

## Interactive Container Session

To open a shell for debugging or running Jupyter inside the container:
```bash
docker compose run --rm --entrypoint /bin/sh smear-co2
# then inside the container:
python -m src.pipeline       # run pipeline
python -c "import src; ..."  # test imports
```

> **Note:** `setup.sh` is for local (non-container) installs only. The container installs dependencies directly via the Dockerfile.
