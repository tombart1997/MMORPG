# Live Blender asset workflow

Tested with **Blender 5.2.2 LTS and Godot 4.7.2 on Windows**, 2026-09-26.
This experiment creates one sword and does not replace any game assets.

The agent used real MCP `initialize`, `tools/list`, and `tools/call` requests to
modify a persistent Blender scene, receive rendered PNG image content, inspect
those images, and make subsequent edits. See [the visual review](REVIEW.md) and
[the image gallery](output/gallery.html).

## Start or resume

From the repository root, on this machine:

```powershell
# First installation only (already completed):
./blender/mcp_workflow/setup.ps1

# Start a dedicated live Blender instance with the saved study:
./blender/mcp_workflow/launch.ps1 -BlendFile ./blender/mcp_workflow/output/oathkeeper_sword.blend

# Or omit -BlendFile to start from a factory scene for a new task.
```

Leave that Blender process running. Do not use `--background`: the reused bridge
dispatches work through Blender's GUI main-thread event loop. `launch.ps1` requests
a hidden window and uses isolated Blender user resources. Blender may still show
its own UI. Closing the dedicated window disconnects MCP; relaunch it to reconnect.
The launcher refuses to take over an occupied port. It never terminates an existing
Blender process. The UI and logs remain useful for diagnosing an interrupted tool.

