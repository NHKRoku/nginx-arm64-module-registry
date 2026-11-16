# Catalog formats

This repository intentionally has two catalog concepts:

- `../index.json`: the existing NGINX dynamic-module registry. Its `name` is a string and its schema is documented by `module-index.schema.json`.
- NGINX UI Marketplace catalog: a separate document describing installable NGINX UI plugin packages. It uses a localized `name` map and a `plugins` array and must be served at `/v1/index.json` when published.

Do not replace the root module registry with an NGINX UI Marketplace catalog. The Marketplace catalog is not generated until the plugin has a valid manifest, signed package, release asset and checksum.
