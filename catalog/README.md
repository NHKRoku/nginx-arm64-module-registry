# Catalog formats

This repository intentionally has two distinct catalog concepts.

## Dynamic-module registry

- URL: `https://raw.githubusercontent.com/NHKRoku/nginx-arm64-module-registry/main/index.json`
- File: `../index.json`
- Purpose: module metadata, source archives, binary artifacts and SHA-256 checksums.
- Schema: `module-index.schema.json`
- Its `name` is a string and it uses a `modules` array.

This is the registry consumed by the NGINX UI Module Manager plugin. It is **not** a Marketplace source.

## NGINX UI Marketplace catalog

NGINX UI Marketplace catalogs describe installable NGINX UI plugin packages. They use a localized `name` map and a `plugins` array, with package releases, platform downloads and SHA-256 checksums.

The upstream catalog schema is vendored as `nginx-ui-catalog.schema.json` from:

https://github.com/nginxui/plugin-spec/blob/main/schema/catalog.schema.json

The plugin project is in `../nginx-ui-plugin/`. A Marketplace catalog document and public source URL will be added only after the plugin passes `nginx-ui plugin lint` and `nginx-ui plugin conformance`, has a published release package, and the package has been signed. Do not replace the root module registry with this format.

For a self-hosted catalog, NGINX UI looks for `/v1/index.json` and then `/index.json` below the configured source address. Static hosting such as GitHub Pages can serve that layout.
