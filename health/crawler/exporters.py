"""Exporter to Parquet files."""

import dataclasses
import logging
import os

from etils import epath
import pyarrow as pa
import pyarrow.parquet as pq
from scrapy.exporters import BaseItemExporter

from crawler.items import CroissantItem


class ParquetItemExporter(BaseItemExporter):
    """
    Parquet exporter
    """

    def __init__(self, file, **kwargs):
        """
        Initialize exporter
        """
        super().__init__(**kwargs)
        self.file = file
        self.group_count = 0
        self.items = []

    def export_item(self, item: CroissantItem) -> CroissantItem:
        """
        Export a specific item to the file
        """
        # Create a new row group every 1000 lines
        if len(self.items) >= 1000:
            self._flush_table()
        self.items.append(dataclasses.asdict(item))
        return item

    def finish_exporting(self):
        """
        Triggered when Scrapy ends exporting. Useful to shutdown threads, close files etc.
        """
        self._flush_table()

    def _schema(self) -> pa.Schema:
        schema = []
        for field in dataclasses.fields(CroissantItem):
            if field.type is int:
                schema.append(pa.field(field.name, pa.int32()))
            elif field.type == int | None:
                schema.append(pa.field(field.name, pa.int32(), nullable=True))
            elif field.type is str:
                schema.append(pa.field(field.name, pa.string()))
            elif field.type == str | None:
                schema.append(pa.field(field.name, pa.string(), nullable=True))
            elif field.type is bytes:
                schema.append(pa.field(field.name, pa.binary()))
            elif field.type == bytes | None:
                schema.append(pa.field(field.name, pa.binary(), nullable=True))
            elif field.type is bool:
                schema.append(pa.field(field.name, pa.bool_()))
            elif field.type == bool | None:
                schema.append(pa.field(field.name, pa.bool_(), nullable=True))
            elif field.type == list[str]:
                schema.append(pa.field(field.name, pa.list_(pa.string())))
            else:
                raise ValueError(f"unsupported type: {field.type}")
        return pa.schema(schema)

    def _flush_table(self):
        """
        Writes the current row group to parquet file
        """
        if self.items:
            folder: epath.Path = epath.Path(__file__).parent.parent / self.file.name
            # If the path already exists as a file rather than a folder, delete it.
            if folder.exists() and not folder.is_dir():
                folder.rmtree()
            folder.mkdir(parents=True, exist_ok=True)
            filename = folder / f"{str(self.group_count).zfill(5)}.parquet"
            logging.info(f"Writing table to {os.fspath(filename)}")
            table = pa.Table.from_pylist(self.items, schema=self._schema())
            pq.write_table(table, os.fspath(filename))
            logging.info("Wrote table")
            self.group_count += 1
            self.items = []
