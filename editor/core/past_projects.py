import copy
import dataclasses
import os
import pickle
import time

from etils import epath

from .state import Metadata

METADATA_DIRECTORY: str = epath.Path("~").expanduser() / ".cache" / "croissant"
METADATA_FILE: str = METADATA_DIRECTORY / "previously_loaded"

# super simple, second tuple is for some metadata around when this file was originally created/loaded
projects: list[tuple[Metadata, int]] = []

loaded: bool = False


# inital load up of metadata file
def load_past_projects() -> list[Metadata]:
    global loaded
    global projects
    if not loaded:
        os.makedirs(METADATA_DIRECTORY, exist_ok=True)
        try:
            open(METADATA_FILE, "x")
        except:
            pass
        with open(METADATA_FILE, "rb+") as file:
            try:
                projects = pickle.loads(file.read())
            except:
                projects = []
        if not projects:
            projects = []
        loaded = True
    return projects


# move loaded project to the front so we can see it
def loaded_project(index: int) -> None:
    # bring selected item to the front of the list
    projects.insert(0, projects.pop(index))
    save_projects()


# run if a new croissant file is created, or if we load a new file
def add_new_project(metadata: Metadata) -> None:
    projects.insert(0, (metadata, time.time()))
    # check to see if we have more than 10 previous projects, remove older ones
    if len(projects) > 10:
        projects.pop()
    # save projects list back to the overall metadata file
    save_projects()


# save-as you go feature, first project is always the current one
def save_projects() -> None:
    os.makedirs(METADATA_DIRECTORY, exist_ok=True)
    with open(METADATA_FILE, "wb") as file:
        file.write(pickle.dumps(projects))
