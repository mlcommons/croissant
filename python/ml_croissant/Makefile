# flake8 enforces docstrings.
flake8:
	flake8 .

pyflakes:
	pyflakes .

pylint:
	pylint **/*.py

pytest:
	pytest .

pytype:
	pytype --jobs="$$(grep -c ^processor /proc/cpuinfo)" --config=./pyproject.toml

# Launch all tests as launched on GitHub actions.
# - Check types (pytype).
# - Check tests (pytest).
# - Check linters (pylint, pyflakes, flake8).
tests: pytype pytest pylint pyflakes flake8
