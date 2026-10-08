import html
import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageFilter
from pydantic import BaseModel, Field

from . import config
from .backends import BACKENDS
from .jobs import JobManager
from .hardware import inventory
from .store import Store, digest, now

PRESETS = json.loads((config.ROOT/"config/presets.json").read_text(encoding="utf-8"))
store = Store(config.DATA)
manager = JobManager(store)
app = FastAPI(title="Ironfield Asset Forge",version="0.1.0")


@app.middleware("http")
async def local_only(request: Request, call_next):
    from starlette.responses import JSONResponse
    # Loopback application; reject browser cross-origin writes and DNS rebinding.
    if request.url.hostname not in ("localhost","127.0.0.1","testserver"):
        return JSONResponse({"detail":"This application is restricted to localhost"},status_code=403)
    if request.method not in ("GET","HEAD","OPTIONS"):
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != request.headers.get("host"):
            return JSONResponse({"detail":"Cross-origin writes are forbidden"},status_code=403)
        if request.headers.get("x-forge-request") != "1":
            return JSONResponse({"detail":"Missing application request header"},status_code=403)
    return await call_next(request)


@app.exception_handler(ValueError)
async def value_error(request, exc):
    from starlette.responses import JSONResponse
    return JSONResponse({"detail":str(exc)},status_code=400)


@app.exception_handler(FileNotFoundError)
async def missing(request, exc):
    from starlette.responses import JSONResponse
    return JSONResponse({"detail":"Asset or file not found"},status_code=404)


class AssetInput(BaseModel):
    name: str = Field(min_length=1,max_length=120)
    preset: str = "equipment"
    design_requirements: str = Field(default="",max_length=10000)
    license: str = Field(default="User supplied; rights unverified",max_length=2000)


class Settings(BaseModel):
    generation_seed: int = Field(default=42,ge=0,le=4294967295)
    diffusion_steps: int = Field(default=50,ge=10,le=100)
    guidance_scale: float = Field(default=7.0,ge=1,le=20)
    shape_octree_depth: int = Field(default=9,ge=7,le=9)
    triangle_budget: int = Field(default=16000,ge=100,le=2000000)
    texture_resolution: int = 2048
    collision: str = "none"
    generate_lods: bool = False
    lod_ratios: list[float] = Field(default_factory=lambda:[0.65,0.35],max_length=3)
    repair_degenerate: bool = False
    recalculate_normals: bool = False
    render_preview: bool = True
    mc_resolution: int = 256
    front_axis: str = "-Z"
    source_rotation_degrees: list[float] = Field(default_factory=lambda:[0,0,0],min_length=3,max_length=3)
    export_formats: list[str] = Field(default_factory=lambda:["glb"],max_length=2)
    separate_effects: bool = False
    bypass_rigging: bool = False
    attachment: dict | None = None
    material_variant: dict | None = None
    equipment_asset: str | None = None
    weapon_attachment: dict = Field(default_factory=lambda:{"bone":"Hand.R","position":[0,0,0],"rotation_degrees":[0,0,0]})
    stages: list[str] = Field(default_factory=list,max_length=25)


def validate_settings(settings):
    if settings.front_axis not in ("-Z","+Z") or any(abs(v)>360 for v in settings.source_rotation_degrees):
        raise ValueError("Front axis must be -Z or +Z; source rotation is measured in degrees")
    if settings.texture_resolution not in (1024,2048,4096):
        raise ValueError("Texture resolution must be 1024, 2048 or 4096")
    if settings.mc_resolution not in (128,256,384):
        raise ValueError("Isosurface resolution must be 128, 256 or 384")
    if settings.collision not in ("none","convex") or any(not 0.05<=v<1 for v in settings.lod_ratios):
        raise ValueError("Invalid collision or LOD settings")
    if not settings.export_formats or any(f not in ("glb","gltf") for f in settings.export_formats):
        raise ValueError("Export formats: GLB and glTF")
    for attachment in (settings.attachment, settings.weapon_attachment):
        if attachment:
            for key in ("location","position","rotation_degrees"):
                value = attachment.get(key)
                if value is not None and (not isinstance(value,list) or len(value)!=3 or any(not isinstance(v,(int,float)) or abs(v)>10000 for v in value)):
                    raise ValueError("Attachment coordinates must be three finite numbers")
    if settings.equipment_asset:
        store.get(settings.equipment_asset)
    return settings.model_dump()


def busy(asset_id):
    if any(j["asset_id"]==asset_id and j["state"] in ("queued","running") for j in store.jobs()):
        raise ValueError("Wait for or cancel this asset's active job before editing inputs")


@app.get("/api/system")
def system():
    return {"blender":config.BLENDER,"godot":config.GODOT,"presets":PRESETS,"backends":[b.capabilities() for b in BACKENDS.values()],
            "paid_generation_enabled":False,"local_workers":1,"data_directory":str(config.DATA),
            "hardware":inventory()}


@app.get("/api/assets")
def assets():
    return store.all_assets()


@app.post("/api/assets")
def create_asset(body:AssetInput):
    if body.preset not in PRESETS:
        raise ValueError("Unknown preset")
    preset = PRESETS[body.preset]
    settings = Settings(**{k:v for k,v in preset.items() if k in Settings.model_fields}).model_dump()
    return store.create(body.name,body.preset,settings,body.design_requirements,body.license)


@app.get("/api/assets/{asset_id}")
def asset(asset_id:str):
    return store.get(asset_id)


@app.put("/api/assets/{asset_id}/settings")
def settings(asset_id:str,body:Settings):
    busy(asset_id)
    value = validate_settings(body)
    def mutate(a):
        a["settings"] = value
        a["review"]["status"] = "pending"
        a["artifacts"]["stale"] = True
    return store.update(asset_id,mutate)


class DesignInput(BaseModel):
    design_requirements: str = Field(max_length=10000)
    unseen_surfaces: str = Field(max_length=5000)
    license: str = Field(max_length=2000)


@app.put("/api/assets/{asset_id}/design")
def design(asset_id:str,body:DesignInput):
    busy(asset_id)
    def mutate(a):
        a["design_requirements"] = body.design_requirements
        a["unseen_surfaces"] = body.unseen_surfaces
        a["provenance"]["license"] = body.license
        a["review"]["status"] = "pending"
    return store.update(asset_id,mutate)


async def save_upload(asset_id,file,folder,allowed):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in allowed:
        raise ValueError("Unsupported file type: "+extension)
    relative = f"{folder}/{uuid.uuid4().hex[:12]}{extension}"
    path = store.file(asset_id,relative)
    path.parent.mkdir(exist_ok=True)
    count = 0
    try:
        with path.open("wb") as f:
            while chunk:= await file.read(1024*1024):
                count += len(chunk)
                if count>config.MAX_UPLOAD:
                    raise ValueError("Upload exceeds 250 MB")
                f.write(chunk)
        if not count:
            raise ValueError("Empty upload")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return relative,path


@app.post("/api/assets/{asset_id}/references")
async def add_reference(asset_id:str,file:UploadFile=File(...),role:str=Form("primary")):
    busy(asset_id)
    if role not in ("primary","additional","turnaround_pending"):
        raise ValueError("Invalid reference role")
    relative,path = await save_upload(asset_id,file,"references",(".png",".jpg",".jpeg"))
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        record = {"id":uuid.uuid4().hex[:12],"path":relative,"original_filename":file.filename,"resolution":list(im.size),
                  "role":role,"sha256":digest(path),"original":True,"created_at":now(),"consistency_review":"pending" if role=="turnaround_pending" else "user_supplied"}
    store.update(asset_id,lambda a:a["references"].append(record))
    return record


class PrepareInput(BaseModel):
    reference_id: str
    crop: list[int] | None = Field(default=None,min_length=4,max_length=4)
    remove_background: bool = False
    background_color: str = "#d5c4a8"
    tolerance: int = Field(default=38,ge=0,le=120)
    role: str = "primary"


