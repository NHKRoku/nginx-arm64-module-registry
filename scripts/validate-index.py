#!/usr/bin/env python3
"""Validate generated module index invariants without third-party packages."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "index.json"
data = json.loads(path.read_text(encoding="utf-8"))

required = ("name", "description", "schema_version", "generated_at", "architecture", "os_family", "modules")
missing = [key for key in required if key not in data]
if missing:
    raise SystemExit(f"ERROR: index.json missing fields: {', '.join(missing)}")
if not isinstance(data["name"], str):
    raise SystemExit("ERROR: module index name must remain a string (this is not an NGINX UI plugin catalog)")
if data["schema_version"] != 1 or data["architecture"] != "arm64":
    raise SystemExit("ERROR: unsupported module index schema or architecture")

seen = set()
for module in data["modules"]:
    module_id = module.get("id")
    if not isinstance(module_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", module_id):
        raise SystemExit(f"ERROR: invalid module ID: {module_id!r}")
    if module_id in seen:
        raise SystemExit(f"ERROR: duplicate module ID: {module_id}")
    seen.add(module_id)
    if not module.get("binaries"):
        raise SystemExit(f"ERROR: module has no binary artifacts: {module_id}")
    for artifact in [module.get("source", {}), *module["binaries"]]:
        if not re.fullmatch(r"[a-f0-9]{64}", artifact.get("sha256", "")):
            raise SystemExit(f"ERROR: invalid SHA-256 for {module_id}")
print(f"Validated index.json ({len(data['modules'])} module(s)).")
