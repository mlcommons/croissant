import huggingface_hub

from crawler.spiders.base import BaseSpider


class HuggingfaceSpider(BaseSpider):
    name = "huggingface"

    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 20.0,
        "AUTOTHROTTLE_DEBUG": True,
    }

    def list_datasets(self):
        """See base class."""
        # Uncomment this early return for debugging purposes:
        # return [
        #     "lkarjun/Malayalam-Artiicles",
        #     "lkndsjkndgskjngkjsndkj/jsjdjsdvkjvszlhdskb",
        #     "foo",  # does not exist
        #     "Recag/Rp_CommonC_636_2",  # 500
        #     "common_voice",  # timeout from Hugging Face
        # ]
        return [dataset.id for dataset in huggingface_hub.list_datasets()]

    def get_url(self, dataset_id: str):
        """See base class."""
        return f"https://huggingface.co/api/datasets/{dataset_id}/croissant"
