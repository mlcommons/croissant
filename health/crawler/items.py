# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import dataclasses


@dataclasses.dataclass(kw_only=True, repr=False)
class DownloadedItem:
    body: bytes
    dataset_id: str
    response_status: int
    source: str
    url: str
    timeout_seconds: int | None = None

    def __repr__(self):
        return f"DownloadedItem({self.dataset_id})"


@dataclasses.dataclass(kw_only=True, repr=False)
class CroissantItem(DownloadedItem):
    croissant_errors: list[str] = dataclasses.field(default_factory=list)
    croissant_num_fields: int | None = None
    croissant_num_file_objects: int | None = None
    croissant_num_file_sets: int | None = None
    croissant_num_record_sets: int | None = None
    croissant_is_json: bool = False
    croissant_is_valid: bool = False
    croissant_validation_time: int | None = None
    croissant_timeout_seconds: int | None = None

    def __repr__(self):
        return f"CroissantItem({self.dataset_id})"
