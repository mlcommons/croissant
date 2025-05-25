# Howto enable Croissant metadata in CKAN

[CKAN](https://ckan.org) can expose datasets using the Croissant metadata format via the [`ckanext-dcat`](https://github.com/ckan/ckanext-dcat) extension.
This guide explains how to install the extension, activate Croissant support and access the generated JSON-LD.

## Installation and activation

1. Install the extension in the CKAN Python environment:
   ```bash
   pip install ckanext-dcat>=2.3.0
   ```
2. Add `dcat` to the `ckan.plugins` list in your `ckan.ini`:
   ```ini
   ckan.plugins = dcat
   ```
   This automatically enables the Croissant profile provided by the extension.
3. Restart your CKAN instance so that the plugin is loaded.

## Accessing the Croissant metadata

Once activated, each dataset page includes a `<script type="application/ld+json">` block containing the Croissant JSON‑LD.
The same content can be retrieved from the dedicated endpoint:

```
https://YOUR-CKAN-URL/dataset/<dataset-id>/croissant
```

For resources stored in the CKAN DataStore, the JSON‑LD will describe the `RecordSet` objects with the names and types of the table columns.

## Links and references

See the extension's documentation for additional settings:
<https://github.com/ckan/ckanext-dcat#configuration>
