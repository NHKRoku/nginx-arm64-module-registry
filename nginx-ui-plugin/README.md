# NGINX Module Manager — NGINX UI plugin

A read-only NGINX UI plugin for browsing the NHKRoku ARM64 dynamic-module registry and checking basic compatibility against the local NGINX host.

## Current scope (0.1.0)

- Reads the fixed public registry URL: `https://raw.githubusercontent.com/NHKRoku/nginx-arm64-module-registry/main/index.json`.
- Validates the registry schema version and basic structure before using it.
- Shows the local OS, architecture and NGINX version.
- Compares registry binary metadata against the local OS release, architecture and NGINX version.
- Provides a static NGINX UI page at Plugins → NGINX Module Manager → NGINX Modules.
- Exposes read-only JSON endpoints below the plugin's authenticated HTTP route: `/api/registry`, `/api/nginx` and `/api/compatibility`.

## Explicitly not supported

This is a discovery and preliminary compatibility tool only. It does not download or install module binaries, write NGINX configuration, run `nginx -t`, or reload NGINX. The registry currently does not record the complete NGINX configure arguments/build ID, so matching metadata is not proof of ABI compatibility.

## Build

The first target is Linux ARM64 with Python 3:

```sh
./build.sh
```

This creates `dist/linux-arm64/nginx-module-manager`, the executable path declared in `plugin.json`. The launcher is a Python script and uses only the standard library.

## Validate with NGINX UI

Use an NGINX UI 3.x binary with plugin tooling:

```sh
./build.sh
nginx-ui plugin lint .
nginx-ui plugin conformance .
nginx-ui plugin pack . io.github.nhkroku.nginx-module-manager-0.1.0-linux-arm64.tar.gz
```

Do not publish a Marketplace catalog entry until lint and conformance pass, a package is built, its SHA-256 is calculated, and the package is signed. Unsigned packages require developer mode for local testing.

## Security

- The registry URL is fixed in code; registry-supplied URLs are never executed.
- Registry input is treated as data and size-limited.
- The plugin exposes GET-only HTTP endpoints.
- The only local process invocation is the fixed NGINX executable with the single `-V` argument; no shell is used.
- No file writes, module installation, configuration changes or reloads are implemented.
- The plugin process runs with NGINX UI's OS privileges. Install only after reviewing the source.
