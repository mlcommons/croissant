import os
import pickle
import shutil
import time

from etils import epath

import mlcroissant as mlc

from .state import Metadata

PREVIOUS_METADATA_DIRECTORY: str = mlc.constants.CROISSANT_CACHE / "previously_loaded"
MAX_PREVIOUS_PROJECTS: int = 10

# super simple:
# Metadata, creation date, last modified date
projects: list[list[Metadata, int, int]] = []

loaded_project_index: int | None = None

loaded: bool = False


# inital load up of metadata file
def load_past_projects() -> list[Metadata]:
    global loaded
    global projects
    if not loaded:
        os.makedirs(PREVIOUS_METADATA_DIRECTORY, exist_ok=True)
        for item in os.listdir(PREVIOUS_METADATA_DIRECTORY):
            try:
                filename = PREVIOUS_METADATA_DIRECTORY / item / "metadata"
                with open(filename, "rb+") as file:
                    projects.append(
                        [
                            pickle.loads(file.read()),
                            float(item),
                            os.path.getmtime(filename),
                        ]
                    )
            except:
                # wasn't a directory or was malformed, either way, skip it
                pass
        # order projects by last modified time
        projects = sorted(projects, key=lambda p: p[2], reverse=True)
        loaded = True
    return projects


# move loaded project to the front so we can see it
def loaded_project(index: int) -> None:
    global loaded_project_index
    # bring selected item to the front of the list
    projects[index][2] = time.time()
    projects.insert(0, projects.pop(index))
    os.utime(PREVIOUS_METADATA_DIRECTORY / str(projects[index][1]) / "metadata")
    loaded_project_index = index


def remove_last_project():
    shutil.rmtree(PREVIOUS_METADATA_DIRECTORY / str(projects[-1][1]))


# run if a new croissant file is created, or if we load a new file
def add_new_project(metadata: Metadata) -> None:
    projects.insert(0, [metadata, time.time(), time.time()])

    new_dir = PREVIOUS_METADATA_DIRECTORY / str(projects[0][1])
    os.makedirs(new_dir, exist_ok=True)

    with open(new_dir / "metadata", "wb") as file:
        file.write(pickle.dumps(metadata))

    # check to see if we have more than 10 previous projects, remove older ones
    if len(projects) > MAX_PREVIOUS_PROJECTS:
        remove_last_project()
    # load this project
    loaded_project(0)


def save_current_project() -> None:
    with open(
        PREVIOUS_METADATA_DIRECTORY
        / str(projects[loaded_project_index][1])
        / "metadata.json",
        "wb",
    ) as file:
        file.write(pickle.dumps(projects[loaded_project_index][0]))
