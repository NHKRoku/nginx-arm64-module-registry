#!/usr/bin/env python3
"""Read-only NGINX UI plugin for the NHKRoku ARM64 module registry."""

from __future__ import annotations

import base64
import json
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REGISTRY_URL = (
    "https://raw.githubusercontent.com/NHKRoku/"
    "nginx-arm64-module-registry/main/index.json"
)
MAX_MESSAGE = 4 * 1024 * 1024
MAX_REGISTRY = 2 * 1024 * 1024
PLUGIN_ID = "io.github.nhkroku.nginx-module-manager"


def log(message: str) -> None:
    print(f"[{PLUGIN_ID}] {message}", file=sys.stderr, flush=True)


def json_response(status: int, payload: Any) -> dict[str, Any]:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "status": status,
        "headers": {"Content-Type": ["application/json; charset=utf-8"]},
        "body_base64": base64.b64encode(body).decode("ascii"),
    }


def read_registry() -> dict[str, Any]:
    request = urllib.request.Request(
        REGISTRY_URL,
        headers={"Accept": "application/json", "User-Agent": "NHKRoku-Nginx-Module-Manager/0.1.0"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read(MAX_REGISTRY + 1)
    if len(raw) > MAX_REGISTRY:
        raise ValueError("Registry document exceeds the 2 MiB safety limit")

    document = json.loads(raw)
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("Unsupported module registry schema")
    modules = document.get("modules")
    if not isinstance(modules, list):
        raise ValueError("Registry has no valid modules array")

    # Treat registry content as data only. Never execute URLs, commands or paths
    # supplied by the registry.
    for module in modules:
        if not isinstance(module, dict):
            raise ValueError("Registry contains an invalid module entry")
        for binary in module.get("binaries", []):
            if not isinstance(binary, dict):
                raise ValueError("Registry contains an invalid binary entry")
            url = binary.get("download_url", "")
            if url and not (
                isinstance(url, str)
                and url.startswith("https://github.com/NHKRoku/nginx-arm64-module-registry/")
            ):
                raise ValueError("Registry contains a download URL outside the trusted repository")
    return document


def os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def nginx_info() -> dict[str, Any]:
    candidates = [
        shutil.which("nginx"),
        "/usr/sbin/nginx",
        "/usr/local/sbin/nginx",
        "/usr/local/nginx/sbin/nginx",
    ]
    executable = next((p for p in candidates if p and Path(p).is_file()), None)
    result: dict[str, Any] = {
        "found": False,
        "executable": executable,
        "version": None,
        "configure_arguments": "",
    }
    if not executable:
        return result

    try:
        completed = subprocess.run(
            [executable, "-V"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["error"] = str(exc)
        return result

    output = completed.stdout + "\n" + completed.stderr
    version_match = re.search(r"nginx version:\s*nginx/([^\s]+)", output)
    args_match = re.search(r"configure arguments:(.*)", output)
    result.update(
        {
            "found": completed.returncode == 0 and version_match is not None,
            "version": version_match.group(1) if version_match else None,
            "configure_arguments": args_match.group(1).strip() if args_match else "",
            "return_code": completed.returncode,
        }
    )
    return result


def local_platform() -> dict[str, Any]:
    release = os_release()
    return {
        "system": platform.system().lower(),
        "machine": platform.machine().lower(),
        "os_id": release.get("ID", "").lower(),
        "os_version": release.get("VERSION_ID", ""),
        "pretty_name": release.get("PRETTY_NAME", platform.platform()),
    }


def compatibility(registry: dict[str, Any], local: dict[str, Any], nginx: dict[str, Any]) -> list[dict[str, Any]]:
    matches = []
    for module in registry["modules"]:
        for binary in module.get("binaries", []):
            checks = {
                "architecture": local["machine"] in ("aarch64", "arm64")
                and binary.get("architecture") == "arm64",
                "os_family": local["system"] == "linux"
                and local["os_id"] in ("debian", "armbian")
                and binary.get("os") == "debian",
                "debian_release": local["os_version"] == str(binary.get("debian_release", "")),
                "nginx_version": bool(nginx.get("version"))
                and nginx.get("version") == binary.get("nginx_version"),
            }
            matches.append(
                {
                    "module_id": module.get("id"),
                    "module_name": module.get("name"),
                    "module_version": module.get("version"),
                    "binary": binary,
                    "checks": checks,
                    "compatible": all(checks.values()),
                    "limitations": [
                        "The registry does not currently record the complete NGINX configure arguments or build ID.",
                        "A version/platform match is not proof of ABI compatibility; test with nginx -t before loading any module.",
                    ],
                }
            )
    return matches


def handle_http(params: dict[str, Any]) -> dict[str, Any]:
    method = str(params.get("method", "GET")).upper()
    path = str(params.get("path", "/"))
    if method != "GET":
        return json_response(405, {"error": "Only GET is supported in this read-only release"})

    try:
        if path not in ("/api/registry", "/api/nginx", "/api/compatibility"):
            return json_response(404, {"error": "Not found"})
        registry = read_registry()
        local = local_platform()
        nginx = nginx_info()
        if path == "/api/registry":
            return json_response(200, registry)
        if path == "/api/nginx":
            return json_response(200, {"platform": local, "nginx": nginx})
        return json_response(
            200,
            {
                "registry": {
                    "name": registry.get("name"),
                    "generated_at": registry.get("generated_at"),
                    "schema_version": registry.get("schema_version"),
                },
                "platform": local,
                "nginx": nginx,
                "matches": compatibility(registry, local, nginx),
            },
        )
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        log(f"request failed: {exc}")
        return json_response(502, {"error": "Could not read or validate the module registry"})


def rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def dispatch(message: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    method = message.get("method")
    params = message.get("params") or {}
    request_id = message.get("id")
    is_notification = "id" not in message

    if not isinstance(params, dict):
        return (None if is_notification else rpc_error(request_id, -32602, "params must be an object"), False)

    if method == "plugin.initialize":
        result = {"api_version": 1, "capabilities": ["http"]}
    elif method in ("plugin.initialized", "plugin.configure", "plugin.ping", "plugin.shutdown"):
        result = {}
    elif method == "plugin.exit":
        return None, True
    elif method == "http.handle":
        result = handle_http(params)
    else:
        return (None if is_notification else rpc_error(request_id, -32601, "Method not found"), False)

    if is_notification:
        return None, False
    return {"jsonrpc": "2.0", "id": request_id, "result": result}, False


def main() -> int:
    for raw_line in sys.stdin.buffer:
        if len(raw_line) > MAX_MESSAGE:
            log("incoming JSON-RPC message exceeded 4 MiB; exiting")
            return 1
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            log("received malformed JSON-RPC input")
            continue
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            if isinstance(message, dict) and "id" in message:
                response = rpc_error(message.get("id"), -32600, "Invalid request")
                sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                sys.stdout.flush()
            continue

        response, should_exit = dispatch(message)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":"), ensure_ascii=False) + "\n")
            sys.stdout.flush()
        if should_exit:
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
