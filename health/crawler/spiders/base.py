import datetime
import logging
from typing import Any

from etils import epath
import polars as pl
from pydispatch import dispatcher
import scrapy
from scrapy import http
from scrapy import signals
from twisted.internet import error
from twisted.python import failure

from crawler.items import DownloadedItem

logging.getLogger("absl").addFilter(lambda _: False)

_TIMEOUT_SECONDS = 10


class BaseSpider(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        """Opens a connection to the local cache repository to do look-ups."""
        super().__init__(*args, **kwargs)
        self.df = self._scan_parquet_files()
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.date = datetime.datetime.now()

    def _scan_parquet_files(self) -> pl.LazyFrame | None:
        """Scans cached parquet files."""
        folder = epath.Path(__file__).parent.parent.parent / "data"
        parquet_files = list(folder.glob("*/*.parquet"))
        if parquet_files:
            logging.info(f"Found existing Parquet files {parquet_files}")
            return pl.scan_parquet(parquet_files)
        else:
            return None

    def list_datasets(self) -> list[Any]:
        """Returns the list of all datasets in the repository.

        Implement this class to overwrite the default.
        """
        raise NotImplementedError()

    def get_url(self, dataset: Any) -> None:
        """Gets the URL pointing the JSON-LD for a specific dataset.

        Implement this class to overwrite the default. This function takes into input
        every single element from `self.list_datasets`.
        """
        del dataset
        raise NotImplementedError()

    def start_requests(self):
        """See scrapy documentation for more details."""
        datasets = self.list_datasets()
        logging.info(f"Found {len(datasets)} dataset")
        for dataset in datasets:
            url = self.get_url(dataset)
            is_empty = (
                self.df is not None
                and self.df.filter(
                    (pl.col("url") == url) & (pl.col("source") == self.name)
                )
                .collect()
                .is_empty()
            )
            if self.df is not None and not is_empty:
                logging.info(f"Skipping {dataset} (already downloaded)")
                continue
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.parse_error,
                # Only wait 20 seconds, because some requests seem to timeout
                meta={
                    "download_timeout": _TIMEOUT_SECONDS,
                    "handle_httpstatus_list": self.settings.attributes[
                        "HTTPERROR_ALLOWED_CODES"
                    ].value,
                },
            )

    def parse(self, response: http.Response) -> DownloadedItem:
        """See scrapy documentation for more details."""
        return DownloadedItem(
            body=response.body,
            date=self.date,
            response_status=response.status,
            source=self.name,
            url=response.url,
        )

    def parse_error(self, failure: failure.Failure) -> DownloadedItem:
        # In order for timeouts to be processed, we add this callback:
        url = failure.request.url
        if failure.check(error.TimeoutError):
            return DownloadedItem(
                body=repr(failure),
                response_status=408,
                source=self.name,
                url=url,
                timeout_seconds=_TIMEOUT_SECONDS,
            )
        else:
            raise ValueError(f"unhandled failure in code: {failure}")

    def spider_closed(self, spider):
        del spider
        df = self._scan_parquet_files()
        if df is None:
            logging.info("No data written to disk yet")
        else:
            df = df.filter(pl.col("source") == self.name).collect()
            logging.info("Dumping an example of crawled data:")
            print(df.head())
