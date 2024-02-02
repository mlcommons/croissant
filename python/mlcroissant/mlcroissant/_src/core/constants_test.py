"""constants_test module."""

from mlcroissant._src.core.constants import TO_CROISSANT
from mlcroissant._src.core.context import Context
from mlcroissant._src.tests.versions import parametrize_conforms_to


@parametrize_conforms_to()
def test_to_croissant_values_are_unique(conforms_to):
    ctx = Context(conforms_to=conforms_to)
    deja_vu = {}
    for key, value in TO_CROISSANT(ctx).items():
        if value in deja_vu:
            raise ValueError(
                f"Keys {key} and {deja_vu[value]} define the same Croissant value:"
                f" {value}."
            )
        deja_vu[value] = key
