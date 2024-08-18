.PHONY: format
format: ## Format repository code
	poetry run black .
	poetry run isort .

.PHONY: format-check
format-check: ## Check the code format with no actual side effects
	poetry run black --check .
	poetry run isort --check .

.PHONY: lint
lint: ## Launch the linting tools
	poetry run flake8 .
	poetry run pylint **/**.py

.PHONY: install
install: ## Install Python dependencies
	poetry install --no-root

.PHONY: type-check
type-check: ## Launch the type checking tool
	poetry run mypy .

.PHONY: check
check: format-check lint type-check ## Launch all the checks (formatting, linting, type checking)

.PHONY: help
help: ## Show the available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'