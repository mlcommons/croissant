"""datasets_test module."""

from etils import epath
from format.src import datasets
from format.src import errors
import numpy as np
import pytest


# End-to-end tests on real data. The data is in `tests/end-to-end/*.json`.
@pytest.mark.parametrize(
    ["filename", "error"],
    [
        # Metadata.
        [
            "metadata_missing_property_name.json",
            'Property "https://schema.org/name" is mandatory, but does not exist.',
        ],
        [
            "metadata_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "metadata_bad_type.json",
            (
                "The current dataset doesn't declare any node of type:"
                ' "http://mlcommons.org/schema/RecordSet"'
            ),
        ],
        # Distribution.
        [
            "distribution_missing_property_content_url.json",
            (
                'Property "https://schema.org/contentUrl" is mandatory, but does not '
                "exist."
            ),
        ],
        [
            "distribution_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "distribution_bad_contained_in.json",
            (
                'There is a reference to node named "THISDOESNOTEXIST" in node'
                ' "a-csv-table", but this node doesn\'t exist.'
            ),
        ],
        [
            # When the name misses, the context should still appear without the name.
            "distribution_missing_name.json",
            (
                r"\[dataset\(mydataset\) \> distribution\(\)\] Property "
                r'"https://schema.org/name" is mandatory'
            ),
        ],
        # Record set.
        [
            "recordset_missing_property_name.json",
            'Property "https://schema.org/name" is mandatory, but does not exist.',
        ],
        [
            "recordset_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "recordset_missing_context_for_datatype.json",
            (
                'Property "http://mlcommons.org/schema/dataType" is mandatory, but does'
                " not exist."
            ),
        ],
        # ML field.
        [
            "mlfield_missing_property_name.json",
            'Property "https://schema.org/name" is mandatory, but does not exist.',
        ],
        [
            "mlfield_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "mlfield_missing_source.json",
            'Node "a-record-set/first-field" is a field and has no source.',
        ],
        [
            "mlfield_bad_source.json",
            "Malformed source data: #{THISDOESNOTEXIST#field}.",
        ],
    ],
)
def test_static_analysis(filename, error):
    base_path = epath.Path(__file__).parent / "tests/graphs"
    with pytest.raises(errors.ValidationError, match=error):
        datasets.Dataset(base_path / filename)


def test_generation_titanic():
    titanic_config = (
        epath.Path(__file__).parent.parent.parent.parent
        / "datasets"
        / "titanic"
        / "metadata.json"
    )
    dataset = datasets.Dataset(titanic_config)
    records = dataset.records("passengers")
    records = iter(records)
    assert next(records) == {
        "passengers": {
            "survived": 1,
            "embarked": "S",
            "pclass": 1,
            "age": 29,
            "boat": "2",
            "body": "?",
            "num_siblings_spouses": 0,
            "name": "Allen, Miss. Elisabeth Walton",
            "fare": 211.3375,
            "cabin": "B5",
            "ticket": "24160",
            "gender": "female",
            "home_destination": "St Louis, MO",
            "num_parents_children": 0,
        }
    }
    assert next(records) == {
        "passengers": {
            "survived": 1,
            "embarked": "S",
            "pclass": 1,
            "age": 0.9167,
            "boat": "11",
            "body": "?",
            "num_siblings_spouses": 1,
            "name": "Allison, Master. Hudson Trevor",
            "fare": 151.55,
            "cabin": "C22 C26",
            "ticket": "113781",
            "gender": "male",
            "home_destination": "Montreal, PQ / Chesterville, ON",
            "num_parents_children": 2,
        }
    }


def test_generation_simple_join():
    titanic_config = (
        epath.Path(__file__).parent.parent.parent.parent
        / "datasets"
        / "simple-join"
        / "metadata.json"
    )
    dataset = datasets.Dataset(titanic_config)
    records = dataset.records("publications_by_user")
    records = iter(records)
    assert next(records) == {
        "publications_by_user": {
            "author_email": "john.smith@gmail.com",
            "author_fullname": "John Smith",
            "title": "A New Approach to Machine Learning Using Neural Networks",
        }
    }
    assert next(records) == {
        "publications_by_user": {
            "author_email": "jane.doe@yahoo.com",
            "author_fullname": "Jane Doe",
            "title": (
                "The Application of Machine Learning to Natural Language Processing"
            ),
        }
    }
    assert next(records) == {
        "publications_by_user": {
            "author_email": "david.lee@outlook.com",
            "author_fullname": "David Lee",
            "title": "The Use of Machine Learning to Predict the Stock Market",
        }
    }
    assert next(records) == {
        "publications_by_user": {
            "author_email": "mary.jones@hotmail.com",
            "author_fullname": "Mary Jones",
            "title": np.nan,
        }
    }
    with pytest.raises(StopIteration):
        next(records)
