# NGINX Debian ARM64 Module Registry

Public registry for NGINX dynamic modules.

## Supported environment

- Debian 13 build environment
- ARM64 / aarch64
- Dynamic NGINX modules
- Source archives
- Compiled shared objects
- SHA256 checksums

## Registry URL

https://raw.githubusercontent.com/OWNER/REPOSITORY/main/index.json

## Build

1. Edit config/modules.json.
2. Set NGINX_VERSION in the GitHub Actions workflow.
3. Push a tag beginning with v.
4. GitHub Actions builds and publishes the artifacts.

IMPORTANT:
The default build uses upstream NGINX source.
It is not automatically ABI-compatible with Debian's
separately packaged NGINX binary.

Use the same NGINX version and compatible build
configuration on your server. Test modules before
loading them into production.
