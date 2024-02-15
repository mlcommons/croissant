import dataclasses
import logging

from etils import epath
import huggingface_hub
import polars as pl
import scrapy
from scrapy import http
from twisted.internet import error
from twisted.python import failure

from crawler.items import DownloadedItem

logging.getLogger("absl").addFilter(lambda _: False)


@dataclasses.dataclass
class DatasetInfo:
    id: str


# For testing purposes
fake_datasets = [
    DatasetInfo(id="lkarjun/Malayalam-Articles"),
    DatasetInfo(id="lkndsjkndgskjngkjsndkj/jsjdjsdvkjvszlhdskb"),
    DatasetInfo(id="foo"),  # does not exist
    DatasetInfo(id="gcaillaut/citeseer"),  # timeout from mlcroissant
    DatasetInfo(id="Recag/Rp_CommonC_636_2"),  # 500
    DatasetInfo(id="common_voice"),  # timeout from Hugging Face
]

_TIMEOUT_SECONDS = 10


class HuggingfaceSpider(scrapy.Spider):
    name = "huggingface"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        folder = epath.Path(__file__).parent.parent.parent / "data"
        parquet_files = list(folder.glob("*/*.parquet"))
        if parquet_files:
            self.df = pl.scan_parquet(parquet_files)
            logging.info(f"Found existing Parquet files {parquet_files}")
        else:
            self.df = None

    def _url(self, dataset_id: str):
        return f"https://datasets-server.huggingface.co/croissant?dataset={dataset_id}"

    def start_requests(self):
        datasets = huggingface_hub.list_datasets()
        # Uncomment the following line to use fake datasets
        # datasets = fake_datasets
        for dataset in datasets:
            is_empty = (
                self.df is not None
                and self.df.filter(
                    (pl.col("dataset_id") == dataset.id)
                    & (pl.col("source") == self.name)
                )
                .collect()
                .is_empty()
            )
            if self.df is not None and not is_empty:
                logging.info(f"Skipping {dataset.id} (already downloaded)")
                continue
            url = self._url(dataset.id)
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.parse_error,
                cb_kwargs={"dataset_id": dataset.id},
                # Only wait 20 seconds, because some requests seem to timeout
                meta={
                    "download_timeout": _TIMEOUT_SECONDS,
                    "handle_httpstatus_list": self.settings.attributes[
                        "HTTPERROR_ALLOWED_CODES"
                    ].value,
                },
            )

    def parse(self, response: http.Response, dataset_id="") -> DownloadedItem:
        return DownloadedItem(
            body=response.body,
            dataset_id=dataset_id,
            response_status=response.status,
            source=self.name,
            url=response.url,
        )

    def parse_error(self, failure: failure.Failure) -> DownloadedItem:
        # In order for timeouts to be processed, we add this callback:
        cb_kwargs = failure.request.cb_kwargs
        url = failure.request.url
        if failure.check(error.TimeoutError):
            return DownloadedItem(
                body=repr(failure),
                dataset_id=cb_kwargs["dataset_id"],
                response_status=408,
                source=self.name,
                url=url,
                timeout_seconds=_TIMEOUT_SECONDS,
            )
        else:
            raise ValueError(f"unhandled failure in code: {failure}")
