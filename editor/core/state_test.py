"""Tests for state."""

from etils import epath

import mlcroissant as mlc

from .state import Metadata


def test_rename_record_set():
    ctx = mlc.Context()
    path = epath.Path(__file__).parent.parent / "cypress/fixtures/1.0/titanic.json"
    canonical_metadata = mlc.Metadata.from_file(ctx, path)
    metadata = Metadata.from_canonical(canonical_metadata)

    # Rename RecordSet:
    assert metadata.record_sets[0].id == "genders"
    assert metadata.record_sets[2].fields[1].id == "passengers/gender"
    assert metadata.record_sets[2].fields[1].references.field == "genders/label"
    metadata.rename_record_set("genders", "NEW_GENDERS")
    assert metadata.record_sets[0].id == "NEW_GENDERS"
    assert metadata.record_sets[2].fields[1].references.field == "NEW_GENDERS/label"

    # Rename Field:
    metadata.rename_field("label", "NEW_LABEL")
    assert metadata.record_sets[2].fields[1].references.field == "NEW_GENDERS/NEW_LABEL"

    # Rename Distribution:
    assert metadata.record_sets[2].fields[0].id == "passengers/name"
    assert metadata.record_sets[2].fields[0].source.file_object == "passengers.csv"
    metadata.rename_distribution("passengers.csv", "NEW_PASSENGERS.CSV")
    assert metadata.record_sets[2].fields[0].source.file_object == "NEW_PASSENGERS.CSV"
