from etils import epath

import mlcroissant as mlc

EDITOR_CACHE: epath.Path = mlc.constants.CROISSANT_CACHE / "editor"
PAST_PROJECTS_PATH: epath.Path = EDITOR_CACHE / "projects"
PROJECT_FOLDER_PATTERN = "%Y%m%d%H%M%S%f"


DF_HEIGHT = 150
