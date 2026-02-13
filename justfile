# yazio-exporter task runner

# Install all dependencies
setup:
    uv sync --all-extras

# Run all tests
test *args:
    uv run pytest tests/ {{ args }}

# Run tests with verbose output
test-v:
    uv run pytest tests/ -v

# Run a specific test file
test-file file:
    uv run pytest tests/{{ file }} -v

# Run the CLI
run *args:
    uv run yazio-exporter {{ args }}

# Full export (login + all data)
export-all email password:
    uv run yazio-exporter export-all {{ email }} {{ password }}

# Login and save token
login email password:
    uv run yazio-exporter login {{ email }} {{ password }}

# Export days data
days:
    uv run yazio-exporter days

# Export weight data
weight:
    uv run yazio-exporter weight

# Export all nutrients
nutrients:
    uv run yazio-exporter nutrients

# Export products from days data
products:
    uv run yazio-exporter products

# Show analytics summary
summary:
    uv run yazio-exporter summary

# Lint with ruff
lint:
    uv run ruff check src/ tests/

# Format with ruff
fmt:
    uv run ruff format src/ tests/

# Clean build artifacts
clean:
    rm -rf dist/ build/ src/*.egg-info .pytest_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Build package
build:
    uv build

# Publish to PyPI
publish:
    uv build && uv publish

# Show available commands
help:
    @just --list
