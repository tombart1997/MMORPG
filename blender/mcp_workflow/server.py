"""MCP stdio interface: actual renders are returned as MCP image content."""
from mcp.server.fastmcp import FastMCP, Image
from transport import request, ROOT

mcp = FastMCP('Local Blender Studio')


@mcp.tool()
def inspect_scene() -> dict:
    """Inspect live hierarchy, transforms, evaluated mesh counts, materials and bones."""
    return request('inspect_scene')


@mcp.tool()
def execute_python(code: str) -> dict:
    """Execute trusted, reviewed bpy Python in live Blender; first save a recovery copy.

    Supports object, mesh, modifier, material, armature and camera editing. This is
    authenticated local code execution, NOT a Python security sandbox. Inspect the
    scene first. Render and LOOK at images after every meaningful visual change.
    """
    return request('execute_python', code=code)


@mcp.tool()
def render_preview(names: list[str], label: str, views: list[str] = ['front', 'three_quarter'],
                   resolution: int = 800, focus: str = '') -> list:
    """Render selected named objects in a temporary neutral studio and return actual PNGs.

    Views: front, back, left, right, three_quarter, rear_three_quarter, top.
    +Z is up, front is -Y. Optional focus object frames a close-up. Originals and
    scene settings are preserved. Labels identify iteration directories.
    """
    result = request('render_preview', names=names, label=label, views=views,
                     resolution=resolution, focus=focus)
    return [result, *[Image(path=p) for p in result['images']]]


@mcp.tool()
def validate_asset(names: list[str], require_armature: bool = False,
                   expected_length_m: float = 0.0) -> dict:
    """Report scale, transforms, topology, normals, duplicates, materials and counts.

    No arbitrary polygon ceiling. expected_length_m is optional art-specific scale.
    Does not replace visual review or actual target-engine import.
    """
    return request('validate_asset', names=names, require_armature=require_armature,
                   expected_length_m=expected_length_m)


@mcp.tool()
def save_blend(filename: str) -> dict:
    """Save the current scene under the workflow output directory."""
    return request('save_blend', filename=filename)


@mcp.tool()
def export_gltf(names: list[str], filename: str, merge_static_meshes: bool = False) -> dict:
    """Export ONLY named assets (and named rigs) to GLB or glTF under output/."""
    return request('export_gltf', names=names, filename=filename, merge_static_meshes=merge_static_meshes)


if __name__ == '__main__':
    mcp.run()
