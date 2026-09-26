"""CLI MCP client for sessions that cannot hot-load new tool registrations."""
import argparse
import asyncio
import base64
import json
import sys
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tool')
    parser.add_argument('--args', default='{}')
    parser.add_argument('--args-file')
    parser.add_argument('--code-file')
    parser.add_argument('--record', default='latest')
    args = parser.parse_args()
    arguments = json.loads(Path(args.args_file).read_text() if args.args_file else args.args)
    if args.code_file:
        arguments['code'] = Path(args.code_file).read_text(encoding='utf-8')
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / 'server.py')])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=300)) as session:
            await session.initialize()
            if args.tool == 'list':
                print((await session.list_tools()).model_dump_json(indent=2))
                return
            result = await session.call_tool(args.tool, arguments)
            directory = ROOT / 'runtime/receipts' / args.record
            directory.mkdir(parents=True, exist_ok=True)
            records = []
            for i, content in enumerate(result.content):
                if content.type == 'image':
                    path = directory / f'mcp_image_{i}.png'
                    path.write_bytes(base64.b64decode(content.data))
                    records.append({'image_received': str(path), 'mimeType': content.mimeType})
                elif content.type == 'text':
                    print(content.text)
                    records.append({'text': content.text})
            (directory / 'result.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
            if result.isError:
                raise RuntimeError('MCP tool returned an error')
            print(json.dumps({'receipt': str(directory), 'images': sum('image_received' in r for r in records)}))


if __name__ == '__main__':
    asyncio.run(main())
