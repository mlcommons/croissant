"""Json (De)serialization of the DCF (Croissant) format

Typical usage:
    dcf_dict = json.load(f, object_hook=deserialize_dcf_json)
    json.dump(dcf_dict, f, default=serialize_dcf_json)
"""

import datetime
import dateutil.parser


def deserialize_dcf_json(dct: dict[str, any]) -> dict[str, any]:
    """
    In-place deserialization of a dictionary into their datatypes.

    Args:
        dct: a DCF dictionary containing raw values (e.g. a string instead of a datetime).

    Returns:
        a dictionary containing the proper datatypes (e.g. datetime instead of string).
    """
    for field, value in dct.items():
        if field.startswith("date"):
            datetime_ = dateutil.parser.parse(value)
            if len(value) == 10:
                dct[field] = datetime_.date()
            else:
                dct[field] = datetime_
    return dct


def serialize_dcf_json_field(obj: any) -> str:
    """
    Serialize a field into the proper string representation

    Args:
        obj: any object that is not json serializable by default.

    Returns:
        the String representation of the object

    Raises:
        ValueError Object of type [type] not serializable
    """
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise ValueError(f"Object of type {type(obj)} not serializable.")
