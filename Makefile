PYTHON ?= python3
VENV_DIR ?= .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
RUN_PYTHON = $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(PYTHON))

.PHONY: setup setup-python setup-web doctor clean-generated clean-generated-apply \
	test test-python test-web lint deps-check deps-audit render-smoke

setup: setup-python setup-web

setup-python:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

setup-web:
	npm ci --ignore-scripts --no-audit --no-fund

doctor:
	$(RUN_PYTHON) scripts/doctor.py

clean-generated:
	$(RUN_PYTHON) scripts/clean_generated.py

clean-generated-apply:
	$(RUN_PYTHON) scripts/clean_generated.py --apply

test: test-python test-web

test-python:
	@test -x "$(VENV_PYTHON)" || (echo "Run 'make setup-python' first." && exit 1)
	$(VENV_PYTHON) -m pytest -q

test-web:
	npm test

lint:
	npm run lint

deps-check:
	@test -x "$(VENV_PYTHON)" || (echo "Run 'make setup-python' first." && exit 1)
	$(VENV_PYTHON) -m pip check
	npm ci --dry-run --ignore-scripts --no-audit --no-fund

deps-audit:
	@test -x "$(VENV_PYTHON)" || (echo "Run 'make setup-python' first." && exit 1)
	@$(VENV_PYTHON) -c "import pip_audit" >/dev/null 2>&1 || (echo "Install pip-audit separately: .venv/bin/python -m pip install pip-audit" && exit 1)
	$(VENV_PYTHON) -m pip_audit -r requirements.txt
	npm audit --audit-level=high

render-smoke:
	$(RUN_PYTHON) -m manim -ql -s -r 540,960 --fps 15 test/test_code_execution_engine.py TestChalkboardCodeBlockScene
