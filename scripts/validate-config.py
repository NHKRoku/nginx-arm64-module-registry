#!/usr/bin/env python3
"""Validate the module build manifest and supported build profiles."""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "config/modules.json"
platforms_path = ROOT / "config/platforms.json"


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: {path.relative_to(ROOT)}: {exc}")


manifest = load(manifest_path)
platforms = load(platforms_path)

if manifest.get("schema_version") != 1:
    raise SystemExit("ERROR: unsupported config/modules.json schema_version")
if not isinstance(manifest.get("modules"), list) or not manifest["modules"]:
    raise SystemExit("ERROR: config/modules.json must contain a non-empty modules array")
if platforms.get("schema_version") != 1 or not isinstance(platforms.get("platforms"), list):
    raise SystemExit("ERROR: invalid config/platforms.json")

seen = set()
for item in manifest["modules"]:
    for key in ("id", "name", "description", "repository", "ref"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise SystemExit(f"ERROR: module is missing a non-empty {key}: {item!r}")
    module_id = item["id"]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", module_id):
        raise SystemExit(f"ERROR: invalid module ID: {module_id}")
    if module_id in seen:
        raise SystemExit(f"ERROR: duplicate module ID: {module_id}")
    seen.add(module_id)
    args = item.get("configure_args", [])
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise SystemExit(f"ERROR: configure_args must be an array of strings: {module_id}")

nginx_version = os.getenv("NGINX_VERSION", "1.28.0")
matching_profiles = []
for platform in platforms["platforms"]:
    for key in ("id", "os", "debian_release", "architecture", "build_flavor", "nginx_versions"):
        if key not in platform:
            raise SystemExit(f"ERROR: platform entry missing {key}: {platform!r}")
    if platform["architecture"] != "arm64":
        raise SystemExit(f"ERROR: unsupported architecture in current builder: {platform['architecture']}")
    if (
        platform["os"] == "debian"
        and platform["debian_release"] == "13"
        and platform["build_flavor"] == "nginx.org-upstream-source"
        and nginx_version in platform["nginx_versions"]
    ):
        matching_profiles.append(platform)

if not matching_profiles:
    raise SystemExit(
        f"ERROR: no configured Debian 13 ARM64 upstream-source profile supports NGINX {nginx_version}"
    )

print(
    f"Validated {len(manifest['modules'])} module(s); "
    f"NGINX {nginx_version} matches {len(matching_profiles)} platform profile(s)."
)
