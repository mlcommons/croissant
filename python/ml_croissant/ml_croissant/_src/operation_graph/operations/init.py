"""Init operation module."""

import dataclasses
import logging

from ml_croissant._src.operation_graph.base_operation import Operation

@dataclasses.dataclass(frozen=True, repr=False)
class InitOperation(Operation):
    """Sets up other operations."""

    def __call__(self):
        logging.info("Setting up generation for dataset: %s", self.node.uid)
