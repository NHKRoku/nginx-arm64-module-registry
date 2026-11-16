# NHKRoku NGINX ARM64 Module Registry

Public registry of NGINX dynamic modules for Debian ARM64, with a separate NGINX UI plugin project planned in this repository.

## Projects and endpoints

| Project | Purpose | Catalog |
|---|---|---|
| Dynamic module registry | Source archives, compiled .so bundles, compatibility metadata and SHA-256 checksums | Root index.json |
| NGINX UI plugin | Discover registry modules and inspect local NGINX compatibility from NGINX UI | Separate NGINX UI Marketplace catalog |

Registry URL: https://raw.githubusercontent.com/NHKRoku/nginx-arm64-module-registry/main/index.json

The root index retains schema version 1. Its name is a string. It is not an NGINX UI Marketplace catalog. See catalog/README.md.

## Current build target

- Debian 13
- ARM64 / aarch64
- Upstream NGINX source, currently 1.28.0
- Dynamic modules built with --with-compat
- Source archives, ZIP bundles and SHA-256 checksums

The published binary is built against upstream NGINX source and the build configuration recorded in the registry. It is not automatically ABI-compatible with Debian's separately packaged NGINX binary, another NGINX version, or a custom build. Match the target NGINX version and configure arguments, then test with nginx -t before loading a module.

## Build a module release

1. Add a module entry to config/modules.json (id, name, description, repository, ref and optional configure_args).
2. Ensure its target platform is represented in config/platforms.json.
3. Set NGINX_VERSION in .github/workflows/build.yml to a version allowed by that platform profile.
4. Push a version tag such as v1.1.0.
5. GitHub Actions validates the manifest, builds on an ARM64 runner inside Debian 13, generates and validates index.json, uploads artifacts and publishes the GitHub Release.

For a manual build, run bash scripts/build-modules.sh in a Debian 13 ARM64 environment. The script installs its build dependencies and validates the manifest before compiling.

## Repository layout

    catalog/                  Module index schema and catalog-format notes
    config/modules.json       Module source/build manifest
    config/platforms.json     Supported target build profiles
    scripts/build-modules.sh  ARM64 dynamic module builder
    scripts/generate-index.py Root module index generator
    scripts/validate-config.py Build manifest validation
    scripts/validate-index.py Generated index validation
    nginx-ui-plugin/           Separate NGINX UI plugin project and security plan
    .github/workflows/         Build/release and validation workflows
    index.json                 Public dynamic-module registry (schema v1)

## NGINX UI plugin direction

The plugin project is kept separate from the module artifact registry. Its first milestone is read-only module discovery and local compatibility inspection. Installation support is a later milestone requiring checksum verification, constrained file operations, backups, a reviewed load_module snippet, nginx -t, and explicit confirmation before any reload.

NGINX UI plugins run with the privileges of the NGINX UI process. Registry data must never be treated as executable input. No automatic module installation, configuration mutation or NGINX reload is planned for the first release.

See nginx-ui-plugin/README.md and https://nginxui.com/plugin/overview.

## Security and trust

- SHA-256 verifies artifact integrity, not publisher identity.
- Do not load an untrusted .so into a production NGINX process.
- Review source, build provenance and compatibility metadata.
- The future NGINX UI plugin must be packaged and signed separately from module ZIPs.
