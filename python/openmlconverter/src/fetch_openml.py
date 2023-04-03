import requests

OPENML_URL = "https://www.openml.org/api/v1/json"


def _fetch(url: str) -> dict:
    response = requests.get(url)
    if not response.ok:
        msg = response.json()["error"]["message"]
        raise Exception(
            f"Error while fetching {url} from OpenML: '{msg}'.",
        )
    return response.json()


def dataset_json(identifier: str) -> dict:
    response_json = _fetch(f"{OPENML_URL}/data/{identifier}")
    return response_json["data_set_description"]


def features_json(identifier: str) -> dict:
    response_json = _fetch(f"{OPENML_URL}/data/features/{identifier}")
    return response_json["data_features"]["feature"]
