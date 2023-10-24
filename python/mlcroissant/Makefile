# flake8 enforces docstrings.
# Ignoring E203: This rule is in conflict when writing slices (`arr[i + 1 :]`).
# Ignoring E501: This rule is better checked by pylint with regular expressions.
# Ignoring W503: This rule goes against the PEP 8 recommended style.
flake8:
	flake8 . --ignore=E203,E501,W503

pyflakes:
	pyflakes .

pylint:
	pylint **/*.py

pytest:
	pytest .

pytype:
	pytype --jobs="$$(grep -c ^processor /proc/cpuinfo)" \
		--config=./pyproject.toml

mypy:
	mypy --config=./pyproject.toml mlcroissant/ \
		--show-error-codes \
		--allow-redefinition \
		--no-namespace-packages \
		--exclude=mlcroissant/scripts/migrations/

# Launch all tests as launched on GitHub actions.
# - Check types (pytype, mypy).
# - Check tests (pytest).
# - Check linters (pylint, pyflakes, flake8).
tests: pytype mypy pytest pylint pyflakes flake8
