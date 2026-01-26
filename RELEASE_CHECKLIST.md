# Release Checklist for v0.1.0

This checklist outlines the steps to prepare for the initial release candidate.

## Pre-Release Checklist

### Documentation ✅
- [x] README.md is up-to-date with current features
- [x] APPLICATION_SUMMARY.md provides comprehensive technical overview
- [x] SETUP.md has clear installation instructions
- [x] MERGING.md documents data merging behavior
- [x] Visualization module has README
- [x] CHANGELOG.md created with v0.1.0 details
- [x] VERSION file created
- [x] RELEASE_CHECKLIST.md created (this file)

### Code Quality
- [ ] Core modules documented (docstrings optional given complexity)
- [ ] No obvious bugs or critical issues in main processing pipeline
- [ ] Error handling is robust and graceful
- [ ] Logging is comprehensive and informative

### Testing
- [ ] Manual testing of core workflows completed:
  - [ ] Setup script (`./setup.sh`) works correctly
  - [ ] Configuration file (`config/sensors.yaml`) is properly documented
  - [ ] Pipeline can process sample data successfully
  - [ ] CSV and Parquet outputs are generated correctly
  - [ ] Visualization plots are generated without errors
  - [ ] Merging functionality works as expected
  - [ ] Docker deployment works (if Docker is available)

### Security
- [ ] No hardcoded credentials or sensitive information in code
- [ ] Dependencies are from trusted sources
- [ ] No known security vulnerabilities in dependencies
- [ ] `.gitignore` properly excludes sensitive files

### Repository Hygiene
- [ ] No large binary files in repository (unless necessary)
- [ ] `.gitignore` is comprehensive
- [ ] Example configuration file (`config/sensors.example.yaml`) exists
- [ ] License file (MIT) is present and correct
- [ ] No temporary or cache files committed

### Dependencies
- [ ] `requirements.txt` is complete and version-pinned
- [ ] `requirements_dev.txt` includes development dependencies
- [ ] All dependencies are compatible with Python 3.10+
- [ ] Docker image uses appropriate base image (python:3.12-slim)

### Known Issues Documentation
- [x] Taylor diagram module flagged as WIP in documentation
- [x] Single-site limitation documented
- [x] File format specificity documented
- [x] No real-time processing limitation documented

## Release Process

### 1. Final Verification
```bash
# Ensure virtual environment is clean
rm -rf venv/
./setup.sh

# Activate environment
source activate.sh

# Verify imports work
python -c "from src.pipeline import SensorPipeline; print('✓ Imports OK')"

# Check for any obvious syntax errors
python -m py_compile src/*.py src/**/*.py
```

### 2. Create Release Tag
```bash
# Ensure all changes are committed
git status

# Create annotated tag
git tag -a v0.1.0 -m "Release v0.1.0 - Initial Release Candidate"

# Verify tag
git tag -l -n9 v0.1.0
```

### 3. Push Release
```bash
# Push commits and tag
git push origin main
git push origin v0.1.0
```

### 4. GitHub Release
1. Go to: https://github.com/SMEAR-EE/SCD41_DATA/releases/new
2. Select tag: `v0.1.0`
3. Release title: `v0.1.0 - Initial Release Candidate`
4. Copy release notes from `CHANGELOG.md`
5. Mark as "pre-release" if this is a release candidate
6. Publish release

### 5. Docker Image (Optional)
```bash
# Build and test Docker image
docker build -t smear-ee/scd41-data:0.1.0 .
docker build -t smear-ee/scd41-data:latest .

# Test Docker image
docker run --rm smear-ee/scd41-data:0.1.0 python -c "import src; print('✓ Docker OK')"

# Push to registry (if applicable)
# docker push smear-ee/scd41-data:0.1.0
# docker push smear-ee/scd41-data:latest
```

### 6. Post-Release
- [ ] Update README.md badge with release version (if using badges)
- [ ] Announce release to team/collaborators
- [ ] Archive any pre-release branches
- [ ] Begin planning v0.2.0 features

## Version Numbering

Following [Semantic Versioning](https://semver.org/):
- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): Add functionality (backwards-compatible)
- **PATCH** version (0.0.X): Backwards-compatible bug fixes

For v0.1.0 (initial release):
- Major = 0: Still in initial development
- Minor = 1: First feature-complete version
- Patch = 0: Initial release

## Future Release Planning

### v0.2.0 - Refactoring & Organization (Planned)
**Focus:** Improve directory structure and output organization
- Refactor merged directory structure
- Per-sensor individual outputs with improved naming
- Consolidate output directory hierarchy
- Enhanced CLI interface

**Breaking Changes:** Possible changes to output directory structure

### v0.3.0 - Visualization & Analysis (Planned)
**Focus:** Complete visualization features and add analysis tools
- Complete Taylor diagram implementation
- Additional validation metrics
- Interactive plotting support
- Automated report generation

**Breaking Changes:** None expected

### v1.0.0 - Production Release (Future)
**Requirements for 1.0.0:**
- All core features complete and tested
- Taylor diagram fully functional
- Comprehensive test suite
- Stable API
- Published peer-reviewed paper
- DOI assigned to dataset

## Notes

- This is a **release candidate** (v0.1.0), not a production release
- Most features are functional and have been validated
- Future work focuses on refactoring and enhancements, not core functionality
- The pipeline is already being used for real research data at SMEAR Estonia

## Contact

For questions or issues with this release:
- Open an issue: https://github.com/SMEAR-EE/SCD41_DATA/issues
- Repository: https://github.com/SMEAR-EE/SCD41_DATA

---

**Last Updated:** 2026-01-26
**Status:** Release Candidate - Ready for v0.1.0 tagging