@app.post("/api/assets/{asset_id}/prepare")
def prepare(asset_id:str,body:PrepareInput):
    busy(asset_id)
    a = store.get(asset_id)
    record = next((r for r in a["references"] if r["id"]==body.reference_id),None)
    if not record:
        raise ValueError("Reference does not exist")
    if body.role not in ("primary","additional","turnaround_pending"):
        raise ValueError("Invalid reference role")
    im = Image.open(store.file(asset_id,record["path"])).convert("RGBA")
    if record.get("consistency_review")=="pending" and body.role=="primary":
        raise ValueError("Review turnaround consistency before promoting it to a primary reference")
    if body.crop:
        x,y,w,h = body.crop
        if x<0 or y<0 or w<=0 or h<=0 or x+w>im.width or y+h>im.height:
            raise ValueError("Crop must be inside original image bounds")
        im = im.crop((x,y,x+w,y+h))
    if body.remove_background:
        import numpy as np
        if not re.fullmatch(r"#[0-9a-fA-F]{6}",body.background_color):
            raise ValueError("Expected a hex background color")
        rgb = np.array([int(body.background_color[i:i+2],16) for i in (1,3,5)])
        pixels = np.asarray(im).copy()
        distance = np.max(np.abs(pixels[:,:,:3].astype(int)-rgb),axis=2)
        alpha = np.clip((distance-body.tolerance)/8.0,0,1)*255
        pixels[:,:,3] = np.minimum(pixels[:,:,3],alpha.astype("uint8"))
        im = Image.fromarray(pixels)
    relative = f"references/{uuid.uuid4().hex[:12]}_prepared.png"
    im.save(store.file(asset_id,relative))
    new = {"id":uuid.uuid4().hex[:12],"path":relative,"parent_id":record["id"],"original":False,"role":body.role,
           "resolution":list(im.size),"sha256":digest(store.file(asset_id,relative)),"preparation":body.model_dump(),
           "mask_review":"pending" if body.remove_background else "not_applicable","created_at":now()}
    if record.get("consistency_review"):
        new["consistency_review"]=record["consistency_review"]
    store.update(asset_id,lambda a:a["references"].append(new))
    return new


class ReferenceReviewInput(BaseModel):
    consistency_approved: bool
    notes: str = Field(min_length=1,max_length=3000)


@app.put("/api/assets/{asset_id}/references/{reference_id}/review")
def review_reference(asset_id:str,reference_id:str,body:ReferenceReviewInput):
    busy(asset_id)
    def mutate(a):
        record=next((r for r in a["references"] if r["id"]==reference_id),None)
        if not record:
            raise ValueError("Reference not found")
        record["consistency_review"]="approved" if body.consistency_approved else "rejected"
        record["consistency_notes"]=body.notes
        record["reviewed_at"]=now()
    return store.update(asset_id,mutate)


@app.post("/api/assets/{asset_id}/import")
async def import_mesh(asset_id:str,file:UploadFile=File(...),license_note:str=Form("User supplied imported mesh; rights unverified")):
    busy(asset_id)
    relative,path = await save_upload(asset_id,file,"imports",(".glb",".blend",".fbx",".obj"))
    return store.candidate(asset_id,relative,"imported",{"original_filename":file.filename,"license":license_note,"cost_credits":0})


class Selection(BaseModel):
    candidate_id: str


@app.post("/api/assets/{asset_id}/select")
def select(asset_id:str,body:Selection):
    busy(asset_id)
    def mutate(a):
        if not any(c["id"]==body.candidate_id for c in a["candidates"]):
            raise ValueError("Candidate not found")
        a["selected_candidate"] = body.candidate_id
        a["artifacts"] = {}
        a["review"]["status"] = "pending"
    return store.update(asset_id,mutate)


class JobInput(BaseModel):
    operation: str
    options: dict = Field(default_factory=dict)
    reason: str = Field(default="",max_length=2000)


@app.post("/api/assets/{asset_id}/jobs")
def job(asset_id:str,body:JobInput):
    if not 1<=body.options.get("instances",25)<=100:
        raise ValueError("Performance test supports 1–100 instances")
    return manager.submit(asset_id,body.operation,body.options,body.reason)


@app.get("/api/jobs")
def jobs():
    return store.jobs()


@app.post("/api/jobs/{job_id}/cancel")
def cancel(job_id:str):
    return manager.cancel(job_id)


@app.post("/api/jobs/{job_id}/resume")
def resume(job_id:str):
    job = store.get_job(job_id)
    return manager.submit(job["asset_id"],job["operation"],job["options"],job["reason"],resume_id=job_id)


class ReviewInput(BaseModel):
    status: str = "pending"
    notes: str = Field(default="",max_length=15000)
    defects: list[dict] = Field(default_factory=list,max_length=100)
    checklist: dict[str,bool] = Field(default_factory=dict)
    override_reason: str = Field(default="",max_length=3000)


def review_checks(asset):
    checks = ["reference_fidelity","silhouette","surface_materials","separate_parts","gameplay_distance"]
    if asset["preset"] in ("humanoid","creature"):
        checks += ["anatomy","face_hands","armor_cloth_clipping"]
        if not asset["settings"].get("bypass_rigging"):
            checks += ["rig_integrity","joint_deformation","weapon_alignment","foot_sliding","idle_walk_run_melee"]
    if asset["preset"]=="environment":
        checks += ["modularity","effects_separation"]
    return checks


