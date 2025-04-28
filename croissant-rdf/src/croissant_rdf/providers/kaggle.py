import requests

from croissant_rdf.croissant_harvester import CroissantHarvester
from croissant_rdf.utils import logger

__author__ = "David Steinberg,Nelson Quinones"


class KaggleHarvester(CroissantHarvester):
    api_url = "https://www.kaggle.com/datasets/"

    def fetch_datasets_ids(self):
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except Exception:
            logger.warning("KAGGLE_USERNAME or KAGGLE_KEY are not set. Kaggle datasets IDs cannot be harvested.")

        api = KaggleApi()
        api.authenticate()
        # print([str(dataset) for dataset in api.dataset_list(search=self.search)[: self.limit]])
        return [str(dataset) for dataset in api.dataset_list(search=self.search)[: self.limit]]

    def fetch_dataset_croissant(self, dataset_id: str):
        return requests.get(self.api_url + str(dataset_id) + "/croissant/download", timeout=30)
        # return response.json() if response.status_code == 200 else None


def main():
    KaggleHarvester.cli()


__all__ = ["KaggleHarvester"]
