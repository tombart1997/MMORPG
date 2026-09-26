"""Original Amber Scar art. Blender 5.x; no external assets or add-ons.

Reuses V2 rig/animation authorship; produces editable sources and consolidated GLBs.
All texture pixels are authored here from seeded periodic fields, not downloaded.
Run: blender --background --factory-startup --python-exit-code 1 --python blender/scripts/build_benchmark.py
"""
import bpy
import math
import json
import random
import sys
from pathlib import Path
from mathutils import Vector
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_characters as base
import build_turnwarden_v2 as tw

ROOT = base.ROOT
OUT = ROOT / 'game/assets/benchmark'
SRC = ROOT / 'blender/benchmark'
TEX = OUT / 'textures'
for folder in (OUT, SRC, TEX):
    folder.mkdir(parents=True, exist_ok=True)
REPORT = json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else {}
random.seed(921)


def texture(kind):
    n = 256
    y, x = np.mgrid[0:n, 0:n].astype(float) / n
    rng = np.random.default_rng(sum(map(ord, kind)))
    field = np.zeros((n, n))
    for f, a in [(3, .30), (7, .19), (17, .10), (43, .045), (97, .018)]:
        grid = rng.random((f, f)) * 2 - 1
        ix, iy = (x*f).astype(int), (y*f).astype(int)
        fx, fy = x*f-ix, y*f-iy
        fx, fy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
        field += a * ((grid[iy%f,ix%f]*(1-fx)+grid[iy%f,(ix+1)%f]*fx)*(1-fy)+(grid[(iy+1)%f,ix%f]*(1-fx)+grid[(iy+1)%f,(ix+1)%f]*fx)*fy)
    if kind in ('bark', 'hide'):
        grain = np.sin(x * math.tau * 9 + 1.6 * np.sin(y * math.tau * 2) + field*4)
        h = field * .65 + grain * .16 - np.power(np.maximum(0, grain), 14) * .26
    elif kind == 'cloth':
        h = field * .15 + .04 * (np.sin(x * math.tau * 90) + np.sin(y * math.tau * 90))
    elif kind == 'metal':
        h = field * .18 + .013 * np.sin(y * math.tau * 87)
    elif kind == 'leather':
        h = field * .26 + rng.random((n, n)) * .035
    else:
        h = field + rng.random((n,n))*.025
    value = np.clip(.72 + h, .18, 1)
    maps = {}
    for channel in ('color', 'normal', 'rough'):
        pixels = np.ones((n, n, 4), dtype=np.float32)
        if channel == 'color':
            for k in range(3): pixels[:, :, k] = value
        elif channel == 'rough':
            pixels[:, :, :3] = np.clip(.75 + h[:, :, None] * .7, .3, 1)
        else:
            dx = (np.roll(h, 1, 1) - np.roll(h, -1, 1)) * 2.1
            dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 2.1
            normal = np.stack((dx, dy, np.ones_like(dx)), axis=2)
            normal /= np.linalg.norm(normal, axis=2)[:, :, None]
            pixels[:, :, :3] = normal * .5 + .5
        name = kind + '_' + channel
        img = bpy.data.images.new(name, n, n, alpha=True)
        img.colorspace_settings.name = 'sRGB' if channel == 'color' else 'Non-Color'
        img.pixels.foreach_set(pixels.ravel())
        img.filepath_raw = str(TEX / (name + '.png'))
        img.file_format = 'PNG'
        img.save()
        maps[channel] = img.filepath_raw
    return maps


MAPS = {kind: texture(kind) for kind in ('bark', 'hide', 'stone', 'soil', 'cloth', 'metal', 'leather', 'leaf')}