@app.get("/api/assets/{asset_id}/review-checks")
def checks(asset_id:str):
    return review_checks(store.get(asset_id))


@app.put("/api/assets/{asset_id}/review")
def review(asset_id:str,body:ReviewInput):
    busy(asset_id)
    a = store.get(asset_id)
    if body.status not in ("pending","rejected","accepted"):
        raise ValueError("Invalid review status")
    if body.status=="accepted":
        if a["artifacts"].get("stale") or a["artifacts"].get("validation",{}).get("technical_status")!="passed":
            raise ValueError("Current technical checks must pass before acceptance")
        if any(not body.checklist.get(c,False) for c in review_checks(a)):
            raise ValueError("Complete the visual checklist before accepting")
        if any(not d.get("resolved",False) for d in body.defects) and not body.override_reason.strip():
            raise ValueError("Unresolved defects require a written human override")
    record = body.model_dump()
    record["accepted_at"] = now() if body.status=="accepted" else None
    record["candidate_id"] = a["selected_candidate"]
    record["runtime_sha256"] = a["artifacts"].get("runtime_sha256")
    return store.update(asset_id,lambda a:a.update(review=record))


@app.get("/api/assets/{asset_id}/files/{relative:path}")
def files(asset_id:str,relative:str):
    path = store.file(asset_id,relative)
    if not path.is_file():
        raise HTTPException(404,"File not found")
    return FileResponse(path)


@app.get("/api/assets/{asset_id}/export")
def export(asset_id:str):
    a = store.get(asset_id)
    if a["review"]["status"]!="accepted" or a["artifacts"].get("stale"):
        raise HTTPException(409,"Accept the current reviewed version before exporting the production bundle")
    if a["review"].get("runtime_sha256")!=a["artifacts"].get("runtime_sha256"):
        raise HTTPException(409,"Reviewed version differs from current export")
    runtime=a["artifacts"].get("files",{}).get("runtime.glb")
    if not runtime or digest(store.file(asset_id,runtime))!=a["review"].get("runtime_sha256"):
        raise HTTPException(409,"Runtime file changed after review; process and review it again")
    path = store.file(asset_id,"accepted_bundle.zip")
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.write(store.file(asset_id,"manifest.json"),"manifest.json")
        for name,relative in a["artifacts"].get("files",{}).items():
            if name.endswith((".glb",".gltf",".bin",".png",".blend",".json")):
                archive.write(store.file(asset_id,relative),"exports/"+name)
        for r in a["references"]:
            archive.write(store.file(asset_id,r["path"]),r["path"])
    return FileResponse(path,filename=re.sub(r"[^a-zA-Z0-9_-]","_",a["name"])+".zip")


def gallery_images():
    if not config.GALLERY.is_file():
        return []
    source = config.GALLERY.read_text(encoding="utf-8")
    paths = re.findall(r'<img[^>]+src="([^"]+)"',source)
    base = config.GALLERY.parent.resolve()
    return [p for p in paths if (base/p).resolve().is_relative_to(base) and (base/p).is_file()]


@app.get("/api/gallery")
def gallery():
    return [{"path":p,"name":Path(p).stem.replace("_"," "),"url":"/api/gallery/image/"+p} for p in gallery_images()]


@app.get("/api/gallery/image/{relative:path}")
def gallery_image(relative:str):
    if relative not in gallery_images():
        raise HTTPException(404,"Gallery image not found")
    return FileResponse(config.GALLERY.parent/relative)


class GalleryInput(BaseModel):
    path: str


@app.post("/api/assets/{asset_id}/gallery-reference")
def use_gallery(asset_id:str,body:GalleryInput):
    busy(asset_id)
    if body.path not in gallery_images():
        raise ValueError("Image not found in configured gallery")
    source = config.GALLERY.parent/body.path
    relative = f"references/{uuid.uuid4().hex[:12]}_{source.name}"
    target = store.file(asset_id,relative)
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(source,target)
    with Image.open(target) as im:
        record = {"id":uuid.uuid4().hex[:12],"path":relative,"original_filename":source.name,"resolution":list(im.size),"original":True,"role":"primary","source":str(source),"sha256":digest(target),"created_at":now()}
    store.update(asset_id,lambda a:a["references"].append(record))
    return record


app.mount("/static",StaticFiles(directory=config.ROOT/"web"),name="static")


@app.get("/")
def index():
    return FileResponse(config.ROOT/"web/index.html")
