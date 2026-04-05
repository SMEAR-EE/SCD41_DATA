# Container Deployment

The pipeline runs in Docker or Podman without requiring a local Python install. See `Dockerfile` in the repository root for the image definition.

## 1. Configure Volumes

Edit `docker-compose.yaml` to mount your raw data directories. The container needs three volume types: sensor configuration, pipeline output, and raw sensor data (one mount per data source):

| Volume | Purpose | Mode |
|--------|---------|------|
| `./config:/app/config` | Sensor configuration | Read-only |
| `./output:/app/output` | Pipeline outputs (CSV, Parquet, logs, plots) | Read-write |
| `/host/path/to/data:/data/scd41` | Raw SCD41 sensor files (one per source) | Read-only |
| `/host/path/to/data:/data/lgr` | Raw LGR sensor files (one per source) | Read-only |

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

**Podman** (should work with `podman-compose`; not officially tested):
```bash
podman-compose build
podman-compose up
```

The pipeline is a batch job - re-running `docker compose up` is safe. The pipeline only writes output files; it does not reprocess data that has already been written unless you clear `output/` or pass `force=True`.

The image uses a multi-stage Alpine build for minimal disk usage.

## 4. Output

Results appear in `./output/` on the host (mounted volume). The pipeline creates subdirectories automatically:
- `output/sensors/` - per-sensor CSVs, Parquet, and plots
- `output/merged/` - merged datasets (CSV, Parquet) and multi-sensor plots
- `output/validation/` - validation reports
- `output/logs/` - processing logs

## Interactive Container Session

To open a shell for debugging or running Jupyter inside the container:
```bash
docker compose run --rm --entrypoint /bin/sh smear-co2
# then inside the container:
python -m src.pipeline       # run pipeline
python -c "import src; ..."  # test imports
```