The **project-local `.codex/config.toml` is installed** with server
`blender_studio`; `codex mcp get blender_studio` verified its registration. Restart
the Codex session to discover the tools. The version-controlled
[config snippet](codex-config.toml) records the exact command/arguments. On another
checkout, update its absolute paths and merge it into the trusted project's
`.codex/config.toml`. The official [Codex MCP documentation](https://developers.openai.com/codex/mcp)
describes project-scoped configuration. No global Codex settings were changed.

This conversation could not hot-add a new native tool namespace. Instead,
`client.py` used the official MCP SDK to call the same stdio server. It saves the
actual returned image bytes, allowing the agent's local image viewer to inspect
them. This is a real MCP client, not a script runner masquerading as MCP.

```powershell
$py = './blender/mcp_workflow/.venv/Scripts/python.exe'
& $py ./blender/mcp_workflow/client.py list
& $py ./blender/mcp_workflow/client.py inspect_scene
& $py ./blender/mcp_workflow/client.py render_preview --args-file ./blender/mcp_workflow/examples/sword_preview.json --record manual_preview
```

With the CLI client, open every returned `runtime/receipts/<record>/mcp_image_*.png`
in the image-viewing tool. With native MCP, inspect the returned image content.
A successful render call is **not** visual approval.

## Available operations

| MCP tool | Purpose |
| --- | --- |
| `inspect_scene` | Complete active scene object list/hierarchy, transforms, dimensions, evaluated mesh statistics, material properties, modifiers, armature bones |
| `execute_python` | Reviewed live `bpy` edits: objects, meshes, modifiers, materials, cameras, rigs; recovery copy and submitted-code audit before execution |
| `render_preview` | Named selection in a temporary neutral studio; PNG paths **and MCP image content** |
| `validate_asset` | Scale, transforms, naming, topology, winding, duplicate geometry, materials, counts, optional required armature |
| `save_blend` | Save under `output/` |
| `export_gltf` | Named selection in the active scene only; `.glb` or separate `.gltf`; optional consolidation of unrigged mesh copies |

The integration reuses the socket/thread/main-thread timer implementation from
[MCP for Blender](https://github.com/ahujasid/mcp-for-blender), pinned to commit
`8ce9f8d45be9370db420c9f6df521277f69819ab`. See [provenance](vendor/PROVENANCE.md).
Our small subclass/facade adds studio inspection, local authentication, export and
validation. No upstream external asset services or telemetry modules are enabled.

`execute_python` is trusted local Python execution, **not a security sandbox**.
The bridge binds only to `127.0.0.1:9877` and requires the per-launch token in
ignored `runtime/token`. Only submit reviewed code. Do not expose the socket to a
network. Dedicated save/export/render tools constrain their output paths; Python
itself retains Blender's full process permissions. A recovery `.blend` is kept at
`runtime/before_last_edit.blend`; this does not automatically roll back failed code.

## Reusable visual inspection

`render_preview` accepts explicit `names`, an iteration `label`, `views`, a square
`resolution` (128–2048), and optional `focus` object for a close-up. Front is **-Y**,
up is **+Z**, and the other named views are `back`, `left`, `right`,
`three_quarter`, `rear_three_quarter`, and `top`. The convention is explicit; orient
other assets consistently before comparing them.

Evaluated world-space bounds drive orthographic framing with an 18% margin.
Temporary mesh copies freeze modifiers/current pose. Three neutral area lights,
a gray world, Cycles 32 samples and AgX make silhouettes and material boundaries
easy to compare. The temporary scene, objects, lights and camera are removed in
`finally`; the source scene and its render settings are preserved. Named objects
are shown intentionally, even if hidden in the original scene. This is an asset
isolation preview, not a simulation of its complete game environment.

For every substantive edit:

1. Inspect the scene; identify the asset by name.
2. State a concrete visual hypothesis and edit through MCP.
3. Render front and 3/4 at minimum, then actually view the returned PNGs.
4. Record weaknesses: silhouette, proportions, joins, material hierarchy and distance readability.
5. Change geometry/materials in response. Render/view again.
6. Check rear/side views and a close-up before approval.
7. Export, validate and inspect in Godot. Engine lighting/import can change the result.

Do not batch the historical iteration scripts and call that visual iteration.
They record this study's edit sequence; the saved blend is the editable source of
truth. Helpers evolved during review, so rerunning history with current helpers is
not a byte-for-byte recreation of every archived render.

## Verification

```powershell
# Requires the saved sword study open in the live studio:
& ./blender/mcp_workflow/.venv/Scripts/python.exe ./blender/mcp_workflow/verify_pipeline.py

# Isolated Godot import, statistics and optional real renderer captures:
./blender/mcp_workflow/validate_godot.ps1 -Capture
```

Reports are in `output/pipeline_verification.json`, `blender_validation.json` and
`godot_validation.json`. The live test checks authentication, tool discovery,
byte-identical PNG delivery, scene preservation, invalid view/path handling,
topology warnings, GLB structure, packed images and finite unit normals. No
polygon ceiling is imposed. The isolated Godot project imports the real GLB,
checks materials/mesh counts/bounds, and can capture close and 8 m perspective
views. The latter uses 60° FOV at 1280×720; it is a distance-readability fixture,
not an equipped character or full-game combat capture.

Final artifact: **8,796 triangles, one runtime mesh, eight material surfaces,
eight embedded texture images, 1.184 m overall length**. Twenty editable mesh
parts remain in the blend. Export consolidation acts on temporary evaluated
copies, preserving the source. Blender +Z becomes Godot +Y. The grip center is
the attachment origin. The blade is about 0.875 m long; the guard is 0.368 m wide.

## Limitations and recommendation

This proves a useful **static-prop authoring and visual-review pipeline**. Adopt it
for individual weapon/prop tasks with the render-review gate intact. This one test
does not establish autonomous production quality for an entire MMORPG library.

- The sword is a clean stylized asset; no AAA close-up realism is claimed. Its
  eight materials should eventually be consolidated/atlased for a large library.
  No LODs or equipped-character motion/clipping test were requested or produced.
- Rig inspection and generic bpy editing exist, but skinned animation export has
  not been proven by this rigid-sword test. Static consolidation explicitly rejects
  armatures and armature-modified meshes.
- Topology checks do not detect every self-intersection, intentional overlap,
  semantic unwanted object, or perceptual defect. Some asset types intentionally
  have open boundaries. Report results, then apply art judgment.
- No mouse/sculpt-brush interaction was used. The agent authored live bpy edits
  and evaluated real rendered output. The reusable studio focuses on asset
  geometry/materials; it does not reproduce arbitrary scene lighting or effects.
- Tool execution is synchronous. Do not resend a mutation after a timeout without
  inspecting the scene first; an operation may have finished after disconnection.
- This Windows sandbox blocked asyncio pipes and Blender export temporary-file
  access. Running the local client and dedicated Blender process outside the agent
  sandbox resolved it; normal user permissions suffice. No administrator install
  is required. Closing Blender also requires a relaunch, as tested in this session.

The original startup scene is preserved in the blend, but the sword study is
active. Exports explicitly exclude other scenes. The experiment's files live
entirely under `blender/mcp_workflow/`; existing production assets/gameplay were
not modified by this work.
