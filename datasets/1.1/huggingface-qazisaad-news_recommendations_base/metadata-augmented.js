window.__CROISSANT_DATA__ = {
  "@context": {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "citeAs": "cr:citeAs",
    "column": "cr:column",
    "conformsTo": "dct:conformsTo",
    "containedIn": "cr:containedIn",
    "cr": "http://mlcommons.org/croissant/",
    "data": {
      "@id": "cr:data",
      "@type": "@json"
    },
    "dataBiases": "cr:dataBiases",
    "dataCollection": "cr:dataCollection",
    "dataType": {
      "@id": "cr:dataType",
      "@type": "@vocab"
    },
    "dct": "http://purl.org/dc/terms/",
    "extract": "cr:extract",
    "field": "cr:field",
    "fileProperty": "cr:fileProperty",
    "fileObject": "cr:fileObject",
    "fileSet": "cr:fileSet",
    "format": "cr:format",
    "includes": "cr:includes",
    "isLiveDataset": "cr:isLiveDataset",
    "jsonPath": "cr:jsonPath",
    "key": "cr:key",
    "md5": "cr:md5",
    "parentField": "cr:parentField",
    "path": "cr:path",
    "personalSensitiveInformation": "cr:personalSensitiveInformation",
    "recordSet": "cr:recordSet",
    "references": "cr:references",
    "regex": "cr:regex",
    "repeated": "cr:repeated",
    "replace": "cr:replace",
    "sc": "https://schema.org/",
    "separator": "cr:separator",
    "source": "cr:source",
    "subField": "cr:subField",
    "transform": "cr:transform"
  },
  "@type": "sc:Dataset",
  "distribution": [
    {
      "@type": "cr:FileObject",
      "@id": "repo",
      "name": "repo",
      "description": "The Hugging Face git repository.",
      "contentUrl": "https://huggingface.co/datasets/qazisaad/news_recommendations_base/tree/refs%2Fconvert%2Fparquet",
      "encodingFormat": "git+https",
      "sha256": "https://github.com/mlcommons/croissant/issues/80"
    },
    {
      "@type": "cr:FileSet",
      "@id": "parquet-files-for-config-default",
      "name": "parquet-files-for-config-default",
      "description": "The underlying Parquet files as converted by Hugging Face (see: https://huggingface.co/docs/dataset-viewer/parquet).",
      "containedIn": {
        "@id": "repo"
      },
      "encodingFormat": "application/x-parquet",
      "includes": "default/*/*.parquet",
      "cr:examples": {
        "file_list": [],
        "file_count": 0,
        "includes": [
          "default/*/*.parquet"
        ]
      }
    }
  ],
  "recordSet": [
    {
      "@type": "cr:RecordSet",
      "dataType": "cr:Split",
      "key": {
        "@id": "default_splits/split_name"
      },
      "@id": "default_splits",
      "name": "default_splits",
      "description": "Splits for the default config.",
      "field": [
        {
          "@type": "cr:Field",
          "@id": "default_splits/split_name",
          "name": "split_name",
          "description": "The name of the split.",
          "dataType": "sc:Text"
        }
      ],
      "data": {
        "default_splits/split_name": "train"
      }
    },
    {
      "@type": "cr:RecordSet",
      "@id": "default",
      "name": "default",
      "description": "qazisaad/news_recommendations_base - 'default' subset.",
      "field": [
        {
          "@type": "cr:Field",
          "@id": "default/split",
          "name": "default/split",
          "description": "Split to which the example belongs to.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "parquet-files-for-config-default"
            },
            "extract": {
              "fileProperty": "fullpath"
            },
            "transform": {
              "regex": "default/(?:partial-)?(train)/.+parquet$"
            }
          },
          "references": {
            "field": {
              "@id": "default_splits/split_name"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "default/category",
          "name": "default/category",
          "description": "Column 'category' from the Hugging Face parquet file.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "parquet-files-for-config-default"
            },
            "extract": {
              "column": "category"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "default/sub-category",
          "name": "default/sub-category",
          "description": "Column 'sub-category' from the Hugging Face parquet file.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "parquet-files-for-config-default"
            },
            "extract": {
              "column": "sub-category"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "default/title",
          "name": "default/title",
          "description": "Column 'title' from the Hugging Face parquet file.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "parquet-files-for-config-default"
            },
            "extract": {
              "column": "title"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "default/times",
          "dataType": "sc:DateTime",
          "source": {
            "fileSet": {
              "@id": "parquet-files-for-config-default"
            },
            "extract": {
              "column": "times"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "default/url",
          "name": "default/url",
          "description": "Column 'url' from the Hugging Face parquet file.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "parquet-files-for-config-default"
            },
            "extract": {
              "column": "url"
            }
          }
        }
      ],
      "cr:examples": {
        "columns": [
          "split",
          "category",
          "sub-category",
          "title",
          "times",
          "url"
        ],
        "rows": [
          [
            "train",
            "lifestyle",
            "lifestyle",
            "Man tests biohacker Bryan Johnson's insane $2 MILLION anti-aging lifestyle for 75 DAYS to see if it's really possible to ... - Daily Mail",
            "2023-10-09 02:27:36",
            "https://news.google.com/rss/articles/CBMibGh0dHBzOi8vd3d3LmRhaWx5bWFpbC5jby51ay9mZW1haWwvYXJ0aWNsZS0xMjU4OTc0NS9JLXNwZW50LTc1LWRheXMtZm9sbG93aW5nLUJyeWFuLUpvaG5zb24tSU5TQU5FLWRpZXQuaHRtbNIBAA?oc=5&hl=en-US&gl=US&ceid=US:en"
          ],
          [
            "train",
            "lifestyle",
            "lifestyle",
            "Gestational diabetes care plan: Monitoring and lifestyle measures - Medical News Today",
            "2023-10-09 11:08:57",
            "https://news.google.com/rss/articles/CBMiSGh0dHBzOi8vd3d3Lm1lZGljYWxuZXdzdG9kYXkuY29tL2FydGljbGVzL2dlc3RhdGlvbmFsLWRpYWJldGVzLWNhcmUtcGxhbtIBAA?oc=5&hl=en-US&gl=US&ceid=US:en"
          ]
        ]
      }
    }
  ],
  "conformsTo": "http://mlcommons.org/croissant/1.1",
  "name": "news_recommendations_base",
  "description": "\n\t\n\t\t\n\t\tDataset Card for \"news_recommendations_base\"\n\t\n\nMore Information needed\n",
  "keywords": [
    "1K - 10K",
    "parquet",
    "Text",
    "Datasets",
    "pandas",
    "Croissant",
    "Polars",
    "🇺🇸 Region: US"
  ],
  "url": "https://huggingface.co/datasets/qazisaad/news_recommendations_base"
};
