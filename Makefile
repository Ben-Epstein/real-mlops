export PYTHONPATH = .venv

.PHONY: uv
uv:
	pip install --upgrade 'uv>=0.4.6,<0.5'
	uv venv

.PHONY: setup
setup:
	@if [ ! -d ".venv" ] || ! command -v uv > /dev/null; then \
		echo "UV not installed or .venv does not exist, running uv"; \
		make uv; \
	fi
	@if [ ! -f "uv.lock" ]; then \
		echo "Can't find lockfile. Locking"; \
		uv lock; \
	fi
	uv sync --all-extras
	uv pip install --no-deps -e .

.PHONY: format
format: setup
	uv --quiet run ruff format .
	uv --quiet run ruff check --fix .

.PHONY: lint
lint: setup
	uv --quiet run ruff check .
	uv --quiet run ruff format --check
	uv --quiet run mypy .

.PHONY: test
test: setup
	uv --quiet run pytest tests --cov=api --cov=tests --cov-fail-under=85 --cov-branch tests


.PHONE: sqlmesh-ui
sqlmesh-ui:
	uv pip install 'sqlmesh[web]' && uv run sqlmesh -p src/features ui