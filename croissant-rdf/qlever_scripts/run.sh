#!/bin/bash
set -eo pipefail

t="$(date +%s)"

huggingface-rdf
qlever --qleverfile Qleverfile index --overwrite-existing
qlever start
docker run -d --publish 8176:7000 --name qlever.ui.huggingface-datasets$t docker.io/adfreiburg/qlever-ui
docker exec -it qlever.ui.huggingface-datasets$t bash -c "python manage.py configure olympics http://localhost:7019"
