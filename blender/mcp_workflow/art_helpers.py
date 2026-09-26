"""Small mesh construction helpers for the single sword experiment."""
import bpy
import bmesh
import math


def material(name, color, metallic=0, roughness=.4):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Roughness'].default_value = roughness
    mat.diffuse_color = (*color, 1)
    return mat


def mesh_object(name, verts, faces, mats, indices=None, bevel=0):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    for mat in mats:
        mesh.materials.append(mat)
    if indices:
        for poly, index in zip(mesh.polygons, indices):
            poly.material_index = index
    if bevel:
        mod = ob.modifiers.new('Forged edge radius', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    return ob


def prism(name, outline, depth, mat, bevel=.002):
    n = len(outline)
    verts = [(x, y, z) for y in (-depth/2, depth/2) for x, z in outline]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    return mesh_object(name, verts, faces, [mat], bevel=bevel)


def cylinder(name, z, depth, radius, mat, vertices=12, radius_top=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius if radius_top is None else radius_top,
                                  depth=depth, location=(0, 0, z))
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    bevel = ob.modifiers.new('Soft edges', 'BEVEL')
    bevel.width = .001
    bevel.segments = 2
    return ob


def remove(*names):
    for name in names:
        ob = bpy.data.objects.get(name)
        if ob:
            mesh = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)


def blade(name, rings, mats):
    # Each ring: height, half-width, central thickness. Broad bevels flank a
    # recessed fuller. Closed front/back mesh with deliberate material bands.
    section = [(-1, 0), (-.64, -1), (-.20, -1), (-.13, -.57), (.13, -.57),
               (.20, -1), (.64, -1), (1, 0), (.64, 1), (.20, 1), (.13, .57),
               (-.13, .57), (-.20, 1), (-.64, 1)]
    n = len(section)
    verts = []
    for ring in rings:
        z, w, t = ring[:3]
        groove = ring[3] if len(ring) > 3 else 1
        for x, y in section:
            if abs(x) in (.13, .20):
                x *= max(.025, groove)
            if abs(y) == .57:
                y = math.copysign(1 - .43*groove, y)
            verts.append((x*w, y*t, z))
    faces = [tuple(range(n-1, -1, -1))]
    indices = [0]
    for r in range(len(rings)-1):
        for i in range(n):
            faces.append((r*n+i, r*n+(i+1)%n, (r+1)*n+(i+1)%n, (r+1)*n+i))
            indices.append(1 if i in (0, 6, 7, 13) else 2 if i in (2, 3, 4, 9, 10, 11) and rings[r][0] < .73 else 0)
    faces.append(tuple((len(rings)-1)*n+i for i in range(n)))
    indices.append(1)
    return mesh_object(name, verts, faces, mats, indices)
