import argparse
import json
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Union

import requests
from rdflib import Graph, URIRef
from rich.progress import track

from croissant_rdf.utils import chunk_data, logger

DEFAULT_BASE_URL = "https://w3id.org/croissant-rdf/data/"

class CroissantHarvester(ABC):
    """Abstract base class for harvesting and processing Croissant metadata for datasets.

    This class defines a common interface for dataset harvesters targeting various providers.
    Child classes should override the abstract methods to implement custom fetching logic.
    The `api_url` attribute can be overridden either via subclass definition or during instantiation.
    """

    api_url: str = ""  # intended to be overridden in child classes

    def __init__(
        self,
        fname: str = "croissant_metadata.ttl",
        limit: int = 10,
        use_api_key: bool = True,
        search: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        serialization: str = "turtle",
        api_url: Optional[str] = None,
    ):
        """Initialize a Croissant metadata Harvester instance for a specific provider.

        Args:
            fname (str): The filename for the output Turtle file.
            limit (int): The maximum number of datasets to fetch.
            use_api_key (bool): Use API key for API requests.
            search (str): Search keywords to filter datasets.
            base_url (str): The base URL for the RDF graph, used as a prefix in generated RDF triples.
            api_url (str): The base URL for the API endpoint to fetch dataset metadata.
        """
        self.fname = fname
        self.limit = limit
        self.search = search
        self.base_url = base_url
        self.serialization = serialization
        self.use_api_key = use_api_key
        self.api_url = api_url if api_url is not None else self.__class__.api_url

    @abstractmethod
    def fetch_datasets_ids(self) -> List[str]:
        """Fetch a list of dataset identifiers from the provider."""
        pass

    @abstractmethod
    def fetch_dataset_croissant(self, dataset_id: str) -> requests.Response:
        """Fetch the Croissant metadata for a specific dataset from the provider using a HTTP request.

        Args:
            dataset_id (str): The ID of the dataset.

        Returns:
            requests.Response: The response from the request to retrieve metadata."""
        pass

    def fetch_dataset_croissant_handler(self, dataset_id: str) -> Optional[Union[Dict, List]]:
        """Run the function to fetch Croissant JSON-LD from URL, and catch exceptions to return them as strings.

        Args:
            dataset_id (str): The ID of the dataset.

        Returns:
            Optional[Union[Dict, List, str]]: The JSON-LD response as list/dict, or an error message as str.
        """
        resp_json = {}
        try:
            response = self.fetch_dataset_croissant(dataset_id)
            resp_json = response.json()
            response.raise_for_status()
            return resp_json
        except Exception as e:
            if resp_json.get("error"):
                return f"Error for {dataset_id}: {resp_json['error']}"
            if not str(e):
                return f"Empty error for {dataset_id}"
            return f"Error for {dataset_id}: {e!s}"


    def fetch_datasets_croissant(self) -> List[Dict]:
        """Fetch metadata for multiple datasets, using threading where applicable."""
        try:
            datasets = self.fetch_datasets_ids()
            logger.info(f"Retrieved {len(datasets)} datasets ID.")
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
            return []
        results = []
        errors = []
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(self.fetch_dataset_croissant_handler, dataset): dataset for dataset in datasets}
                for future in track(as_completed(futures), "Fetching datasets metadata", len(futures)):
                    result = future.result()
                    if isinstance(result, str):
                        errors.append(result)
                    else:
                        results.append(result)
        except KeyboardInterrupt:
            logger.warning("Process interrupted by user. Shutting down...")
            executor.shutdown(wait=False)
            raise
        if errors:
            logger.warning(
                f"Error fetching Croissant metadata JSON-LD for {len(errors)} URLs:\n" + "\n".join(errors)
            )
        return results

    def convert_to_rdf(self, data) -> str:
        """Take a JSON-serializable data structure, converts it to RDF using
        JSON-LD format, and serializes it into Turtle format, saving it to the specified file.

        Args:
            data (list|dict): The JSON-serializable data structure to convert to RDF.

        Returns:
            str: The path to the generated turtle file.
        """
        total_items = len(data)
        chunk_size = total_items // 100 if total_items > 100 else 1
        logger.info(
            f"Loading Croissant metadata JSON-LD to RDF graph. Total items: {total_items}, Chunk size: {chunk_size}"
        )
        g = Graph()
        g.bind("cr", "http://mlcommons.org/croissant/")
        g.bind("crdf", self.base_url)
        start_time = time.time()
        for chunk in track(chunk_data(data, chunk_size), "Parsing data", total_items):
            for item in chunk:
                item_json_ld = json.dumps(item)
                g.parse(data=item_json_ld, format="json-ld", base=URIRef(self.base_url))

        logger.info(
            f"Parsing completed in {time.time() - start_time:.2f}s, writing {len(g)} RDF triples to file {self.fname}"
        )
        start_time = time.time()
        g.serialize(destination=self.fname, format=self.serialization)
        logger.info(f"Serialization completed in {time.time() - start_time:.2f}s")
        return self.fname

    def generate_ttl(self) -> str:
        """Fetch datasets and generate a Turtle file.

        Returns:
            str: The path to the generated turtle file.

        Raises:
            Exception: If there was an error generating the turtle file.
        """
        logger.info(f"Searching {self.limit} datasets metadata{f' for `{self.search}`' if self.search else ''}.")
        try:
            start_time = time.time()
            datasets = self.fetch_datasets_croissant()
            # datasets = asyncio.run(self.afetch_datasets_croissant())
            logger.info(
                f"Retrieved Croissant metadata JSON-LD for {len(datasets)} datasets in {time.time() - start_time:.2f}s"
            )
            ttl_path = self.convert_to_rdf(datasets)

            return ttl_path
        except Exception as e:
            logger.error(f"Error generating TTL file: {e}")
            raise

    @classmethod
    def cli(cls):
        """Parse command-line arguments and generate a RDF file from harvested Croissant metadata."""
        parser = argparse.ArgumentParser(description="Generate a RDF file from datasets Croissant metadata.")
        parser.add_argument(
            "search",
            type=str,
            nargs="?",
            default=None,
            help="Search keywords to filter datasets.",
        )
        parser.add_argument(
            "--fname",
            type=str,
            required=False,
            default="croissant_metadata.ttl",
            help="The filename for the output Turtle file.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            required=False,
            default=10,
            help="The maximum number of datasets to fetch.",
        )
        parser.add_argument(
            "--format",
            type=str,
            required=False,
            default="turtle",
            help="The serialization format of the output RDF (turtle, n3, nt, xml, json-ld).",
        )
        parser.add_argument(
            "--base",
            type=str,
            required=False,
            default=DEFAULT_BASE_URL,
            help="The base URL used to .",
        )
        parser.add_argument(
            "--use_api_key",
            type=bool,
            required=False,
            default=True,
            help="Use API key for API requests.",
        )
        args = parser.parse_args()

        harvester = cls(
            fname=args.fname,
            limit=args.limit,
            use_api_key=args.use_api_key,
            search=args.search,
            serialization=args.format,
        )
        harvester.generate_ttl()

    # # TODO: using async fetching of Croissant metadata with httpx?
    # import asyncio
    # import httpx
    # # @abstractmethod
    # async def afetch_dataset_croissant(self, dataset_id: str, client: httpx.AsyncClient) -> Optional[Union[Dict, List, str]]:
    #     """Example for HuggingFace to test async fetching."""
    #     url = self.api_url + dataset_id + "/croissant"
    #     response = None
    #     try:
    #         response = await client.get(url, headers=self.headers if self.use_api_key else {}, timeout=30)
    #         response.raise_for_status()
    #         return response.json()
    #     except Exception as e:
    #         if response and response.json().get("error"):
    #             return f"Error for {url}: {response.json()['error']}"
    #         if not str(e):
    #             return "Empty error for " + url
    #         return str(e)

    # async def afetch_datasets_croissant(self) -> List[Dict]:
    #     """Asynchronously fetch metadata for multiple datasets concurrently."""
    #     try:
    #         datasets_ids = self.fetch_datasets_ids()
    #         logger.info(f"Retrieved {len(datasets_ids)} dataset IDs.")
    #     except Exception as e:
    #         logger.error(f"Error fetching dataset IDs: {e}")
    #         return []
    #     results = []
    #     errors = []
    #     async with httpx.AsyncClient(follow_redirects=True, limits=httpx.Limits(max_connections=20)) as client:
    #         # Create tasks for each dataset using the shared client.
    #         tasks = [self.afetch_dataset_croissant(dataset_id, client) for dataset_id in datasets_ids]
    #         for future in track(asyncio.as_completed(tasks), total=len(tasks), description="Fetching datasets metadata"):
    #             result = await future
    #             if isinstance(result, str):
    #                 errors.append(result)
    #             else:
    #                 results.append(result)
    #     if errors:
    #         logger.warning(f"Error fetching Croissant metadata JSON-LD for {len(errors)} URLs:\n{'\n'.join(errors)}")
    #     return results
