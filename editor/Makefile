current_dir := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

black:
	docker run --rm --volume $(current_dir):/src --workdir /src pyfound/black:24.2.0 black \
		--line-length 88 \
		--exclude '.*\/node_modules\/' \
	.

isort:
	isort \
		--profile google \
		--line-length 88 \
		--use-parentheses \
		--project mlcroissant \
		--project components \
		--project core \
		--project events \
		--project views \
		--project state \
		--project utils \
		--multi-line 3 \
		--thirdparty datasets \
	.

format: black isort

pytest:
	PYTHONPATH=. pytest
