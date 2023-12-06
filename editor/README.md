# Croissant Editor

Start locally from the
[Docker image](https://hub.docker.com/repository/docker/mlcommons/croissant-editor/general):

```bash
docker run -p 8501:8501 -v ~/.cache/croissant:/root/.cache/croissant -it mlcommons/croissant-editor
```

Navigate to http://localhost:8501.

Launch the end-to-end tests locally (after you started the application):

```bash
nvm use default  # We recommend managing NPM using NVM
npm install
npm run cypress:open  # Opens the Cypress application
npm run cypress:run  # Runs e2e tests in background
```

You can debug the tests in Github Actions because failed screenshots are uploaded as artifacts.

You may need to install [`libmagic`](https://pypi.org/project/python-magic).

# Create a custom component

Custom components are in `components/`.

### Launch the component locally

- In `components/tree/__init__.py`, change the constant `_RELEASE = False` to `_RELEASE = True`.
- Start the frontend with the newest version of Node:

```bash
cd components/tree/frontend
npm install
npm run start
```

### Display the component for easy debugging

```python
import streamlit as st

from components.tree import render_tree

nodes = [
    {"name": "data/splits.csv", "type": "FileObject", "parents": []},
    {"name": "data/cities.csv", "type": "FileObject", "parents": []},
    {"name": "github-repository", "type": "FileSet", "parents": []},
    {
        "name": (
            "this-is-a-file-with-a-very-very-very-very-very-very-very-very-long-name"
        ),
        "type": "FileObject",
        "parents": ["github-repository"],
    },
    {
        "name": "this-is-another-file-with-a-very-very-very-very-very-very-very-very-long-name",
        "type": "FileObject",
        "parents": [
            "this-is-a-file-with-a-very-very-very-very-very-very-very-very-long-name"
        ],
    },
    {"name": "huggingface-repository", "type": "FileSet", "parents": []},
    {
        "name": "file_*.parquet",
        "type": "FileSet",
        "parents": ["huggingface-repository"],
    },
    {
        "name": "annotations.json",
        "type": "FileObject",
        "parents": ["huggingface-repository"],
    },
    {
        "name": "PASS1.tar",
        "type": "FileObject",
        "parents": [],
    },
    {
        "name": "PASS2.tar",
        "type": "FileObject",
        "parents": [],
    },
    {
        "name": "PASS3.tar",
        "type": "FileObject",
        "parents": [],
    },
    {
        "name": "images",
        "type": "FileSet",
        "parents": ["PASS1.tar", "PASS2.tar", "PASS3.tar"],
    },
]
node = render_tree(nodes)
st.write(node)
```

### Build the component

- Build the JavaScript locally.

```
cd components/tree/frontend/
npm run build
```

- Don't forget to toggle `_RELEASE = True` back to `_RELEASE = False`.
- Commit your changes.

### Build the docker image

Change `TAG` below and execute the following commands:

```
TAG=0.0.1
IMAGE=croissant-editor
docker build -t ${IMAGE} .
docker login
for tag in latest ${TAG}
do
  docker tag ${IMAGE} mlcommons/${IMAGE}:${TAG}
  docker image push mlcommons/${IMAGE}:${TAG}
done
```
