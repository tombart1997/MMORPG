import bpy, json
for name in ['AnatomicalHead','Jade_SweptHair','Eye.R','Eye.L']:
    obj=bpy.data.objects.get(name)
    if obj:
        print('HERO_PART',name,'bounds',[(round(min(v.co[i] for v in obj.data.vertices),4),round(max(v.co[i] for v in obj.data.vertices),4)) for i in range(3)],'materials',[m.name for m in obj.data.materials],flush=True)
for mat in bpy.data.materials:
    if any(k in mat.name for k in ['Skin','Eye','Lip','Hair']):
        print('HERO_MATERIAL',mat.name,tuple(mat.diffuse_color),flush=True)
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type=='BSDF_PRINCIPLED': print('BASE_COLOR',list(node.inputs['Base Color'].default_value),'links',[(l.from_node.name,l.from_socket.name) for l in node.inputs['Base Color'].links],flush=True)
print('FACE_OBJECTS',[o.name for o in bpy.data.objects if any(k in o.name.lower() for k in ['eye','brow','lip','lash','head'])],flush=True)
