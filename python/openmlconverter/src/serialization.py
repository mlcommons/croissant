import datetime
import dateutil.parser


def deserialize_json(dct):
    for field, value in dct.items():
        if field.startswith("date"):
            dct[field] = dateutil.parser.parse(value)
    return dct


def serialize_json(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise ValueError(f"Object of type {type(obj)} not serializable.")
