import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

manifest = json.loads(
    (ROOT / "config/modules.json").read_text()
)

REPO = os.getenv("GITHUB_REPOSITORY", "OWNER/REPOSITORY")
TAG = os.getenv("GITHUB_REF_NAME", "")
REF_TYPE = os.getenv("GITHUB_REF_TYPE", "")
NGINX = os.getenv("NGINX_VERSION", "unknown")

def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()

modules = []

for item in manifest["modules"]:

    module_id = item["id"]

    archives = list(
        DIST.glob(
            f"{module_id}-debian13-arm64-nginx-{NGINX}.zip"
        )
    )

    sources = list(
        DIST.glob(f"{module_id}-source-*.tar.gz")
    )

    if not archives or not sources:
        continue

    archive = archives[0]
    source = sources[0]

    is_release = REF_TYPE == "tag" and TAG.startswith("v")

    binary_url = None
    source_url = None

    if is_release:
        base = f"https://github.com/{REPO}/releases/download/{TAG}"
        binary_url = f"{base}/{archive.name}"
        source_url = f"{base}/{source.name}"

    modules.append({
        "id": module_id,
        "name": item["name"],
        "description": item["description"],
        "version": item["ref"],
        "type": "dynamic",
        "repository": item["repository"],

        "source": {
            "filename": source.name,
            "download_url": source_url,
            "sha256": sha256(source)
        },

        "binaries": [{
            "os": "debian",
            "debian_release": "13",
            "architecture": "arm64",
            "nginx_version": NGINX,
            "build_flavor": "nginx.org-upstream-source",
            "filename": archive.name,
            "download_url": binary_url,
            "sha256": sha256(archive)
        }]
    })

index = {
    "name": "NGINX Debian ARM64 Module Registry",
    "description": "Community NGINX dynamic modules",
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "architecture": "arm64",
    "os_family": ["debian"],
    "modules": modules
}

(ROOT / "index.json").write_text(
    json.dumps(index, indent=2) + "\n"
)

print("Generated index.json")
print("Modules:", len(modules))
