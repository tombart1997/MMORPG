"""Remove superseded scenery primitive generators; exports own presentation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'game/scripts/world/remaster_scenery.gd'
text=path.read_text()
if 'static func append(' in text:
    text=text.split('static func append(')[0]+'''static func mesh_for(kind: String) -> Mesh:
\tif meshes.has(kind): return meshes[kind]
\tmeshes[kind] = WorldAssetKit.mesh_for("rock0" if kind == "stone" else kind)
\treturn meshes[kind]
'''
    path.write_text(text)
path=ROOT/'game/scripts/world/settlement.gd';text=path.read_text()
start=text.index('\t_box(point + Vector3(0, 1.4, 0)') if '\t_box(point + Vector3(0, 1.4, 0)' in text else -1
if start>=0:
    end=text.index('func _sign(',start)
    text=text[:start]+text[end:]
    # _box calls remaining above are ground strips already handled by the
    # terrain shader. Remove dead box/window/roof presentation generators.
    text=text[:text.index('func _box(')]+'''func _box(_point: Vector3, _dimensions: Vector3, _color: Color, _collision_value: bool = false) -> void:
\tpass # Ground strips are painted into the terrain shader.

func _place(kind: String, point: Vector3, size_value: Vector3 = Vector3.ONE) -> void:
\tvar scene := ForgeModelCatalogue.scene_for("world",StringName(kind))
\tassert(scene != null,"Missing generated settlement model: "+kind)
\tvar model := scene.instantiate() as Node3D
\tmodel.position=point;model.scale=size_value;add_child(model)

func _collision(point: Vector3, dimensions: Vector3) -> void:
\tvar body:=StaticBody3D.new();var collider:=CollisionShape3D.new();var shape:=BoxShape3D.new()
\tshape.size=dimensions;collider.shape=shape;body.position=point
\tbody.add_child(collider);add_child(body)
'''
    path.write_text(text)
