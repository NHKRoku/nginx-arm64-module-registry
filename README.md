# NHKRoku NGINX ARM64 Module Registry

Public registry of NGINX dynamic modules for Debian ARM64, with a separate NGINX UI plugin for read-only discovery and compatibility inspection.

## Projects and endpoints

| Project | Purpose | Catalog |
|---|---|---|
| Dynamic module registry | Source archives, compiled .so bundles, compatibility metadata and SHA-256 checksums | Root `index.json` |
| NGINX UI Module Manager | Browse registry modules and inspect the local NGINX host | Separate NGINX UI Marketplace catalog, published after package validation/signing |

Registry URL: https://raw.githubusercontent.com/NHKRoku/nginx-arm64-module-registry/main/index.json

The root index retains schema version 1. Its `name` is a string and its `modules` property contains dynamic-module records. It is **not** an NGINX UI Marketplace catalog. Do not add the root registry URL as an NGINX UI Marketplace source.

## NGINX UI plugin

The plugin lives in `nginx-ui-plugin/`. Its first release is intentionally read-only:

- Fetches and validates the root module registry.
- Detects local OS release, CPU architecture and NGINX version.
- Compares those values with published binary metadata.
- Shows the result in a static NGINX UI plugin page.

It does not download/install modules, edit NGINX configuration, run `nginx -t`, or reload NGINX. Metadata matches are preliminary and do not prove ABI compatibility; the registry does not yet record the complete target configure arguments/build ID.

Build and test it on a Linux ARM64 host with Python 3 and NGINX UI 3.x tooling:

```sh
cd nginx-ui-plugin
./build.sh
nginx-ui plugin lint .
nginx-ui plugin conformance .
nginx-ui plugin pack . io.github.nhkroku.nginx-module-manager-0.1.0-linux-arm64.tar.gz
```

A Marketplace catalog entry is deliberately not published yet. It must point to a real release package with SHA-256 and a valid signature. See `catalog/README.md` and `nginx-ui-plugin/README.md`.

## Dynamic-module registry build target

- Debian 13
- ARM64 / aarch64
- Upstream NGINX source, currently 1.28.0
- Dynamic modules built with `--with-compat`
- Source archives, ZIP bundles and SHA-256 checksums

The published binary is built against upstream NGINX source and the build configuration recorded in the registry. It is not automatically ABI-compatible with Debian's separately packaged NGINX binary, another NGINX version, or a custom build. Match the target NGINX version and configure arguments, then test with `nginx -t` before loading a module.

## Build a module release

1. Add a module entry to `config/modules.json` (id, name, description, repository, ref and optional configure_args).
2. Ensure its target platform is represented in `config/platforms.json`.
3. Set `NGINX_VERSION` in `.github/workflows/build.yml` to a version allowed by that platform profile.
4. Push a version tag such as `v1.1.0`.
5. GitHub Actions validates the manifest, builds on an ARM64 runner inside Debian 13, generates and validates `index.json`, uploads artifacts and publishes the GitHub Release.

For a manual build, run `bash scripts/build-modules.sh` in a Debian 13 ARM64 environment. The script installs its build dependencies and validates the manifest before compiling.

## Repository layout

    catalog/                   Registry schemas and catalog-format notes
    config/modules.json        Module source/build manifest
    config/platforms.json      Supported target build profiles
    scripts/                  Registry build and validation tooling
    nginx-ui-plugin/           NGINX UI plugin source, page and tests
    .github/workflows/         Build/release and validation workflows
    index.json                 Public dynamic-module registry (schema v1)

## Security and trust

- SHA-256 verifies artifact integrity, not publisher identity.
- Do not load an untrusted .so into a production NGINX process.
- Review source, build provenance and compatibility metadata.
- NGINX UI plugins run with the privileges of the NGINX UI process. Registry data is treated as data, never executable input.
- The first plugin release is read-only. Module installation and configuration changes require a separate hardened design.
