PYTHON ?= python3
PIP := $(PYTHON) -m pip

.PHONY: setup setup-python setup-web doctor clean-generated clean-generated-apply \
	test test-python test-web lint render-smoke generate-kokoro-audio

setup: setup-python setup-web

setup-python:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

setup-web:
	npm ci

doctor:
	$(PYTHON) scripts/doctor.py

clean-generated:
	$(PYTHON) scripts/clean_generated.py

clean-generated-apply:
	$(PYTHON) scripts/clean_generated.py --apply

test: test-python test-web

test-python:
	$(PYTHON) -m pytest -q

test-web:
	npm test

lint:
	npm run lint

render-smoke:
	manim -ql -s -r 540,960 --fps 15 test/test_code_execution_engine.py TestChalkboardCodeBlockScene

generate-kokoro-audio:
	$(PYTHON) scripts/generate_remotion_kokoro_audio.py
