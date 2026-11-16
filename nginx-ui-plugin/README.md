# NHKRoku NGINX Module Manager — NGINX UI plugin

This directory is the separate NGINX UI plugin project hosted in this monorepo. It is **not** the dynamic-module registry and is not yet a publishable Marketplace package.

## Responsibilities

The plugin will consume the module registry at:

`https://raw.githubusercontent.com/NHKRoku/nginx-arm64-module-registry/main/index.json`

Planned first milestones:

1. Read and validate the registry; browse modules and release artifacts.
2. Inspect the local NGINX binary version and build information.
3. Compare the local NGINX environment with each artifact's OS, architecture, NGINX version and build flavor.
4. Download artifacts only after explicit user action and verify SHA-256 before presenting an install action.
5. Later: stage module files, create backups, write a reviewed `load_module` snippet, run `nginx -t`, and require explicit confirmation before reload.

## Security boundary

NGINX UI plugins execute with the operating-system privileges of the NGINX UI process. This plugin must therefore use a narrow allowlist of filesystem and process operations. Never execute shell text assembled from registry data. Never auto-install, overwrite a module, edit the active configuration, or reload NGINX in the initial release.

The first release is intended to be read-only (discovery and compatibility inspection). Installation support is a later milestone with backups, path restrictions, dry-run output, config testing, and explicit confirmation.

## Catalog separation

The module registry remains at the repository root `index.json` and keeps its current schema. An NGINX UI Marketplace catalog is a different document with a localized `name` object and a `plugins` array. Do not point NGINX UI's Marketplace source at the module index. A plugin catalog entry and signed plugin package will be added only after this plugin passes the NGINX UI linter and conformance tests.

## Development target

- NGINX UI: 3.x plugin system
- Plugin ID target: `io.github.nhkroku.nginx-module-manager`
- Protocol: NGINX UI JSON-RPC 2.0 over newline-delimited stdio
- Package: NGINX UI `.tar.gz` plugin package, signed before distribution

See https://nginxui.com/plugin/overview and https://nginxui.com/plugin/quick-start.
