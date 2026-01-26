# Quick Start Guide: Creating v0.1.0 Release

This guide provides step-by-step instructions to create the v0.1.0 release after this PR is merged.

## Prerequisites
- All changes from this PR have been merged to main branch
- You have write access to the repository
- Git is configured with your credentials

## Release Steps

### Step 1: Update Local Repository
```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Verify you have the release files
ls -la CHANGELOG.md VERSION RELEASE_CHECKLIST.md
```

### Step 2: Create Release Tag
```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release v0.1.0 - Initial Release Candidate

This release establishes the first official version of the SMEAR Estonia
CO2 Sensor Processing Pipeline with all core features functional and validated.

Key features:
- Multi-sensor data processing (4× SCD41 + 1× LGR)
- Time-synchronized resampling to 10-minute intervals
- Quality control with uptime tracking
- Multiple output formats (CSV and Parquet)
- Comprehensive visualization module
- Docker deployment support

See CHANGELOG.md for complete release notes."

# Verify tag was created
git tag -l -n9 v0.1.0

# Push tag to GitHub
git push origin v0.1.0
```

### Step 3: Create GitHub Release

1. **Navigate to Releases**
   - Go to: https://github.com/SMEAR-EE/SCD41_DATA/releases/new

2. **Configure Release**
   - **Choose a tag:** Select `v0.1.0` from dropdown
   - **Release title:** `v0.1.0 - Initial Release Candidate`
   - **Description:** Copy from CHANGELOG.md (see below)

3. **Release Description Template**
   ```markdown
   ## SMEAR Estonia CO2 Sensor Processing Pipeline - v0.1.0
   
   This is the first release candidate for the SMEAR Estonia CO2 Sensor Processing Pipeline.
   
   ### 🚀 Features
   
   - **Multi-sensor data processing** for 4× SCD41 + 1× LGR CO2 sensors
   - **Time synchronization** with 10-minute interval resampling (epoch-aligned)
   - **Quality control system** with uptime tracking and data validation
   - **Multiple output formats** (CSV and Parquet with Snappy compression)
   - **Comprehensive visualization** module with uptime, validation, and QC plots
   - **Data merging** capability with outer join strategy
   - **Docker support** with Dockerfile and docker-compose.yaml
   - **Configuration management** via YAML files
   - **Incremental processing** with atomic writes
   - **Detailed logging** with structured output
   
   ### 📦 Installation
   
   ```bash
   git clone https://github.com/SMEAR-EE/SCD41_DATA
   cd SCD41_DATA
   git checkout v0.1.0
   ./setup.sh
   source activate.sh
   ```
   
   ### 📖 Documentation
   
   - [Quick Start Guide](README.md)
   - [Technical Overview](APPLICATION_SUMMARY.md)
   - [Setup Instructions](SETUP.md)
   - [Data Merging](MERGING.md)
   - [Full Changelog](CHANGELOG.md)
   
   ### ⚠️ Known Limitations
   
   - Taylor diagram module is work-in-progress
   - Single-site focus (optimized for SMEAR Estonia)
   - Batch-oriented (no real-time processing)
   
   ### 🔮 Future Work
   
   - **v0.2.0**: Directory structure refactoring
   - **v0.3.0**: Complete Taylor diagram implementation
   - **v1.0.0**: Production release with comprehensive testing
   
   ### 📝 Citation
   
   ```
   Zorec, M. et al. (2025). SMEAR Estonia CO2 Sensor Processing Pipeline.
   Version 0.1.0. GitHub: SMEAR-EE/SCD41_DATA
   ```
   
   ### 🐛 Report Issues
   
   Found a bug? Please [open an issue](https://github.com/SMEAR-EE/SCD41_DATA/issues/new/choose).
   
   ---
   
   **Full Release Notes:** [CHANGELOG.md](CHANGELOG.md)
   ```

4. **Release Options**
   - ☑️ Check "Set as a pre-release" (optional, since this is v0.1.0)
   - ☑️ Check "Create a discussion for this release" (optional)

5. **Publish**
   - Click "Publish release"

### Step 4: Verify Release

```bash
# Check that tag exists on GitHub
git ls-remote --tags origin

# Verify you can see:
# refs/tags/v0.1.0

# Clone fresh copy to test
cd /tmp
git clone https://github.com/SMEAR-EE/SCD41_DATA
cd SCD41_DATA
git checkout v0.1.0

# Verify VERSION file
cat VERSION
# Should show: 0.1.0

# Test setup
./setup.sh
source activate.sh
python -c "import src.pipeline; print('✅ Release verified')"
```

### Step 5: Post-Release Activities

1. **Update Documentation** (if needed)
   - Add release badge to README on main branch
   - Update any external documentation links

2. **Announce Release**
   - Email team/collaborators
   - Post to relevant forums/channels
   - Update project website (if applicable)

3. **Archive Development Branch** (optional)
   ```bash
   # If this PR was from a development branch
   git branch -d copilot/prepare-initial-release-candidate
   git push origin --delete copilot/prepare-initial-release-candidate
   ```

4. **Plan Next Release**
   - Create milestone for v0.2.0 on GitHub
   - Start planning issues for next version

## Docker Release (Optional)

If you want to publish Docker images:

```bash
# Build images
docker build -t smear-ee/scd41-data:0.1.0 .
docker build -t smear-ee/scd41-data:latest .

# Test images
docker run --rm smear-ee/scd41-data:0.1.0 python -c "import src; print('✅ Docker OK')"

# Login to Docker Hub (if publishing)
docker login

# Push images
docker push smear-ee/scd41-data:0.1.0
docker push smear-ee/scd41-data:latest

# Update docker-compose.yaml to use released version
# image: smear-ee/scd41-data:0.1.0
```

## Troubleshooting

### Tag already exists
```bash
# Delete local tag
git tag -d v0.1.0

# Delete remote tag
git push origin :refs/tags/v0.1.0

# Recreate tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

### Wrong commit tagged
```bash
# Create tag at specific commit
git tag -a v0.1.0 <commit-hash> -m "Release v0.1.0"
```

### Release on wrong branch
Make sure you're on main branch before creating tags:
```bash
git checkout main
git pull origin main
git tag -a v0.1.0 -m "Release v0.1.0"
```

## Checklist

- [ ] All PR changes merged to main
- [ ] Local repository updated
- [ ] Release tag created (v0.1.0)
- [ ] Tag pushed to GitHub
- [ ] GitHub Release created
- [ ] Release verified with fresh clone
- [ ] Team notified
- [ ] Docker images built and tested (optional)
- [ ] Next version planning started

## Support

If you encounter any issues during the release process:
- Review [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- Open an issue on GitHub

---

**Last Updated:** 2026-01-26  
**Status:** Ready for execution after PR merge
