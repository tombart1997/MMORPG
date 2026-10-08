import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from PIL import Image

from . import config
from .backends import BACKENDS
from .store import atomic_json, digest, now
from .validation import validate_glb
from .hardware import inventory


class Cancelled(Exception):
    pass


class Context:
    def __init__(self, manager, job):
        self.manager,self.job = manager,job
        self.cancel = manager.events[job["id"]]

    def update(self, **kwargs):
        self.job.update(kwargs)
        self.manager.store.save_job(self.job)

    def run_process(self, command, timeout, stage, cwd=None):
        self.update(stage=stage)
        log = self.manager.store.file(self.job["asset_id"], f"logs/{self.job['id']}.log")
        log.parent.mkdir(exist_ok=True)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        start = time.monotonic()
        with log.open("a",encoding="utf-8") as output:
            startup = None
            if os.name == "nt":
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,cwd=cwd,creationflags=flags,startupinfo=startup)
            try:
                while process.poll() is None:
                    if self.cancel.wait(0.4):
                        raise Cancelled("Job cancelled; completed checkpoints retained")
                    if time.monotonic()-start>timeout:
                        raise TimeoutError(f"{stage} exceeded {timeout} seconds; resume from the retained checkpoint")
                    # Keep elapsed progress honest for tools without a percent API.
                    self.update(elapsed_seconds=round(time.monotonic()-start,1),message=f"{stage} · {round(time.monotonic()-start)} seconds")
                if process.returncode:
                    tail = log.read_text(encoding="utf-8",errors="replace")[-1600:]
                    raise RuntimeError(f"{stage} failed (exit {process.returncode}). {tail}")
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        return log


