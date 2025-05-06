import openml
import requests

from croissant_rdf.croissant_harvester import CroissantHarvester

__author__ = "Vincent Emonet"


# https://www.openml.org/search?type=data&sort=runs&status=active&id=1464
# https://data.openml.org/datasets/0000/1464/dataset_1464_croissant.json
class OpenmlHarvester(CroissantHarvester):
    api_url = "https://data.openml.org/datasets/"

    def fetch_datasets_ids(self):
        datalist = openml.datasets.list_datasets(output_format="dataframe")
        if self.search:
            datalist = datalist[datalist["name"].str.contains(self.search, case=False, na=False)]
        return datalist["did"].astype(str).tolist()[: self.limit]

    def fetch_dataset_croissant(self, dataset_id: str):
        # 3 = https://data.openml.org/datasets/0000/0003/dataset_3_croissant.json
        # 44593 = https://data.openml.org/datasets/0004/44593/dataset_44593_croissant.json
        extended_id = f"{int(dataset_id):08d}"
        extended_id = f"{extended_id[:4]}/{extended_id[4:] if len(dataset_id) < 5 else dataset_id}"
        return requests.get(self.api_url + extended_id + f"/dataset_{dataset_id}_croissant.json", timeout=30)


def main():
    OpenmlHarvester.cli()


__all__ = ["OpenmlHarvester"]
