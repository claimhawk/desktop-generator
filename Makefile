# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

.PHONY: all check lint typecheck format clean install dev test build generate

# Use venv Python if available, fallback to python3
PYTHON := $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)
SRC_FILES := $(shell find . -name "*.py" -not -path "./.venv/*")

# Default target
all: check

# Setup virtualenv and install dependencies
install:
	python3 -m venv .venv
	.venv/bin/pip install -e .

# Install dev dependencies
dev: install
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/pip install radon

# Run all quality checks
check: lint typecheck
	@echo "✓ All checks passed!"

# Linting with ruff
lint:
	@echo "Running ruff..."
	$(PYTHON) -m ruff check $(SRC_FILES)
	$(PYTHON) -m ruff format --check $(SRC_FILES)

# Type checking with mypy
typecheck:
	@echo "Running mypy..."
	$(PYTHON) -m mypy $(SRC_FILES) --strict

# Auto-format code
format:
	@echo "Formatting code..."
	$(PYTHON) -m ruff format $(SRC_FILES)
	$(PYTHON) -m ruff check --fix $(SRC_FILES)

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Generate dataset
generate:
	./scripts/generate.sh --dry

# Build and upload
build:
	./scripts/build.sh
