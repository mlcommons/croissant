# Croissant 🥐 Online Health

This project aims at monitoring the health of the online Croissant ecocystem
by crawling online JSON-LD files shared across repositories.

It contains:

- a `crawler/` using [Scrapy](https://scrapy.org) to find datasets on the web
  and produce Croissant statistics;
- a `visualizer/` to visualize the scraped data (at the moment done in notebooks).

## Launch locally

```bash
# Install needed dependencies.
pip install -r requirements.txt

# Test the spider locally.
# In huggingface.py you can uncomment the line in
# `list_datasets` to produce crawl fake data.
scrapy crawl huggingface

# When you're ready, the following commands launch a new job:
# Run the local Scrapy server.
scrapyd
# Deploy to the local Scrapy server.
scrapyd-deploy -p crawler
# Schedule the spider.
scrapyd-client schedule -p crawler huggingface

# Pops up a web interface to follow jobs progress.
scrapydweb
```

The most important parameter to fine-tune is `AUTOTHROTTLE_TARGET_CONCURRENCY`
in settings.py (number of parallel requests for AutoThrottle).

## TODO

- [ ] Expand to Kaggle and OpenML.
- [ ] Add unit tests.
