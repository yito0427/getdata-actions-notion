.PHONY: help install test lint format run clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies with Poetry"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run linters (flake8, mypy)"
	@echo "  make format     - Format code (black, isort)"
	@echo "  make run        - Run the data collector"
	@echo "  make clean      - Clean cache and temporary files"

install:
	poetry install

test:
	poetry run pytest tests/ -v --cov=src --cov-report=html

lint:
	poetry run flake8 src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run isort src tests

run:
	poetry run python -m src.main

# Run collector for specific exchanges
run-test:
	poetry run python -m src.main --exchanges binance,coinbase --test

# Check environment setup
check-env:
	@echo "Checking environment setup..."
	@test -f .env || (echo "ERROR: .env file not found. Copy .env.example to .env and configure it." && exit 1)
	@echo "Environment check passed!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache