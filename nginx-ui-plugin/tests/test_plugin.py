import base64
import importlib.util
import json
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "server" / "main.py"
SPEC = importlib.util.spec_from_file_location("nginx_module_manager", MODULE_PATH)
PLUGIN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PLUGIN)


class PluginTests(unittest.TestCase):
    def test_initialize_handshake(self):
        response, should_exit = PLUGIN.dispatch({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "plugin.initialize",
            "params": {"host": {}, "settings": {}, "permissions": ["network"]},
        })
        self.assertFalse(should_exit)
        self.assertEqual(response["result"], {"api_version": 1, "capabilities": ["http"]})

    def test_exit_notification(self):
        response, should_exit = PLUGIN.dispatch({
            "jsonrpc": "2.0",
            "method": "plugin.exit",
            "params": {},
        })
        self.assertIsNone(response)
        self.assertTrue(should_exit)

    def test_unsupported_method(self):
        response, _ = PLUGIN.dispatch({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "not.a.method",
            "params": {},
        })
        self.assertEqual(response["error"]["code"], -32601)

    def test_http_is_read_only(self):
        response = PLUGIN.handle_http({"method": "POST", "path": "/api/registry"})
        self.assertEqual(response["status"], 405)
        payload = json.loads(base64.b64decode(response["body_base64"]))
        self.assertIn("read-only", payload["error"])

    def test_unknown_endpoint_does_not_fetch_registry(self):
        response = PLUGIN.handle_http({"method": "GET", "path": "/not-found"})
        self.assertEqual(response["status"], 404)

    def test_compatibility_requires_exact_target_metadata(self):
        registry = {
            "modules": [{
                "id": "headers-more",
                "name": "Headers More",
                "version": "v0.37",
                "binaries": [{
                    "os": "debian",
                    "debian_release": "13",
                    "architecture": "arm64",
                    "nginx_version": "1.28.0",
                }],
            }]
        }
        local = {
            "system": "linux",
            "machine": "aarch64",
            "os_id": "debian",
            "os_version": "12",
        }
        nginx = {"version": "1.31.8"}
        result = PLUGIN.compatibility(registry, local, nginx)
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["compatible"])
        self.assertFalse(result[0]["checks"]["debian_release"])
        self.assertFalse(result[0]["checks"]["nginx_version"])


if __name__ == "__main__":
    unittest.main()
