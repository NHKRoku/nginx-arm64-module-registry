import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
manifest = json.loads((ROOT / "config/modules.json").read_text(encoding="utf-8"))

REPO = os.getenv("GITHUB_REPOSITORY", "OWNER/REPOSITORY")
TAG = os.getenv("GITHUB_REF_NAME", "")
REF_TYPE = os.getenv("GITHUB_REF_TYPE", "")
NGINX = os.getenv("NGINX_VERSION", "unknown")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


modules = []
is_release = REF_TYPE == "tag" and TAG.startswith("v")
release_base = f"https://github.com/{REPO}/releases/download/{TAG}" if is_release else None

for item in manifest["modules"]:
    module_id = item["id"]
    archive = DIST / f"{module_id}-debian13-arm64-nginx-{NGINX}.zip"
    source = DIST / f"{module_id}-source-{item['ref']}.tar.gz"
    if not archive.is_file() or not source.is_file():
        raise SystemExit(f"ERROR: expected build artifact missing for {module_id}")

    modules.append({
        "id": module_id,
        "name": item["name"],
        "description": item["description"],
        "version": item["ref"],
        "type": "dynamic",
        "repository": item["repository"],
        "source": {
            "filename": source.name,
            "download_url": f"{release_base}/{source.name}" if release_base else None,
            "sha256": sha256(source)
        },
        "binaries": [{
            "os": "debian",
            "debian_release": "13",
            "architecture": "arm64",
            "nginx_version": NGINX,
            "build_flavor": "nginx.org-upstream-source",
            "filename": archive.name,
            "download_url": f"{release_base}/{archive.name}" if release_base else None,
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
(ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
print("Generated index.json")
print("Modules:", len(modules))
