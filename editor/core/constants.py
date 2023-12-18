import os

from etils import epath

import mlcroissant as mlc

# Authentication to Hugging Face:
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")
OAUTH_STATE = os.getenv("OAUTH_STATE")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

EDITOR_CACHE: epath.Path = mlc.constants.CROISSANT_CACHE / "editor"


def PAST_PROJECTS_PATH(user) -> epath.Path:
    base = EDITOR_CACHE / "projects"
    # If there is authentication, look up in the user's path:
    if OAUTH_CLIENT_ID:
        if user is None:
            raise Exception("Please, authenticate before using the application.")
        return base / user.username
    # Else look up at the root:
    else:
        return base


PROJECT_FOLDER_PATTERN = "%Y%m%d%H%M%S%f"

DF_HEIGHT = 150

# Tabs
OVERVIEW = "Overview"
METADATA = "Metadata"
RESOURCES = "Resources"
RECORD_SETS = "Record Sets"
TABS = [OVERVIEW, METADATA, RESOURCES, RECORD_SETS]

NAMES_INFO = (
    "Names are used as identifiers. They are unique and cannot contain special"
    " characters. The interface will replace any special characters."
)
