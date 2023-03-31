import requests

OPENML_URL = "https://www.openml.org/api/v1/json"


def dataset_json(identifier: str) -> dict:
    url_data = f"{OPENML_URL}/data/{identifier}"
    response = requests.get(url_data)
    if not response.ok:
        msg = response.json()["error"]["message"]
        raise Exception(
            f"Error while fetching data from OpenML: '{msg}'.",
        )
    return response.json()["data_set_description"]
