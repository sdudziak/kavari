.PHONY: install verify format test clean dockerize run db_migrate

install:
	poetry install --no-root --only main

install-dev:
	poetry install

publish:
	@if [ -d "dist" ]; then rm -rf dist; fi
	poetry build
	twine upload --config-file=.pypirc dist/*

# Sprawdzenie jakości kodu i bezpieczeństwa
verify:
	poetry run flake8 --config ./config/flake8.cfg ./src
	poetry run black --check ./src
	poetry run mypy --explicit-package-bases src
	poetry run bandit -r ./src
	poetry run safety scan
	poetry run semgrep --config=auto ./src
	poetry run vulture ./src --min-confidence 80
	poetry run detect-secrets scan

# Automatyczne formatowanie kodu
format:
	poetry run isort ./src
	poetry run isort ./tests
	poetry run black ./src
	poetry run black ./tests

# Uruchomienie testów
test:
	poetry run pytest tests

# Czyszczenie cache Pythona i zależności
clean:
	@if [ -d "__pycache__" ]; then rm -rf __pycache__; fi
	@if [ -d "dist" ]; then rm -rf dist; fi
	@if [ -d ".mypy_cache" ]; then rm -rf .mypy_cache; fi
	@if [ -d ".pytest_cache" ]; then rm -rf .pytest_cache; fi
	@if [ -d ".tox" ]; then rm -rf .tox; fi
	@if [ -f ".c" ]; then rm -rf .c; fi
	@if [ -f ".coverage" ]; then rm -f .coverage; fi
	@if [ -f "coverage.xml" ]; then rm -f coverage.xml; fi

dockerize:
	docker build -t trading-bot .