def material(name, color, kind='bark', metal=0, rough=.85, emission=0):
    mat = base.material(name, color, metal, rough)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    # Tint baked into image to keep exported GLB material single-pass and portable.
    image = bpy.data.images.load(MAPS[kind]['color'], check_existing=True).copy()
    image.name = name + '_albedo'
    pix = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    pix[:, :3] *= np.array(color)
    image.pixels.foreach_set(pix.ravel())
    image.filepath_raw = str(TEX / (name + '_albedo.png'))
    image.save()
    image.pack()
    albedo = nodes.new('ShaderNodeTexImage'); albedo.image = image
    links.new(albedo.outputs['Color'], bsdf.inputs['Base Color'])
    normal_tex = nodes.new('ShaderNodeTexImage')
    normal_tex.image = bpy.data.images.load(MAPS[kind]['normal'], check_existing=True)
    normal_tex.image.colorspace_settings.name = 'Non-Color'
    normal = nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value = .45
    links.new(normal_tex.outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    rough_tex = nodes.new('ShaderNodeTexImage')
    rough_tex.image = bpy.data.images.load(MAPS[kind]['rough'], check_existing=True)
    rough_tex.image.colorspace_settings.name = 'Non-Color'
    # Roughness texture has its material-specific response baked in.
    rim = rough_tex.image.copy(); rim.name = name + '_rough'
    rp = np.array(rim.pixels[:], dtype=np.float32).reshape(-1, 4)
    rp[:, :3] = np.clip(rp[:, :3] * rough / .75, .08, 1)
    rim.pixels.foreach_set(rp.ravel()); rim.filepath_raw = str(TEX / (name + '_rough.png')); rim.save(); rim.pack()
    rough_tex.image = rim
    links.new(rough_tex.outputs['Color'], bsdf.inputs['Roughness'])
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    return mat


def mesh(name, verts, faces, mat, bone=None, rig=None, smooth=True):
    obj = base.mesh_object(name, verts, faces, mat, [{bone: 1}] * len(verts) if bone else None, rig)
    for face in obj.data.polygons: face.use_smooth = smooth
    return obj


def branch(name, points, widths, mat, bone=None, rig=None, sides=10, seed=0):
    """Irregular, ridged cross-sections following an authored bent centerline."""
    # Smooth the authored gesture while retaining taper and asymmetric fluting.
    if len(points)>2:
        controls=[Vector(p) for p in points]
        expanded=[]; radii=[]
        for i in range(len(controls)-1):
            p0,p1,p2,p3=controls[max(0,i-1)],controls[i],controls[i+1],controls[min(len(controls)-1,i+2)]
            for j in range(3):
                t=j/3
                expanded.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
                a,b=widths[i],widths[i+1]
                radii.append(tuple(v*(1-t)+w*t for v,w in zip(a,b)) if isinstance(a,tuple) else a*(1-t)+b*t)
        points=expanded+[controls[-1]]; widths=radii+[widths[-1]]
    obj = base.tube(name, points, widths, mat, [{bone: 1}] * len(points) if bone else None, rig, sides)
    for j, center in enumerate(points):
        for k in range(sides):
            v = obj.data.vertices[j * sides + k]
            v.co = Vector(center) + (v.co - Vector(center)) * (1 + .12 * math.sin(k * 2.7 + seed) + .055 * math.sin(j * 1.9 + k))
    uv=obj.data.uv_layers.new(name='ArtUV')
    lengths=[0.0]
    for j in range(1,len(points)): lengths.append(lengths[-1]+(Vector(points[j])-Vector(points[j-1])).length)
    for face in obj.data.polygons:
        around=[obj.data.loops[i].vertex_index%sides for i in face.loop_indices]
        seam=max(around)-min(around)>sides/2
        for li in face.loop_indices:
            vi=obj.data.loops[li].vertex_index
            k=vi%sides
            u=1.0 if seam and k==0 else k/sides
            uv.data[li].uv=(u,lengths[vi//sides]*.48)
    return obj


def leaf(name, root, tip, width, mat, bone=None, rig=None):
    a, b = Vector(root), Vector(tip)
    d = b - a
    side = d.cross(Vector((0, 0, 1))).normalized()
    if side.length < .1: side = Vector((1, 0, 0))
    middle = a.lerp(b, .46)
    ridge = middle + Vector((0, 0, width * .22))
    verts = [a, middle + side * width, b, middle - side * width, ridge]
    obj = mesh(name, verts, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], mat, bone, rig)
    return obj


def uv_map(obj):
    if obj.data.uv_layers: return
    uv = obj.data.uv_layers.new(name='ArtUV') if not obj.data.uv_layers else obj.data.uv_layers.active
    # Object-space planar projections; tree bark retains vertical grain.
    for face in obj.data.polygons:
        normal = face.normal
        axis = max(range(3), key=lambda i: abs(normal[i]))
        for loop_idx in face.loop_indices:
            p = obj.data.vertices[obj.data.loops[loop_idx].vertex_index].co
            pair = (p.y, p.z) if axis == 0 else ((p.x, p.z) if axis == 1 else (p.x, p.y))
            uv.data[loop_idx].uv = (pair[0] * 1.6, pair[1] * 1.6)


def join(parts, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts: obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object; obj.name = name
    return obj


def export(name, rig=None, separate=False, character=False):
    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in parts: uv_map(obj)
    source_count = len(parts)
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC / (name + '.blend')))
    if not separate: join(parts, name + ('Skin' if rig else 'Mesh'))
    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in parts: obj.data.calc_loop_triangles()
    info = {'triangles': sum(len(o.data.loop_triangles) for o in parts),
            'surfaces': sum(len(set(p.material_index for p in o.data.polygons)) for o in parts),
            'runtime_meshes': len(parts), 'skinned_meshes': sum(bool(o.modifiers.get('Skin')) for o in parts),
            'editable_meshes': source_count}
    dest = base.EXPORT if character else OUT
    bpy.ops.export_scene.gltf(filepath=str(dest / (name + '.glb')), export_format='GLB', export_yup=True,
                             export_skins=True, export_animations=bool(rig), export_animation_mode='NLA_TRACKS',
                             export_force_sampling=True, export_apply=False, export_extras=True)
    REPORT[name] = info
    if rig:
        info['bones'] = [b.name for b in rig.data.bones]
        info['clips'] = {track.name: (track.strips[0].action_frame_end - track.strips[0].action_frame_start) / 60 for track in rig.animation_data.nla_tracks}
        info['meshes'] = len(parts)
        mf = base.EXPORT / 'manifest.json'
        manifest = json.loads(mf.read_text())
        manifest['assets'][name] = info
        mf.write_text(json.dumps(manifest, indent=2) + '\n')
    print('BENCHMARK_ASSET', name, json.dumps(info))


def tree(variant):
    base.reset(); random.seed(330 + variant)
    bark = material('GroveBark', (.34, .29, .20), 'bark')
    foliage = material('GroveLeaves', (.30, .43, .16), 'leaf', rough=.91)
    foliage.use_backface_culling = False
    h = [6.6, 7.8, 6.3][variant]
    bend = [-1.6, 1.0, .5][variant]
    centers = [(0, 0, 0), (.1, -.1, .65), (.05, .05, 2.1), (bend * .3, .1, 3.2), (bend * .65, .12, 4.5), (bend, .3, h - .5)]
    branch('ButtressedTrunk', centers, [.65, .46, .37, .30, .20, .045], bark, sides=14, seed=variant)
    for i in range(6):
        a = i * math.tau / 6
        branch('RootFlare', [(math.cos(a) * 1.7, math.sin(a) * 1.7, .02), (math.cos(a) * .75, math.sin(a) * .75, .2), (0, 0, 1.1)], [.025, .24, .22], bark, sides=8)
    endpoints = []
    for i in range(11):
        a = i * 2.39996 + variant
        z = 2.6 + i * .25
        start = Vector((bend * max(0, z - 2) / h, .05, z))
        spread = 2.6 if variant != 1 else 2.1
        end = Vector((math.cos(a) * spread + bend * .65, math.sin(a) * spread, min(h, z + 1.7)))
        elbow = start.lerp(end, .55) - Vector((0, 0, .4))
        branch('Limb', [start, elbow, end], [.21 - i * .010, .10, .024], bark, sides=9, seed=i)
        for j in range(3):
            direction = Vector((math.cos(a + (j - 1) * .9), math.sin(a + (j - 1) * .9), .55))
            tip = end + direction * random.uniform(.8, 1.55)
            branch('Twig', [elbow.lerp(end, .5), end, tip], [.057, .035, .005], bark, sides=6)
            endpoints.append(tip)
    # Actual folded leaf polygons, arranged along arching terminal sprays.
    for tip in endpoints:
        for spray in range(7):
            a = random.random() * math.tau
            root = tip + Vector((random.uniform(-.8, .8), random.uniform(-.8, .8), random.uniform(-.4, .6)))
            for k in range(7):
                p = root + Vector((math.cos(a), math.sin(a), -.15)) * k * .16
                for sign in (-1, 1):
                    la = a + sign * 1.1
                    length = random.uniform(.38, .60)
                    leaf('CanopyLeaf', p, p + Vector((math.cos(la) * length, math.sin(la) * length, random.uniform(-.20, .12))), length * .39, foliage)
    export(['tree_bent', 'tree_fork', 'tree_wide'][variant])


def rock(variant):
    base.reset(); random.seed(981 + variant)
    stone = material('BlueSlate', (.40, .46, .43), 'stone', rough=.93)
    moss = material('SlateLichen', (.33, .40, .19), 'stone', rough=.98)
    for k in range(3 if variant == 1 else 2):
        cx, cy = (k - .7) * .9, random.uniform(-.4, .4)
        count = 9
        angles = [i * math.tau / count + random.uniform(-.08, .08) for i in range(count)]
        rad = [random.uniform(.8, 1.25) for _ in range(count)]
        verts = []
        for level, width, z in [(0, 1, -.12), (1, 1.05, .42), (2, .75, 1.3 + variant * .18), (3, .4, 1.65 + variant * .2)]:
            for i, a in enumerate(angles):
                verts.append((cx + math.cos(a) * rad[i] * width + level * .14, cy + math.sin(a) * rad[i] * width * .8, z + random.uniform(-.13, .13)))
        faces = []
        for j in range(3):
            for i in range(count): faces.append((j * count + i, j * count + (i + 1) % count, (j + 1) * count + (i + 1) % count, (j + 1) * count + i))
        faces += [tuple(range(3 * count, 4 * count)), tuple(reversed(range(count)))]
        obj = mesh('SplitSlate', verts, faces, stone, smooth=False)
        obj.data.materials.append(moss)
        for p in obj.data.polygons:
            if p.normal.z > .6 and random.random() < .65: p.material_index = 1
        bevel = obj.modifiers.new('WornEdges', 'BEVEL'); bevel.width = .055; bevel.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    export('rock_' + str(variant))


def undergrowth(kind):
    base.reset(); random.seed(400 + kind)
    leaves = material('UnderstoryLeaves', (.36, .47, .18) if kind != 3 else (.45, .43, .20), 'leaf')
    leaves.use_backface_culling = False
    wood = material('UnderstoryWood', (.30, .24, .14))
    if kind in (0, 1):
        for i in range(12 if kind == 0 else 8):
            a = i * 2.4; h = random.uniform(.55, 1.15) if kind == 0 else random.uniform(.25, .6)
            end = Vector((math.cos(a) * .65, math.sin(a) * .65, h))
            branch('ShrubStem', [(0, 0, 0), end * .6, end], [.035, .02, .003], wood, sides=5)
            for j in range(2, 8):
                p = end * j / 8
                for sign in (-1, 1):
                    d = Vector((math.cos(a + sign * 1.0), math.sin(a + sign * 1.0), .35))
                    leaf('ShrubLeaf', p, p + d * .35, .10, leaves)
    elif kind == 2:
        for i in range(9):
            a = i * math.tau / 9
            for j in range(1, 10):
                t = j / 10
                p = Vector((math.cos(a) * t * .86, math.sin(a) * t * .86, math.sin(t * math.pi * .85) * .50))
                for sign in (-1, 1):
                    d = Vector((math.cos(a + sign * 1.05), math.sin(a + sign * 1.05), -.08))
                    leaf('FernPinna', p, p + d * (1 - t) * .35, (1 - t) * .068, leaves)
    else:
        for i in range(23):
            a = i * 2.4; length = random.uniform(.22, .56)
            p = Vector((random.uniform(-.22, .22), random.uniform(-.22, .22), 0))
            leaf('SedgeBlade', p, p + Vector((math.cos(a) * .21, math.sin(a) * .21, length)), .025, leaves)
    export(['shrub_laurel', 'shrub_briar', 'fern', 'sedge'][kind])


def deadwood():
    base.reset()
    bark = material('Deadwood', (.32, .27, .19))
    branch('FallenSplitTrunk', [(-2.1, 0, .25), (-1.2, .12, .37), (0, 0, .45), (1.6, -.25, .42), (2.2, -.36, .36)], [.28, .43, .46, .34, .12], bark, sides=13)
    for sign in (-1, 1):
        branch('SnappedBranch', [(sign * .7, 0, .42), (sign * 1.1, sign * .65, .60), (sign * 1.25, sign * .9, .78)], [.15, .08, .015], bark)
    export('fallen_wood')


def litter():
    base.reset()
    ochre=material('FallenLeaf', (.44,.28,.09), 'leaf', rough=.96)
    ochre.use_backface_culling=False
    for k in range(3):
        c=Vector(((k-1)*.16,(k%2)*.15,.015+k*.007))
        verts=[c+Vector((0,0,.035))]
        for i in range(16):
            a=i*math.tau/16
            r=1 if i%2==0 else .64
            verts.append(c+Vector((math.cos(a)*.12*r,math.sin(a)*.23*r,.017*math.sin(a*3))))
        mesh('CurledOakLeaf',verts,[(0,i+1,(i+1)%16+1) for i in range(16)],ochre)
    export('leaf_litter')


def fracture():
    base.reset(); random.seed(778)
    bark = material('FractureBark', (.30, .31, .22))
    inside = material('FractureSplinter', (.52, .38, .20))
    core = material('WakeAmber', (.95, .29, .025), 'stone', rough=.23, emission=.35)
    for i in range(7):
        a = i * math.tau / 7 + .18
        height = [3.8, 4.7, 4.2, 3.6, 4.5, 3.9, 3.3][i]
        # Each rib is an individual damage/collapse unit, with a torn double tip.
        before = set(bpy.context.scene.objects)
        r = Vector((math.cos(a), math.sin(a), 0))
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        points = [r * 2.7 + Vector((0, 0, .04)), r * 1.45 + Vector((0, 0, .25)), r * 1.12 + Vector((0, 0, 1.0)), r * 1.42 + tangent * .12 + Vector((0, 0, 2.2)), r * 1.04 + tangent * .30 + Vector((0, 0, height - .4)), r * .62 + tangent * .45 + Vector((0, 0, height))]
        branch('RibMain', points, [.045, .40, .38, .27, .16, .015], bark, sides=12, seed=i)
        branch('TornEdge', [points[2] + tangent * .19, points[3] + tangent * .23, points[4] + tangent * .29], [.13, .095, .003], inside, sides=7)
        branch('RootBranch', [r * 1.2 + Vector((0, 0, .32)), r * 2.2 + tangent * .6 + Vector((0, 0, .12)), r * 3.3 + tangent * 1.1 + Vector((0, 0, .025))], [.22, .12, .005], bark, sides=8)
        for j in range(3):
            p = points[2].lerp(points[4], j / 3)
            branch('Scar', [p, p + tangent * .12 + Vector((0, 0, .32)), p + tangent * .10 + Vector((0, 0, .62))], [.08, .055, .008], inside, sides=5)
        join([o for o in bpy.context.scene.objects if o not in before], 'Rib_%d' % i)
    # Three offset slivers form a split heart with dark gaps, rather than a glowing ball.
    for i in range(3):
        a = i * math.tau / 3
        c = Vector((math.cos(a) * .28, math.sin(a) * .28, 2.0 + (i - 1) * .23))
        verts = [c + Vector((-.25, -.21, -.65)), c + Vector((.24, -.17, -.53)), c + Vector((.34, .16, -.15)), c + Vector((.08, .25, .91)), c + Vector((-.28, .08, .48)), c + Vector((-.05, -.25, .28)), c + Vector((0, 0, .03))]
        mesh('Core_%d' % i, verts, [(0, 1, 6), (1, 2, 6), (2, 3, 6), (3, 4, 6), (4, 0, 6), (0, 4, 5), (4, 3, 5), (3, 2, 5), (2, 1, 5), (1, 0, 5)], core, smooth=False)
    export('briarwake', separate=True)


def mossling():
    base.reset(); rig = base.armature(True)
    bark = material('MosslingBark', (.42, .38, .22), 'hide')
    moss = material('MosslingMoss', (.30, .43, .13), 'leaf')
    horn = material('MosslingFungus', (.71, .56, .32), 'bark')
    eye = material('MosslingEyes', (.95, .43, .065), 'stone', rough=.36, emission=.25)
    dark = material('MosslingCrevices', (.09, .12, .075), 'hide')
    centers = [(0, 0, .50), (0, -.035, .66), (0, -.08, .89), (0, -.045, 1.08), (0, .04, 1.22)]
    obj = base.tube('RootTorso', centers, [(.22, .17), (.29, .21), (.39, .26), (.38, .23), (.24, .18)], bark,
                    [{'Hips':1}, {'Hips':.7, 'Spine':.3}, {'Spine':.6, 'Chest':.4}, {'Chest':1}, {'Chest':1}], rig, 16)
    # Asymmetric bark plates follow the torso instead of floating over spheres.
    for sign in (-1, 1):
        for j in range(4):
            branch('TorsoFluting', [(sign * (.14 + j * .048), .13, .6), (sign * (.16 + j * .059), .19, .9), (sign * (.12 + j * .07), .1, 1.16)], [.035, .055, .018], moss if j == 3 else bark, 'Chest', rig, 7)
    for side, sign in [('R', 1), ('L', -1)]:
        base.limb(rig, side, 'UpperArm', 'Forearm', bark, .155 if side == 'R' else .125)
        base.limb(rig, side, 'Thigh', 'Shin', bark, .14)
        hand = rig.data.bones['Hand.' + side].head_local
        branch('RootPalm', [hand, hand + Vector((0, .03, -.07)), hand + Vector((0, .09, -.14))], [.10, .13, .07], bark, 'Hand.' + side, rig, 9)
        for k in range(3):
            p = hand + Vector(((k - 1) * .075, .05, -.07))
            branch('GraspingClaw', [p, p + Vector((sign * .02, .14, -.10)), p + Vector((sign * .04, .26, -.12)), p + Vector((sign * .025, .30, -.03))], [.04, .032, .019, .002], horn, 'Hand.' + side, rig, 7)
        # One continuous foot mesh, toe spread authored into the ring silhouette.
        x = sign * .25
        branch('Body_Boot_' + side, [(x, -.08, .09), (x, .07, .085), (x, .20, .06), (x, .29, .04)], [(.075, .075), (.125, .08), (.12, .04), (.045, .023)], bark, 'Foot.' + side, rig, 10)
    # Thick split bark mask: sloping crown, angular jaw and forward brow.
    branch('BarkHead', [(0, .18, 1.15), (0, .22, 1.27), (0, .19, 1.46), (0, .10, 1.56)], [(.13, .11), (.23, .19), (.27, .19), (.12, .10)], bark, 'Head', rig, 14)
    for sign in (-1, 1):
        # Almond eyes with a carved dark surround and heavy angled eyebrow.
        for width, mat, depth in [(.102, dark, .377), (.055, eye, .389)]:
            c = Vector((sign * .10, depth, 1.40))
            mesh('EyeSocket', [c + Vector((-width, 0, 0)), c + Vector((0, -.012, .038)), c + Vector((width, 0, .015)), c + Vector((0, .014, -.023))], [(0,1,3),(1,2,3)], mat, 'Head', rig)
        branch('HeavyBrow', [(sign * .025, .40, 1.46), (sign * .13, .385, 1.48), (sign * .25, .31, 1.43)], [.034, .057, .035], bark, 'Head', rig, 7)
        branch('RootAntler', [(sign * .19, .05, 1.49), (sign * .30, -.035, 1.69), (sign * .42, .02, 1.78), (sign * .47, .13, 1.86 if sign == 1 else 1.72)], [.09, .063, .033, .003], bark, 'Head', rig, 8)
        branch('AntlerFork', [(sign * .29, -.025, 1.66), (sign * .27, -.13, 1.8), (sign * .23, -.12, 1.9)], [.041, .023, .002], horn, 'Head', rig, 6)
    branch('NoseRidge', [(0, .36, 1.46), (0, .425, 1.35), (0, .40, 1.29)], [.027, .055, .025], horn, 'Head', rig, 6)
    branch('MouthFissure', [(-.13, .35, 1.27), (0, .405, 1.25), (.12, .35, 1.285)], [.009, .013, .006], dark, 'Head', rig, 6)
    # Shelf fungus on one shoulder, leafy mantle on the other; clear attack arms.
    for i in range(5):
        cx, cy, z = -.24 - .027 * i, -.18, 1.1 + .07 * i
        verts = [(cx, cy, z)]
        for j in range(9):
            a = j * math.pi / 8
            verts.append((cx - math.sin(a) * (.24 - i * .018), cy - math.cos(a) * .21, z - .04 + .045 * math.sin(a)))
        mesh('ShelfFungus', verts, [(0, j + 1, j + 2) for j in range(8)], horn, 'Chest', rig)
    for i in range(28):
        a = i * 2.4; p = Vector((.2 + math.cos(a) * .16, -.14 + math.sin(a) * .14, 1.12 + (i % 4) * .055))
        leaf('MossMantle', p, p + Vector((math.cos(a) * .24, math.sin(a) * .27, -.13)), .085, moss, 'Chest', rig)
    base.animations(rig, True)
    export('briarling', rig, character=True)


def hero():
    rig = tw.build_character()
    # Keep V2's proportions, authored face, torso and entire existing rig/animations.
    mats = {m.name: m for m in bpy.data.materials}
    steel = material('WardenSteel', (.49, .57, .59), 'metal', .72, .36)
    darksteel = material('WardenBlackenedSteel', (.19, .25, .27), 'metal', .6, .48)
    brass = material('WardenBrass', (.61, .40, .16), 'metal', .62, .43)
    cloth = material('WardenOxblood', (.34, .055, .038), 'cloth', rough=.93)
    leather = material('WardenLeather', (.18, .09, .043), 'leather', rough=.8)
    replace = {'TW_Steel':steel, 'TW_DarkSteel':darksteel, 'TW_Brass':brass, 'TW_Cloth':cloth, 'TW_Leather':leather}
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH': continue
        for slot in obj.material_slots:
            if slot.material.name in replace: slot.material = replace[slot.material.name]
        if any(token in obj.name for token in ['Pauldron', 'CoatTail', 'BackMantle', 'Body_Boot']): bpy.data.objects.remove(obj, do_unlink=True)
    for side, sign in [('R', 1), ('L', -1)]:
        shoulder = rig.data.bones['UpperArm.' + side].head_local
        for layer in range(3):
            # Forged shoulder shell with a raised spine, bevel and descending lames.
            sx = .19 if side == 'R' else .15
            c = shoulder + Vector((sign * (.025 + layer * .035), -.006, .055 - layer * .052))
            verts = [c + Vector((sign * x, y, z)) for x,y,z in [(-.11,-.115,0),(.08,-.155,-.02),(sx,-.10,-.08),(sx,.085,-.08),(.08,.135,-.015),(-.11,.095,0),(.045,-.015,.065)]]
            obj = mesh('ForgedShoulder', verts, [(i,(i+1)%6,6) for i in range(6)], steel if layer == 0 else darksteel, 'UpperArm.' + side, rig, smooth=False)
            solid = obj.modifiers.new('PlateThickness', 'SOLIDIFY'); solid.thickness = .018
            bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier=solid.name)
            branch('ShoulderRim', [verts[1],verts[2],verts[3],verts[4]], [.013]*4, brass, 'UpperArm.' + side, rig, 6)
        # Square toe box with bevel, heel, instep and calf transition.
        x = sign * .14
        branch('Body_Boot_' + side, [(x,-.09,.08),(x,.015,.105),(x,.15,.07),(x,.265,.055)], [(.069,.06),(.078,.098),(.086,.062),(.07,.035)], leather, 'Foot.' + side, rig, 8)
        # Flat hanging cloth panels, with ridges/folds and irregular weighted hem.
        verts=[]; weights=[]
        for row,z in enumerate([1.02,.86,.66]):
            for j in range(5):
                verts.append((sign * (.025+j*.054), -.13 - .025*math.cos(j*math.pi) - row*.013, z - (.025 if row==2 and j%2 else 0)))
                weights.append({'Hips':1-row*.24, 'Thigh.'+side:row*.24})
        obj = base.mesh_object('SplitCoat', verts, [(r*5+j,r*5+j+1,(r+1)*5+j+1,(r+1)*5+j) for r in range(2) for j in range(4)], cloth, weights, rig)
        obj.data.materials[0].use_backface_culling = False
    # Back cuirass follows the torso and provides a highlight at normal rear camera.
    tw.wedge('BackCuirass', (0,-.118,1.30), (.207,.032,.146), darksteel,'Chest',rig,flare=-.032)
    for sign in (-1,1):
        branch('BackHarness', [(sign*.18,-.15,1.43),(sign*.08,-.17,1.28),(sign*.13,-.145,1.13)], [.022,.022,.022], leather,'Chest',rig,6)
    tw.diamond_plate('BackOathSeal',(0,-.175,1.35),.037,.068,.012,brass,'Chest',rig)
    export('turnwarden_v2', rig, character=True)
    tw.build_sword()
    sword_mats = {}
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for vertex in obj.data.vertices:
                if vertex.co.y>0: vertex.co.y*=1.08/1.3
            for slot in obj.material_slots:
                name=slot.material.name
                color=tuple(slot.material.diffuse_color[:3])
                if name not in sword_mats:
                    sword_mats[name]=material(name+'_Forged',color,'metal' if 'Grip' not in name else 'leather', .7 if 'Grip' not in name else 0, .32 if 'Grip' not in name else .82)
                slot.material=sword_mats[name]
    export('turnwarden_v2_sword', character=True)