class JobManager:
    def __init__(self, store, start=True):
        self.store = store
        self.queue = queue.Queue()
        self.events = {}
        self.thread = None
        for job in store.jobs():
            if job["state"] in ("queued","running"):
                job.update(state="interrupted",message="Application stopped. Resume this job from its saved checkpoint.")
                store.save_job(job)
        if start:
            self.thread = threading.Thread(target=self._worker,daemon=True,name="forge-worker")
            self.thread.start()

    def submit(self, asset_id, operation, options=None, reason="", resume_id=None):
        if operation not in ("generate","retexture","process","turntable","godot"):
            raise ValueError("Unknown stage")
        self.store.get(asset_id)
        with self.store.lock:
            if any(j["asset_id"] == asset_id and j["state"] in ("running","queued") for j in self.store.jobs()):
                raise ValueError("An active job already owns this asset")
            if operation == "generate":
                backend = (options or {}).get("backend","triposr")
                if backend == "meshy":
                    raise ValueError("Paid generation is disabled")
                if backend not in BACKENDS:
                    raise ValueError("Unknown generation backend")
                attempts = [j for j in self.store.jobs() if j["asset_id"]==asset_id and j["operation"]=="generate" and j.get("resumed_from") is None]
                if not resume_id and len(attempts)>=3:
                    raise ValueError("Three-candidate retry budget reached; create a new asset after reviewing the failures")
                if attempts and not resume_id and not reason.strip():
                    raise ValueError("Record a reason for regeneration")
            job = {"id":uuid.uuid4().hex[:12],"asset_id":asset_id,"operation":operation,"state":"queued",
                   "stage":"queued","progress":0,"created_at":now(),"reason":reason,"options":options or {},
                   "checkpoint":{},"resumed_from":resume_id,"message":"Waiting for worker","estimated_cost_credits":0}
            if resume_id:
                previous = self.store.get_job(resume_id)
                if previous["asset_id"] != asset_id or previous["state"] not in ("failed","interrupted","cancelled"):
                    raise ValueError("Job is not resumable")
                job["checkpoint"] = previous.get("checkpoint",{})
            # Freeze mutable input paths and settings at enqueue time.
            asset = self.store.get(asset_id)
            job["settings"] = dict(asset["settings"])
            job["candidate"] = self.store.selected(asset_id)
            job["reference"] = next((r for r in reversed(asset["references"]) if r.get("role") == "primary"),None)
            if resume_id:
                # Resume the exact inputs rather than silently regenerating with
                # newly edited settings or a different selected reference.
                for key in ("settings","candidate","reference"):
                    job[key] = previous.get(key,job[key])
            self.events[job["id"]] = threading.Event()
            self.store.save_job(job)
            self.queue.put(job["id"])
            return job

    def cancel(self, job_id):
        job = self.store.get_job(job_id)
        if job["state"] not in ("queued","running"):
            raise ValueError("Job is not active")
        self.events[job_id].set()
        return job

    def _worker(self):
        while True:
            job_id = self.queue.get()
            try:
                self.execute(job_id)
            finally:
                self.queue.task_done()

    def execute(self, job_id):
        job = self.store.get_job(job_id)
        ctx = Context(self,job)
        started = time.monotonic()
        try:
            if ctx.cancel.is_set():
                raise Cancelled("Cancelled before execution")
            ctx.update(state="running",started_at=now(),progress=5)
            getattr(self,"_"+job["operation"])(ctx)
            if ctx.cancel.is_set():
                raise Cancelled("Cancelled after checkpoint; output retained")
            ctx.update(state="succeeded",progress=100,finished_at=now(),message="Complete · visual review remains separate",duration_seconds=round(time.monotonic()-started,2))
        except Cancelled as exc:
            ctx.update(state="cancelled",message=str(exc),finished_at=now())
        except Exception as exc:
            ctx.update(state="failed",message=str(exc),finished_at=now())
        finally:
            self.store.update(job["asset_id"],lambda a:a["history"].append({"job_id":job_id,"operation":job["operation"],"state":job["state"],"reason":job["reason"],"timestamp":now()}))

    def _generate(self, ctx):
        job = ctx.job
        ref = job["reference"]
        if not ref:
            raise ValueError("Prepare a primary reference before generation")
        aid = job["asset_id"]
        origin_job = job.get("checkpoint",{}).get("generation_job",job["id"])
        out = self.store.file(aid,f"generated/{origin_job}")
        out.mkdir(parents=True,exist_ok=True)
        ctx.update(checkpoint={**job.get("checkpoint",{}),"generation_job":origin_job},progress=10)
        if job["checkpoint"].get("candidate_id"):
            return
        backend=job["options"].get("backend","triposr")
        source = BACKENDS[backend].generate(self.store.file(aid,ref["path"]),out,job["settings"],ctx)
        metadata = json.loads((out/"generation.json").read_text(encoding="utf-8"))
        metadata["backend"]=backend
        relative = source.relative_to(self.store.asset_dir(aid)).as_posix()
        c = self.store.candidate(aid,relative,"generated_local",metadata)
        ctx.update(checkpoint={"generation_job":origin_job,"candidate_id":c["id"],"source":relative},progress=95)

    def _process(self,ctx):
        self._blender(ctx,"process")

    def _retexture(self,ctx):
        job,aid=ctx.job,ctx.job["asset_id"]
        candidate=job["candidate"]
        if not candidate or candidate.get("origin")!="generated_local" or candidate.get("model")!="stabilityai/TripoSR":
            raise ValueError("Atlas rebaking needs a local TripoSR candidate with retained checkpoints")
        source=self.store.file(aid,candidate["path"]).parent
        required=("scene_code.pt","geometry.npz","foreground.png")
        if not all((source/name).exists() for name in required):
            raise ValueError("The local neural/geometry checkpoints are missing")
        out=self.store.file(aid,f"generated/{job['id']}")
        out.mkdir(parents=True,exist_ok=True)
        for name in required:
            shutil.copy2(source/name,out/name)
        reference=self.store.file(aid,job["reference"]["path"])
        path=BACKENDS["triposr"].generate(reference,out,job["settings"],ctx)
        metadata=json.loads((out/"generation.json").read_text(encoding="utf-8"))
        metadata.update(parent_candidate=candidate["id"],operation="atlas_rebake",geometry_checkpoint_sha256=digest(out/"geometry.npz"))
        self.store.candidate(aid,path.relative_to(self.store.asset_dir(aid)).as_posix(),"generated_local",metadata)
        self.store.update(aid,lambda a:a["settings"].update(source_rotation_degrees=[0,0,0]))
        ctx.update(progress=95)

    def _turntable(self,ctx):
        self._blender(ctx,"turntable")

    def _blender(self,ctx,operation):
        if not config.BLENDER:
            raise RuntimeError("Blender not found; set BLENDER_PATH")
        job,aid = ctx.job,ctx.job["asset_id"]
        candidate = job["candidate"]
        if not candidate:
            raise ValueError("Import or generate a mesh first")
        out = self.store.file(aid,f"processed/{job['id']}")
        source_relative=candidate["path"]
        if operation=="turntable":
            artifacts=self.store.get(aid)["artifacts"]
            if artifacts.get("candidate_id")==candidate["id"] and artifacts.get("files",{}).get("editable.blend"):
                source_relative=artifacts["files"]["editable.blend"]
        request = {"source":str(self.store.file(aid,source_relative)),"output":str(out),"settings":job["settings"],"operation":operation}
        path = self.store.file(aid,f"requests/{job['id']}.json")
        atomic_json(path,request)
        ctx.run_process([config.BLENDER,"--background","--threads","6","--python-exit-code","1","--python",str(config.ROOT/"blender/pipeline.py"),"--","--request",str(path)],timeout=1800,stage="blender_"+operation)
        files = {p.name:p.relative_to(self.store.asset_dir(aid)).as_posix() for p in out.iterdir() if p.is_file() and p.suffix != ".blend1"}
        if operation == "process":
            report = validate_glb(out/"runtime.glb")
            atomic_json(out/"validation.json",report)
            files["validation.json"] = (out/"validation.json").relative_to(self.store.asset_dir(aid)).as_posix()
            report["candidate_id"] = candidate["id"]
            def mutate(a):
                a["artifacts"] = {"files":files,"validation":report,"candidate_id":candidate["id"],"job_id":job["id"],"runtime_sha256":digest(out/"runtime.glb")}
                a["review"]["status"] = "pending"
                a["review"]["accepted_at"] = None
            self.store.update(aid,mutate)
        else:
            frames = [Image.open(out/f"turntable_{i:02d}.png").convert("RGB") for i in range(12)]
            frames[0].save(out/"turntable.gif",save_all=True,append_images=frames[1:],duration=150,loop=0)
            sheet = Image.new("RGB",(512*4,512*3))
            for i,frame in enumerate(frames):
                sheet.paste(frame,((i%4)*512,(i//4)*512))
            sheet.save(out/"turntable_sheet.jpg",quality=90)
            files["turntable.gif"] = (out/"turntable.gif").relative_to(self.store.asset_dir(aid)).as_posix()
            files["turntable_sheet.jpg"] = (out/"turntable_sheet.jpg").relative_to(self.store.asset_dir(aid)).as_posix()
            self.store.update(aid,lambda a:a["artifacts"].setdefault("previews",{}).update(files))
        ctx.update(checkpoint={"files":files},progress=95)

    def _godot(self,ctx):
        if not config.GODOT:
            raise RuntimeError("Godot not found; set GODOT_PATH")
        aid,job = ctx.job["asset_id"],ctx.job
        asset = self.store.get(aid)
        files = asset["artifacts"].get("files",{})
        if "runtime.glb" not in files:
            raise ValueError("Run Blender processing before Godot validation")
        project = self.store.file(aid,f"godot/{job['id']}")
        shutil.copytree(config.ROOT/"godot_validation",project,ignore=shutil.ignore_patterns(".godot","assets","results"),dirs_exist_ok=True)
        (project/"assets").mkdir(exist_ok=True)
        (project/"results").mkdir(exist_ok=True)
        shutil.copy2(self.store.file(aid,files["runtime.glb"]),project/"assets/asset.glb")
        for name,relative in files.items():
            if name in ("collision.glb","effects.glb","structure.glb") or name.startswith("lod") and name.endswith(".glb"):
                shutil.copy2(self.store.file(aid,relative),project/"assets"/name)
        # Optional separate weapon uses an explicit inspected source asset.
        equipment = job["settings"].get("equipment_asset")
        if equipment:
            other = self.store.get(equipment)
            path = other["artifacts"].get("files",{}).get("runtime.glb")
            if path:
                shutil.copy2(self.store.file(equipment,path),project/"assets/equipment.glb")
        atomic_json(project/"test_settings.json",{"instances":job["options"].get("instances",25),"asset_name":asset["name"],"preset":asset["preset"],"attachment":job["settings"].get("weapon_attachment",{}),"frames":180,"front_axis":job["settings"].get("front_axis","-Z")})
        ctx.run_process([config.GODOT,"--headless","--path",str(project),"--editor","--import"],120,"godot_import")
        # Godot generates mesh LODs by default. Disable that implicit destructive
        # step so the benchmark tests the exported geometry and explicit LODs.
        changed=False
        for import_config in (project/"assets").glob("*.glb.import"):
            content=import_config.read_text(encoding="utf-8")
            if "meshes/generate_lods=true" in content:
                content=content.replace("meshes/generate_lods=true","meshes/generate_lods=false")
                content=content.replace("meshes/force_disable_compression=false","meshes/force_disable_compression=true")
                import_config.write_text(content,encoding="utf-8")
                changed=True
        if changed:
            ctx.run_process([config.GODOT,"--headless","--path",str(project),"--editor","--import"],120,"godot_import_exact_geometry")
        ctx.run_process([config.GODOT,"--headless","--path",str(project),"--script","res://validate.gd"],120,"godot_technical")
        technical = json.loads((project/"results/technical.json").read_text(encoding="utf-8"))
        ctx.update(progress=70,checkpoint={"project":str(project),"technical":technical})
        if job["options"].get("rendered_benchmark",True):
            ctx.run_process([config.GODOT,"--path",str(project),"--rendering-method","gl_compatibility","--disable-vsync","--resolution","960x640"],180,"godot_rendered_benchmark")
        perf_path = project/"results/performance.json"
        perf = json.loads(perf_path.read_text(encoding="utf-8")) if perf_path.exists() else {"status":"not_measured","reason":"headless validation does not measure GPU performance"}
        gpu = subprocess.run(["nvidia-smi","--query-gpu=name,memory.total,driver_version","--format=csv,noheader"],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW).stdout.strip() if shutil.which("nvidia-smi") else "unknown"
        perf["hardware"] = inventory()
        atomic_json(project/"results/performance.json",perf)
        for clip in ("idle","walk","run","attack_01"):
            frames=[project/"results"/f"preview_{clip}_{i}.png" for i in range(6)]
            if all(p.exists() for p in frames):
                images=[Image.open(p).convert("RGB") for p in frames]
                images[0].save(project/"results"/f"preview_{clip}.gif",save_all=True,append_images=images[1:],duration=150,loop=0)
        self.store.update(aid,lambda a:a["artifacts"].update(godot={"project":project.relative_to(self.store.asset_dir(aid)).as_posix(),"technical":technical,"performance":perf,"candidate_id":a["selected_candidate"],"runtime_sha256":a["artifacts"].get("runtime_sha256")}))
        ctx.update(progress=95)
