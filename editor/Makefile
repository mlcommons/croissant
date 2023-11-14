black:
	black \
		--line-length 88 \
		--preview \
	.

isort:
	isort \
		--profile google \
		--line-length 88 \
		--use-parentheses \
		--project mlcroissant \
		--project components \
		--project core \
		--project views \
		--project state \
		--project utils \
		--multi-line 3 \
		--thirdparty datasets \
	.

format: black isort

pytest:
	PYTHONPATH=. pytest
