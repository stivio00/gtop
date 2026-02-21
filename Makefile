# Makefile for gtop project

PYTHON ?= python
PACKAGE_NAME = gtop

.PHONY: help install-dev build upload clean test lint format

help:
	@echo "Available targets:"
	@echo "  install-dev   Install development dependencies (build, test, lint)"
	@echo "  build         Build source and wheel distributions"
	@echo "  upload        Upload built distributions to PyPI (requires TWINE_USERNAME/TWINE_PASSWORD)"
	@echo "  clean         Remove build artifacts"
	@echo "  test          Run any test suite (placeholder)"
	@echo "  lint          Run linters (e.g. flake8)"
	@echo "  format        Run code formatter (e.g. black)"

install-dev:
	@echo "Installing development dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install build twine hatchling pytest flake8 black

build:
	@echo "Building package..."
	$(PYTHON) -m build

upload: build
	@echo "Uploading package to PyPI..."
	# You must have TWINE_USERNAME and TWINE_PASSWORD env vars set
	$(PYTHON) -m twine upload dist/*

clean:
	rm -rf build dist *.egg-info

test:
	@echo "No tests defined yet."

lint:
	@echo "Running flake8..."
	flake8 .

format:
	@echo "Running black..."
	black .
