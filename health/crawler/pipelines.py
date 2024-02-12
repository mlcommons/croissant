# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import contextlib
import dataclasses
import json
import signal
import time

from crawler.items import CroissantItem
from crawler.items import DownloadedItem
import mlcroissant as mlc


def count(nodes, node_cls):
    return len([node for node in nodes if isinstance(node, node_cls)])


_CROISSANT_TIMEOUT_SECONDS = 5


class TimeoutError(Exception):
    pass


@contextlib.contextmanager
def timeout(seconds: int):
    def _handle_timeout(signum, frame):
        raise TimeoutError()

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class CrawlerPipeline:
    def process_item(self, download_item: DownloadedItem, spider) -> CroissantItem:
        item = CroissantItem(**dataclasses.asdict(download_item))
        if download_item.response_status == 200:
            with timeout(seconds=_CROISSANT_TIMEOUT_SECONDS):
                try:
                    metadata = None
                    start = time.time()
                    try:
                        jsonld = json.loads(download_item.body)
                        item.croissant_is_json = True
                        try:
                            metadata = mlc.Dataset(jsonld=jsonld).metadata
                            item.croissant_is_valid = True
                            nodes = metadata.nodes()
                            item.croissant_num_fields = count(nodes, mlc.Field)
                            item.croissant_num_file_objects = count(
                                nodes, mlc.FileObject
                            )
                            item.croissant_num_file_sets = count(nodes, mlc.FileSet)
                            item.croissant_num_record_sets = count(nodes, mlc.RecordSet)
                        except (json.JSONDecodeError, mlc.ValidationError):
                            item.croissant_is_valid = False
                            if metadata:
                                errors = [error for _, error in metadata.issues._errors]
                                item.croissant_errors = errors
                    except json.JSONDecodeError:
                        item.croissant_is_json = False
                    finally:
                        total = time.time() - start
                        item.croissant_validation_time = total
                except TimeoutError:
                    item.croissant_timeout_seconds = _CROISSANT_TIMEOUT_SECONDS
        return item
