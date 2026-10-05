"""base_operation_test module."""

import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.tests.nodes import create_test_record_set


class _CountingOperation(Operation):
    """Yields one row per call and records how many times it ran."""

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "calls", 0)

    def call(self, *args):
        object.__setattr__(self, "calls", self.calls + 1)

        def generate():
            yield {"row": self.calls}

        return generate()


def _operation() -> _CountingOperation:
    return _CountingOperation(
        operations=Operations(), node=create_test_record_set(id="record-set")
    )


def test_output_is_cached_when_asked_for_in_memory():
    operation = _operation()

    first = operation(set_output_in_memory=True)
    second = operation(set_output_in_memory=True)

    assert operation.calls == 1
    assert isinstance(first, pd.DataFrame)
    assert first is second


def test_generator_output_is_not_cached():
    """A generator is consumed by its caller, so it must not be memoized.

    Regression test: the cache was consulted and populated unconditionally, so
    the second call returned the exhausted generator from the first one and
    yielded nothing.
    """
    operation = _operation()

    first = list(operation(set_output_in_memory=False))
    second = list(operation(set_output_in_memory=False))

    assert operation.calls == 2
    assert not operation.has_output()
    assert first == [{"row": 1}]
    assert second == [{"row": 2}]


def test_a_cached_dataframe_is_not_served_to_a_streaming_caller():
    """Reading in memory first must not change what a generator caller receives."""
    operation = _operation()

    operation(set_output_in_memory=True)
    streamed = operation(set_output_in_memory=False)

    assert not isinstance(streamed, pd.DataFrame)
    assert list(streamed) == [{"row": 2}]
