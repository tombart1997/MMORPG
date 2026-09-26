"""One request per connection. Never retry mutations after an ambiguous timeout."""
import json
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def request(action, **params):
    command = dict(type=action, params=params, token=(ROOT / 'runtime/token').read_text().strip())
    with socket.create_connection(('127.0.0.1', 9877), timeout=5) as connection:
        connection.settimeout(240)
        connection.sendall(json.dumps(command).encode('utf-8'))
        data = bytearray()
        while True:
            block = connection.recv(65536)
            if not block:
                raise ConnectionError('Blender disconnected before completing the operation')
            data.extend(block)
            try:
                response = json.loads(data.decode('utf-8'))
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    if response['status'] != 'success':
        raise RuntimeError(response['message'])
    return response['result']
