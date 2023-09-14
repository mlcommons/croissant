"""constants_test module."""

from mlcroissant._src.core.constants import TO_CROISSANT


def test_to_croissant_values_are_unique():
    deja_vu = {}
    for key, value in TO_CROISSANT.items():
        if value in deja_vu:
            raise ValueError(
                f"Keys {key} and {deja_vu[value]} define the same Croissant value:"
                f" {value}."
            )
        deja_vu[value] = key
