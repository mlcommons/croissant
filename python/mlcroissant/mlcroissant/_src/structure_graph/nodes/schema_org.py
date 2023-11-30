from __future__ import annotations

import abc
import dataclasses

from mlcroissant._src.core.json_ld import remove_empty_values


@dataclasses.dataclass(eq=False, repr=False)
class Thing:
    """Base schema.org thing type"""

    def to_json(self) -> dict:
        return remove_empty_values(self.__dict__)

    alternateName: str | None = None
    description: str | None = None
    disambiguatingDescription: str | None = None
    image: str | None = None
    mainEntryOfPage: str | None = None
    name: str | None = None
    sameAs: str | None
    url: str | None = None


class Organization(Thing):
    address: str | None = None
    email: str | None = None
    funder: list[Person | Organization] = dataclasses.field(default_factory=list)


class Person(Thing):
    givenName: str | None = None
    additionalName: str | None = None
    address: str | None = None
    afilliation: Organization | None = None
    familyName: str | None = None
    email: str | None = None
    alumniOf: Organization | None = None
    funder: list[Person | Organization] = dataclasses.field(default_factory=list)
    memberOf: list[Organization] = dataclasses.field(default_factory=list)
    worksFor: list[Organization] = dataclasses.field(default_factory=list)