def armor():
    base.reset()
    leather = material('GuardHarness', (.24,.12,.055), 'leather', rough=.82)
    brass = material('GuardSeal', (.58,.38,.14), 'metal', .6,.43)
    # Socket-local chest reinforcement, shaped straps follow the V2 cuirass.
    for sign in (-1,1):
        branch('VestStrap', [(sign*.16,.14,.075),(sign*.15,.155,-.035),(sign*.10,.14,-.13)], [.022,.026,.022], leather, sides=6)
    verts=[(-.036,.178,.008),(0,.195,.055),(.036,.178,.008),(0,.198,-.065),(0,.218,.006)]
    mesh('OathSeal',verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],brass,smooth=False)
    export('traveler_guard', character=True)


if __name__ == '__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    chosen=args[0] if args else 'all'
    if chosen not in ('all','forest','briarwake','briarling','turnwarden_v2'):
        raise ValueError('Unknown benchmark asset group: '+chosen)
    if chosen in ('all','forest'):
        for i in range(3): tree(i)
        for i in range(3): rock(i)
        for i in range(4): undergrowth(i)
        deadwood()
        litter()
    if chosen in ('all','briarwake'): fracture()
    if chosen in ('all','briarling'): mossling()
    if chosen in ('all','turnwarden_v2'): hero(); armor()
    (OUT/'manifest.json').write_text(json.dumps(REPORT, indent=2)+'\n')
    print('AMBER SCAR BUILD COMPLETE')
