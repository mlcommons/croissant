"""Tests for execute."""

from unittest import mock

import pandas as pd
import pytest

from mlcroissant._src.core.issues import GenerationError
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.execute import execute_downloads
from mlcroissant._src.operation_graph.execute import execute_operations_sequentially
from mlcroissant._src.operation_graph.operations import Data
from mlcroissant._src.operation_graph.operations import InitOperation
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.tests.nodes import create_test_file_object
from mlcroissant._src.tests.nodes import create_test_record_set
from mlcroissant._src.tests.nodes import empty_record_set


def test_execute_downloads():
    operations = Operations()
    node1 = create_test_file_object(name="node1")
    node2 = create_test_file_object(name="node2")
    download1 = Download(operations=operations, node=node1)
    download2 = Download(operations=operations, node=node2)
    data = Data(operations=operations, node=empty_record_set)
    operations.add_node(download1)
    operations.add_node(download2)
    operations.add_node(download2)
    operations.add_node(data)
    with mock.patch.object(Download, "__call__") as download_call, mock.patch.object(
        Data, "__call__"
    ) as data_call:
        execute_downloads(operations)
        assert download_call.call_count == 2
        data_call.assert_not_called()


def test_only_execute_needed_operations():
    operations = Operations()
    node = create_test_file_object()
    record_set = create_test_record_set(name="my-record-set")
    init = InitOperation(operations=operations, node=node)
    (
        init
        >> Download(operations=operations, node=node)
        >> ReadFields(operations=operations, node=record_set)
    )

    # This operation is isolated in the operation graph and should not be executed:
    init >> Data(operations=operations, node=record_set)

    with mock.patch.object(Download, "__call__") as download_call, mock.patch.object(
        Data, "__call__"
    ) as data_call, mock.patch.object(
        ReadFields, "__call__", return_value=pd.Series([])
    ) as read_field_mock:
        # Use list(iterator) to actually yield all operations and execute them.
        list(execute_operations_sequentially("my-record-set", operations))
        assert download_call.call_count == 1
        assert read_field_mock.call_count == 1
        assert data_call.call_count == 0


def test_raises_with_an_explicit_mlcroissant_exception():
    with mock.patch.object(Download, "__call__", side_effect=ValueError):
        operations = Operations()
        node = create_test_file_object()
        record_set = create_test_record_set(name="my-record-set")
        (
            InitOperation(operations=operations, node=node)
            >> Download(operations=operations, node=node)
            >> ReadFields(operations=operations, node=record_set)
        )
        with pytest.raises(GenerationError, match=".+Download\\(file_object_name\\)"):
            list(execute_operations_sequentially("my-record-set", operations))
