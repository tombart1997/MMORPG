# Upstream bridge

`upstream_addon.py` is an unmodified copy of `addon.py` from
https://github.com/ahujasid/mcp-for-blender at commit
`8ce9f8d45be9370db420c9f6df521277f69819ab` (inspected 2026-09-26).
MIT license retained in `LICENSE`.

Reused: socket lifecycle, client threads, command queue, and Blender main-thread
timer dispatch. The upstream class explicitly requires a running GUI event loop.
Our subclass replaces command dispatch with six local workflow operations and
requires a session token. It does not register upstream add-on UI, external asset
services or telemetry handlers. No upstream MCP server/telemetry modules are loaded.

The original server's viewport screenshot capability is useful, but this test
needs repeatable camera renders and explicit image delivery. The small FastMCP
facade adds those, selected export and asset validation. It does not recreate
the upstream Blender transport or attempt a general plugin architecture.

The complete checkout used for inspection is ignored; only the vendored source
and license are committed. Upgrade deliberately and re-run live integration tests.
