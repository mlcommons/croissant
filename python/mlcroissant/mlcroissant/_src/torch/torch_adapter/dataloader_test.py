"""Test PyTorch utilities in torch modules."""

import pytest

import mlcroissant._src.torch.torch_adapter.dataloader as dataloader


@pytest.mark.parametrize(
    ["in_val", "expected_val", "data_type"],
    [
        ["Nos vemos mañana".encode("utf-8"), "Nos vemos mañana".encode("utf-8"), None],
        [
            "Nos vemos mañana".encode("utf-8"),
            "Nos vemos mañana",
            dataloader.LoaderSpecificationDataType.INFER,
        ],
        [
            "Nos vemos mañana".encode("utf-8"),
            "Nos vemos mañana",
            dataloader.LoaderSpecificationDataType.UTF8,
        ],
        [1, 1, dataloader.LoaderSpecificationDataType.INFER],
        [1, 1, None],
        [None, None, dataloader.LoaderSpecificationDataType.INFER],
        [None, None, None],
    ],
)
def test_data_transformation_helper(in_val, expected_val, data_type):
    new_val = dataloader.apply_data_type_transformation(in_val, data_type)
    assert new_val == expected_val
