import os

import requests
from huggingface_hub import list_datasets

from croissant_rdf.croissant_harvester import CroissantHarvester

__author__ = "David Steinberg"


class HuggingfaceHarvester(CroissantHarvester):
    api_url = "https://huggingface.co/api/datasets/"
    headers = {"Authorization": f"Bearer {os.environ.get('HF_API_KEY')}"} if os.environ.get("HF_API_KEY") else {}

    def fetch_datasets_ids(self):
        return [dataset.id for dataset in list(list_datasets(limit=self.limit, search=self.search))]

    def fetch_dataset_croissant(self, dataset_id: str):
        url = self.api_url + dataset_id + "/croissant"
        return requests.get(url, headers=self.headers if self.use_api_key else {}, timeout=30)
        # resp_json = None
        # try:
        #     response = requests.get(url, headers=self.headers if self.use_api_key else {}, timeout=30)
        #     resp_json = response.json()
        #     response.raise_for_status()
        #     return resp_json
        # except Exception as e:
        #     if resp_json and resp_json.get("error"):
        #         return f"Error for {url}: {resp_json['error']}"
        #     if not str(e):
        #         return "Empty error for " + url
        #     return f"Error for {url}: {e!s}"


def main():
    HuggingfaceHarvester.cli()


__all__ = ["HuggingfaceHarvester"]
