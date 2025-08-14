.PHONY: venv install dev run test lint fmt up down

venv:
	python -m venv .venv

install: venv
	. .venv/bin/activate && pip install -U pip && pip install -e .[dev]

dev:
	. .venv/bin/activate && pip install -U pip && pip install -e .

test:
	. .venv/bin/activate && pytest -q

run:
	. .venv/bin/activate && python -m src.app

fmt:
	. .venv/bin/activate && ruff check --select I --fix .
	. .venv/bin/activate && ruff format .

lint:
	. .venv/bin/activate && ruff check .
