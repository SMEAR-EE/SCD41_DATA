# Contributing to SCD41_DATA

Thank you for your interest in contributing to the SMEAR Estonia CO2 Sensor Processing Pipeline!

## How to Contribute

### Reporting Issues

If you encounter a bug or have a feature request:

1. Check if the issue already exists in [GitHub Issues](https://github.com/SMEAR-EE/SCD41_DATA/issues)
2. If not, create a new issue with:
   - Clear description of the problem or feature
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (Python version, OS, etc.)
   - Relevant logs or error messages

### Development Workflow

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR-USERNAME/SCD41_DATA
   cd SCD41_DATA
   ```

2. **Set up development environment**
   ```bash
   ./setup.sh
   source activate.sh
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

4. **Make your changes**
   - Follow existing code style
   - Add docstrings to new functions/classes
   - Update documentation if needed
   - Test your changes

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```

6. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Code Style

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and modular

### Docstring Format

```python
def process_data(data, threshold=10):
    """
    Process sensor data with quality control.
    
    Args:
        data (pd.DataFrame): Input sensor data
        threshold (float): Quality threshold value
        
    Returns:
        pd.DataFrame: Processed and filtered data
        
    Raises:
        ValueError: If data is empty or invalid
    """
    pass
```

## Project Structure

Understanding the codebase:

```
src/
├── pipeline.py          # Main orchestration
├── processor.py         # Daily data processing
├── config.py            # Configuration management
├── uptime.py            # Uptime metrics
├── merger.py            # Multi-sensor merging
├── parsers/
│   ├── base_parser.py   # Parser interface
│   ├── scd41_parser.py  # SCD41 JSON parser
│   └── lgr_parser.py    # LGR CSV parser
└── visualization/       # Plotting modules
```

## Testing

Currently, the project uses manual testing. Before submitting a PR:

1. **Test your changes**
   ```bash
   # Test with sample data
   source activate.sh
   jupyter notebook process_data.ipynb
   # Run through test cases manually
   ```

2. **Verify imports**
   ```bash
   python -c "import src.pipeline; print('OK')"
   ```

3. **Check for syntax errors**
   ```bash
   python -m py_compile src/*.py src/**/*.py
   ```

## Adding New Features

### Adding a New Sensor Parser

1. Create a new parser in `src/parsers/`:
   ```python
   from src.parsers.base_parser import BaseSensorParser
   
   class NewSensorParser(BaseSensorParser):
       def parse_file(self, file_path):
           # Implementation
           pass
   ```

2. Register in `src/config.py`
3. Update documentation

### Adding New Visualizations

1. Add methods to existing plotters in `src/visualization/`
2. Or create a new plotter module following the pattern in `base_plotter.py`
3. Update `src/visualization/README.md`

## Documentation

When adding features:

1. Update relevant `*.md` files in the root
2. Add docstrings to new code
3. Update `CHANGELOG.md` (for maintainers)
4. Update examples in `process_data.ipynb` if needed

## Pull Request Guidelines

Before submitting a PR:

- [ ] Code follows project style
- [ ] Docstrings added for new functions/classes
- [ ] Documentation updated
- [ ] Changes tested manually
- [ ] No breaking changes (or clearly documented if necessary)
- [ ] PR description explains what and why

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How were these changes tested?

## Related Issues
Closes #123
```

## Release Process

For maintainers:

1. Update `VERSION` file
2. Update `CHANGELOG.md` with new version
3. Follow steps in `RELEASE_CHECKLIST.md`
4. Create GitHub release with tag

## Future Development

See planned features in `CHANGELOG.md` under "Future Work":

- v0.2.0: Refactoring & Organization
- v0.3.0: Visualization & Analysis
- v1.0.0: Production Release

## Questions?

- Open a [Discussion](https://github.com/SMEAR-EE/SCD41_DATA/discussions)
- Or create an [Issue](https://github.com/SMEAR-EE/SCD41_DATA/issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SMEAR Estonia CO2 research! 🌍
