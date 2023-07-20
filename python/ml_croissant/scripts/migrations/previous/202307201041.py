"""Migrations for containedIn: https://github.com/mlcommons/croissant/issues/115."""


def _migrate_contained_in(contained_in: str | list[str]):
    if isinstance(contained_in, list):
        return [_migrate_contained_in(el) for el in contained_in]
    elif isinstance(contained_in, str):
        assert contained_in.startswith("#{")
        assert contained_in.endswith("}")
        return contained_in.replace("#{", "").replace("}", "")
    else:
        raise ValueError("Impossible case")


def up(json_ld):
    """Up migration that converts `containedIn` to the new format."""
    distributions = json_ld.get("distribution", [])
    if not isinstance(distributions, list):
        distributions = [distributions]
    for i, distribution in enumerate(distributions):
        if "containedIn" not in distribution:
            continue
        new_contained_in = _migrate_contained_in(distribution["containedIn"])
        json_ld["distribution"][i]["containedIn"] = new_contained_in
    return json_ld
