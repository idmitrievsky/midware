.PHONY: install deps docs test

install:
	pip install .

deps:
	scripts/pin_deps.py

docs:
	pycco midware/*.py
	mv docs/__init__.html docs/index.html

test:
	pip install -r requirements.txt
	pytest
