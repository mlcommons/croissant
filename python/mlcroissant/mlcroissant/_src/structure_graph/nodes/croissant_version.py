from __future__ import annotations

import enum
from typing import Any

from mlcroissant._src.core.context import Context


class CroissantVersion(enum.Enum):
    """Major and minor versions of the Croissant standard."""

    V_0_8 = "http://mlcommons.org/croissant/0.8"
    V_1_0 = "http://mlcommons.org/croissant/1.0"

    @classmethod
    def from_jsonld(cls, ctx: Context, jsonld: Any) -> CroissantVersion:
        """Builds the class from the JSON-LD."""
        if isinstance(jsonld, CroissantVersion):
            return jsonld
        elif not jsonld:
            return CroissantVersion.V_0_8
        else:
            try:
                return CroissantVersion(jsonld)
            except (AttributeError, ValueError):
                ctx.issues.add_error(
                    "conformsTo should be a string or a CroissantVersion. Got:"
                    f" {jsonld}"
                )
                return CroissantVersion.V_0_8

    def to_json(self) -> str | None:
        """Serializes back to JSON-LD."""
        if self == CroissantVersion.V_0_8:
            # In 0.8, the field conformsTo doesn't exist yet.
            return None
        return self.value

    def __lt__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_0_8 < CroissantVersion.V_1_0."""
        return self.value < other.value

    def __le__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_0_8 <= CroissantVersion.V_1_0."""
        return self.value <= other.value

    def __gt__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_1_0 > CroissantVersion.V_0_8."""
        return self.value > other.value

    def __ge__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_1_0 >= CroissantVersion.V_0_8."""
        return self.value >= other.value
