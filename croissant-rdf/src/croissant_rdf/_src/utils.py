import logging
from typing import List

# Disable logger in your code with:
# logging.getLogger("croissant_rdf").setLevel(logging.WARNING)
logger = logging.getLogger("croissant_rdf")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def chunk_data(data: List, chunk_size: int):
    """Chunking data"""
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]
