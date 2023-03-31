import json

import responses

import main
from fetch_openml import OPENML_URL
from serialization import deserialize_json
from .test_utils import path_test_resources


def test_happy_path():
    openml_identifier = "2"
    with responses.RequestsMock() as mocked_requests:
        mock_openml_responses(mocked_requests, openml_identifier)
        croissant_dict_actual = main.convert(openml_identifier)

    filename = path_test_resources() / "dcf" / f"openml_{openml_identifier}_expected.json"
    with open(filename, "r") as f:
        croissant_dict_expected = json.load(f, object_hook=deserialize_json)

    for expected_key, expected in croissant_dict_expected.items():
        actual = croissant_dict_actual[expected_key]
        assert actual == expected, f"field {expected_key}: actual:\n{actual}\n != \n{expected}\n"
    assert croissant_dict_actual == croissant_dict_expected


def mock_openml_responses(mocked_requests: responses.RequestsMock, openml_identifier: str):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """
    resources = path_test_resources() / "openml"
    with open(resources / f"data_{openml_identifier}.json", "r") as f:
        data_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/{openml_identifier}",
        json=data_response,
        status=200,
    )
