from __future__ import annotations

import abc
import dataclasses


@dataclasses.dataclass(eq=False, repr=False)
class Thing(abc.ABC):
    pass


class Person(abc.ABC):
    pass
