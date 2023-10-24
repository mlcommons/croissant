# flake8 enforces docstrings.
flake8:
	flake8 . --ignore=E203,W503

pyflakes:
	pyflakes .

pylint:
	pylint **/*.py

pytest:
	pytest .

pytype:
	pytype --jobs="$$(grep -c ^processor /proc/cpuinfo)" --config=./pyproject.toml

mypy:
	mypy --config=./pyproject.toml mlcroissant/ --show-error-codes --allow-redefinition

# Launch all tests as launched on GitHub actions.
# - Check types (pytype, mypy).
# - Check tests (pytest).
# - Check linters (pylint, pyflakes, flake8).
tests: pytype mypy pytest pylint pyflakes flake8
