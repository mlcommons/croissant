# Croissant 🥐 Universe Explorer

A simple visual croissant explorer to find and discover datasets from the croissant universe.

Starting with openml as a reference example using the the data from the health crawl dump.

A maybe (; running live demo can be found here http://3.71.4.61:8050/

In the notebook we show how to prepare croissant metadata for projection into an embedding space which can then be visually explored as in the video below

[Screencast from 02-29-2024 05:01:31 PM.webm](https://github.com/luisoala/croissant/assets/26168435/5a9856e0-2089-4118-9652-bd46f2406824)

The main steps involve:

1. Read all croissant dataset descriptions from the openml crawl (>5k)
2. Extract dataset descriptions and urls from the croissant files.
3. Pipe the descriptions through sentence transformers embedder
4. Save the embeddings and urls as .csv for ingestion in the visualizer

The code for the visualizer dash app currently still lives at https://github.com/luisoala/croissant-universe-surfer/ to keep the croissant core repo light.  
