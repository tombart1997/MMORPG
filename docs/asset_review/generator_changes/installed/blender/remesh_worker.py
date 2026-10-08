"""Disposable, time-bounded QuadriFlow worker; no rig or materials are modified."""
import argparse
import ctypes
import json
import os
import threading
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector


def watch_parent(identity):
    # A cancelled Forge job terminates the parent Blender process. Keep a
    # handle to that specific process so its worker cannot outlive cancellation.
    if os.name != "nt":return
    from ctypes import wintypes
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    kernel.WaitForSingleObject.restype=wintypes.DWORD
    handle=kernel.OpenProcess(0x00100000,False,identity)
    if not handle:os._exit(2)
    while True:
        if kernel.WaitForSingleObject(handle,400)==0:os._exit(2)


def signature(mesh):
    return len(mesh.vertices),len(mesh.polygons),sum(len(f.vertices)==4 for f in mesh.polygons)


def main():
    import sys
    parser=argparse.ArgumentParser();parser.add_argument("--request",required=True)
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    request=json.loads(Path(args.request).read_text(encoding="utf-8"))
    if request.get("parent_pid"):
        threading.Thread(target=watch_parent,args=(request["parent_pid"],),daemon=True).start()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh=bpy.data.meshes.new("Remeshing input")
    mesh.from_pydata(request["vertices"],[],request["faces"])
    obj=bpy.data.objects.new("Remeshing input",mesh);bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    lo=Vector([min(v.co[i] for v in mesh.vertices) for i in range(3)])
    hi=Vector([max(v.co[i] for v in mesh.vertices) for i in range(3)])
    diagonal=max((hi-lo).length,1e-6)
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=max(diagonal*1e-6,1e-8))
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context="VERTS")
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();mesh.update()
    options=dict(use_mesh_symmetry=False,use_preserve_sharp=True,use_preserve_boundary=True,
                 preserve_attributes=False,smooth_normals=True,mode="FACES",
                 target_faces=max(8,int(request["target"]*.45)),seed=42)
    before=signature(obj.data)
    bpy.ops.object.quadriflow_remesh(**options)
    preparation="welded_seams_and_consistent_normals"
    if signature(obj.data)==before:
        obj.data.remesh_voxel_size=max(diagonal*.0025,1e-5)
        obj.data.use_remesh_fix_poles=True
        bpy.ops.object.voxel_remesh()
        preparation="voxel_volume_then_surface_projection"
        before=signature(obj.data)
        bpy.ops.object.quadriflow_remesh(**options)
        if signature(obj.data)==before:raise ValueError("QuadriFlow could not reconstruct this surface")
    result={"vertices":[list(v.co) for v in obj.data.vertices],
            "faces":[list(f.vertices) for f in obj.data.polygons],
            "remesh_input":preparation,"remeshed_quads":signature(obj.data)[2]}
    Path(request["output"]).write_text(json.dumps(result),encoding="utf-8")


if __name__=="__main__":main()
