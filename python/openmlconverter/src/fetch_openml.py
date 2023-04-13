"""Fetching data from OpenML.

Instead of using the OpenML python bindings, simple API calls are made. This way we need to
depend on one less package.

Typical usage:
  dataset_json = fetch_openml.dataset_json(openml_id)
  features_json = fetch_openml.features_json(openml_id)
"""


import requests


OPENML_URL = "https://www.openml.org/api/v1/json"


def dataset_json(identifier: str) -> dict:
    """
    Fetch an OpenML dataset identified by the identifier

    Args:
        identifier: An OpenML identifier of a DataSet.

    Returns
        a dictionary with the OpenML representation of a Dataset.

    Raises:
        Exception: Error while fetching [url] from OpenML: [msg].
    """
    response_json = _fetch_json(f"{OPENML_URL}/data/{identifier}")
    return response_json["data_set_description"]


def features_json(identifier: str) -> list[dict]:
    """
    Fetch the features of an OpenML dataset identified by the identifier.

    Args:
        identifier: An OpenML identifier of a DataSet.

    Returns
        A list of dictionaries, one for each feature in the DataSet.

    Raises:
        Exception: Error while fetching [url] from OpenML: [msg].
    """
    response_json = _fetch_json(f"{OPENML_URL}/data/features/{identifier}")
    return response_json["data_features"]["feature"]


def _fetch_json(url: str) -> dict:
    """
    Fetch an url and return the json dict

    Args:
        url: The url to fetch.
    Raises:
        Exception: Error while fetching [url] from OpenML: [msg].
    """
    response = requests.get(url)
    if not response.ok:
        msg = response.json()["error"]["message"]
        raise Exception(
            f"Error while fetching {url} from OpenML: '{msg}'.",
        )
    return response.json()
