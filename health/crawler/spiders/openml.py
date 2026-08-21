import openml

from crawler.spiders.base import BaseSpider


class OpenmlSpider(BaseSpider):
    name = "openml"

    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2,
        "AUTOTHROTTLE_MAX_DELAY": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 5.0,
        "AUTOTHROTTLE_DEBUG": True,
    }

    def list_datasets(self):
        """See base class."""
        return list(openml.datasets.list_datasets(output_format="dataframe")["did"])

    def get_url(self, dataset_id: str):
        """See base class."""
        return (
            f"https://openml1.win.tue.nl/datasets/{dataset_id // 10000:04d}/{dataset_id:04d}/dataset_{dataset_id}_croissant.json"
        )
