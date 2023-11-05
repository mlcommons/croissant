DF_HEIGHT = 150
import mlcroissant as mlc

EDITOR_CACHE = mlc.constants.CROISSANT_CACHE / "editor"
LOADED_CROISSANT = EDITOR_CACHE / "loaded_croissant"


def needed_field(text: str) -> str:
    return f"{text}:red[*]"
