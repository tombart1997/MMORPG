"""Live, end-to-end MCP and GLB regression checks. Requires the sword study open."""
import asyncio
import base64
import hashlib
import json
import math
import socket
import struct
import sys
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent


def content_json(result):
    assert not result.isError, result
    return json.loads(next(c.text for c in result.content if c.type == 'text'))


def verify_glb():
    data = (ROOT / 'output/oathkeeper_sword.glb').read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    assert (magic, version, length) == (b'glTF', 2, len(data))
    json_length, json_type = struct.unpack_from('<II', data, 12)
    assert json_type == 0x4e4f534a
    doc = json.loads(data[20:20+json_length])
    binary_start = 20+json_length+8
    assert len(doc['meshes']) == 1
    assert not doc.get('cameras') and not doc.get('skins')
    assert all('uri' not in image and 'bufferView' in image for image in doc.get('images', []))
    normals = 0
    triangles = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4) == 4
            assert 'material' in primitive
            triangles += doc['accessors'][primitive['indices']]['count']//3
            accessor = doc['accessors'][primitive['attributes']['NORMAL']]
            view = doc['bufferViews'][accessor['bufferView']]
            assert accessor['componentType'] == 5126 and accessor['type'] == 'VEC3'
            start = binary_start + view.get('byteOffset',0) + accessor.get('byteOffset',0)
            for i in range(accessor['count']):
                normal = struct.unpack_from('<3f',data,start+i*view.get('byteStride',12))
                assert all(math.isfinite(v) for v in normal)
                assert .98 < sum(v*v for v in normal) < 1.02
                normals += 1
    return dict(bytes=len(data), meshes=len(doc['meshes']), materials=len(doc['materials']),
                triangles=triangles, packed_images=len(doc.get('images',[])), unit_normals_checked=normals)


async def main():
    checks = {}
    with socket.create_connection(('127.0.0.1',9877),timeout=5) as sock:
        sock.sendall(json.dumps(dict(type='inspect_scene',token='invalid')).encode())
        response = json.loads(sock.recv(65536))
        assert response['status'] == 'error' and 'Invalid local session token' in response['message']
        checks['invalid_token_rejected'] = True
    params = StdioServerParameters(command=sys.executable,args=[str(ROOT/'server.py')])
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=300)) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 6
            checks['mcp_tools'] = [t.name for t in tools.tools]
            before = content_json(await session.call_tool('inspect_scene',{}))
            names = [ob['name'] for ob in before['objects'] if ob['name'].startswith('Sword_')]
            assert len(names) == 20
            rendered = await session.call_tool('render_preview',dict(names=names,label='verification',views=['front'],resolution=128))
            metadata = content_json(rendered)
            image = next(c for c in rendered.content if c.type=='image')
            received = base64.b64decode(image.data)
            assert received.startswith(b'\x89PNG\r\n\x1a\n')
            assert received == Path(metadata['images'][0]).read_bytes()
            checks['mcp_render_png_sha256'] = hashlib.sha256(received).hexdigest()
            invalid = await session.call_tool('render_preview',dict(names=names,label='bad',views=['invalid']))
            assert invalid.isError
            outside = await session.call_tool('save_blend',dict(filename='../outside.blend'))
            assert outside.isError
            checks['invalid_view_and_path_rejected'] = True
            after = content_json(await session.call_tool('inspect_scene',{}))
            assert before == after, 'Preview/failed request changed source scene'
            checks['scene_preserved_after_render_and_failures'] = True
            validation = content_json(await session.call_tool('validate_asset',dict(names=names,expected_length_m=1.18)))
            assert not validation['warnings']
            assert not any(ob['issues'] for ob in validation['objects'])
            (ROOT/'output/blender_validation.json').write_text(json.dumps(validation,indent=2))
            checks['blender_validation_clean'] = True
    checks['glb'] = verify_glb()
    (ROOT/'output/pipeline_verification.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))


if __name__ == '__main__':
    asyncio.run(main())
