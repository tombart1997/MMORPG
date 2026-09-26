"""Live Blender entry point; uses the pinned upstream main-thread/socket bridge."""
import sys
from pathlib import Path
import importlib.util
import hmac
import json
import traceback
import os
import tempfile

ROOT = Path(__file__).resolve().parent
temp_dir = ROOT / 'runtime/tmp'
temp_dir.mkdir(parents=True, exist_ok=True)
os.environ['TEMP'] = os.environ['TMP'] = str(temp_dir)
tempfile.tempdir = str(temp_dir)
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('upstream_blender_mcp', ROOT / 'vendor/upstream_addon.py')
upstream = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = upstream
spec.loader.exec_module(upstream)
import operations


class StudioBridge(upstream.BlenderMCPServer):
    def execute_command(self, command):
        try:
            expected = (ROOT / 'runtime/token').read_text().strip()
            if not hmac.compare_digest(str(command.get('token', '')), expected):
                raise PermissionError('Invalid local session token')
            action = command['type']
            if action not in operations.HANDLERS:
                raise ValueError('Unsupported operation: ' + action)
            result = operations.HANDLERS[action](**command.get('params', {}))
            return {'status': 'success', 'result': result}
        except Exception:
            return {'status': 'error', 'message': traceback.format_exc()}


# No upstream UI registration, external asset services, or telemetry registration.
upstream._register_edit_capture_handlers = lambda: None
server = StudioBridge(host='127.0.0.1', port=9877)
server.start()
if not server.running:
    raise RuntimeError('Blender bridge could not start')
print('STUDIO_BRIDGE_READY', flush=True)
