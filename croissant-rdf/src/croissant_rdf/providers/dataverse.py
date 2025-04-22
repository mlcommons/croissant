import requests

from croissant_rdf.croissant_harvester import CroissantHarvester

__author__ = "Vincent Emonet"


# https://guides.dataverse.org/en/latest/admin/discoverability.html#schema-org-head
# curl -I https://demo.dataverse.org/dataset.xhtml?persistentId=doi:10.5072/FK2/KPY4ZC
class DataverseHarvester(CroissantHarvester):
    api_url = "https://demo.dataverse.org"

    def fetch_datasets_ids(self):
        search_url = f"{self.api_url}/api/search"
        # Here we query for items of type 'dataset'. Adjust the query as needed.
        params = {
            "q": self.search,
            # "q": "Soil",
            "type": "dataset",
            # "total_count": self.limit,
        }
        response = requests.get(search_url, params=params, timeout=30)
        results = response.json()
        return [result["global_id"] for result in results.get("data", {}).get("items", [])][: self.limit]

    def fetch_dataset_croissant(self, dataset_id: str):
        # https://demo.dataverse.org/api/datasets/export?exporter=croissant&persistentId=doi:10.70122/FK2/JFASVV
        return requests.get(
            f"{self.api_url}/api/datasets/export?exporter=croissant&persistentId={dataset_id}", timeout=30
        )


def main():
    DataverseHarvester.cli()


__all__ = ["DataverseHarvester"]
