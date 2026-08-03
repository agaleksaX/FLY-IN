.PHONY: install run debug clean lint lint-strict

PYTHON := python3
PIP := pip3

install:
	$(PIP) install -r requirements.txt
	pip install --upgrade pip

run:
	$(PYTHON) main.py $(MAP) $(FLAG)

debug:
	$(PYTHON) -m pdb main.py $(MAP) $(FLAG)

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict