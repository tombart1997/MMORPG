import json
import struct
import threading
import time
import sys
from pathlib import Path

import numpy as np
import pytest

from forge.backends import BACKENDS, MeshyBackend, TripoSRBackend, TripoSGBackend
from forge.jobs import Cancelled, JobManager, Context
from forge.store import Store, atomic_json, digest
from forge.validation import validate_glb


def triangle_glb(path,degenerate=False,external_texture=False):
    vertices=np.array([[0,0,0],[1,0,0],[0 if not degenerate else 2,1 if not degenerate else 0,0]],dtype='<f4').tobytes()
    normals=np.array([[0,0,1]]*3,dtype='<f4').tobytes()
    binary=vertices+normals
    doc={"asset":{"version":"2.0"},"buffers":[{"byteLength":len(binary)}],"bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":36},{"buffer":0,"byteOffset":36,"byteLength":36}],"accessors":[{"bufferView":0,"componentType":5126,"count":3,"type":"VEC3"},{"bufferView":1,"componentType":5126,"count":3,"type":"VEC3"}],"meshes":[{"primitives":[{"attributes":{"POSITION":0,"NORMAL":1}}]}],"nodes":[{"mesh":0}],"scenes":[{"nodes":[0]}],"scene":0}
    if external_texture:
        doc["images"]=[{"uri":"missing.png"}]
    json_bytes=json.dumps(doc).encode();json_bytes+=b' '*(4-len(json_bytes)%4 if len(json_bytes)%4 else 0)
    content=struct.pack('<II',len(json_bytes),0x4E4F534A)+json_bytes+struct.pack('<II',len(binary),0x004E4942)+binary
    path.write_bytes(struct.pack('<4sII',b'glTF',2,len(content)+12)+content)
    return path


def make_asset(store):
    return store.create("Test sword","equipment",{"triangle_budget":1000,"texture_resolution":2048})


def test_manifest_source_integrity_and_path_containment(tmp_path):
    store=Store(tmp_path);asset=make_asset(store)
    source=store.file(asset['id'],'imports/source.glb');source.parent.mkdir();triangle_glb(source)
    expected=digest(source)
    candidate=store.candidate(asset['id'],'imports/source.glb','imported')
    store.update(asset['id'],lambda a:a['settings'].update(triangle_budget=400))
    assert digest(source)==expected==candidate['sha256']
    assert store.get(asset['id'])['candidates'][0]['origin']=='imported'
    with pytest.raises(ValueError):store.file(asset['id'],'../../outside')
    with pytest.raises(ValueError):store.asset_dir('../bad')


@pytest.mark.parametrize('bad,external,passed',[(False,False,True),(True,False,False),(False,True,False)])
def test_export_validation_detects_real_geometry_and_dependency_errors(tmp_path,bad,external,passed):
    report=validate_glb(triangle_glb(tmp_path/'mesh.glb',bad,external))
    assert (report['technical_status']=='passed')==passed
    assert report['visual_status']=='pending'
    assert report['triangles']==1


def test_truncated_export_is_rejected(tmp_path):
    p=triangle_glb(tmp_path/'asset.glb');p.write_bytes(p.read_bytes()[:-5])
    assert validate_glb(p)['technical_status']=='failed'


def test_backend_capabilities_and_paid_boundary(tmp_path):
    local=TripoSRBackend().capabilities();paid=MeshyBackend()
    assert local['single_image'] and not local['multi_view'] and not local['rigging'] and not local['pbr']
    assert not paid.capabilities()['available']
    with pytest.raises(RuntimeError,match='disabled'):paid.generate(tmp_path/'ref.png',tmp_path,{},None)


def test_geometry_backend_routes_jobs_and_never_promises_textures(tmp_path,monkeypatch):
    capability=TripoSGBackend().capabilities()
    assert capability['single_image'] and capability['seeds']
    assert not capability['textures'] and not capability['pbr'] and not capability['retexture']
    store=Store(tmp_path);asset=make_asset(store)
    image=store.file(asset['id'],'references/sword.png');image.parent.mkdir();image.write_bytes(b'fixture')
    store.update(asset['id'],lambda a:a['references'].append({'path':'references/sword.png','role':'primary','sha256':digest(image)}))
    manager=JobManager(store,start=False);calls=[]
    def fixture_backend(reference,output,settings,context):
        calls.append(reference)
        path=triangle_glb(output/'source.glb')
        atomic_json(output/'generation.json',{'model':'fixture geometry adapter'})
        return path
    monkeypatch.setattr(BACKENDS['triposg'],'generate',fixture_backend)
    with pytest.raises(ValueError,match='Unknown'):manager.submit(asset['id'],'generate',{'backend':'not_a_model'})
    job=manager.submit(asset['id'],'generate',{'backend':'triposg'})
    manager.execute(job['id'])
    assert calls==[image] and store.get_job(job['id'])['state']=='succeeded'
    assert store.selected(asset['id'])['backend']=='triposg'


def test_job_snapshots_inputs_blocks_overlap_and_recovers_restart(tmp_path):
    store=Store(tmp_path);a=make_asset(store);manager=JobManager(store,start=False)
    job=manager.submit(a['id'],'process')
    with pytest.raises(ValueError,match='active'):manager.submit(a['id'],'process')
    store.update(a['id'],lambda a:a['settings'].update(triangle_budget=2))
    assert store.get_job(job['id'])['settings']['triangle_budget']==1000
    restarted=JobManager(store,start=False)
    assert store.get_job(job['id'])['state']=='interrupted'
    resumed=restarted.submit(a['id'],'process',resume_id=job['id'])
    assert resumed['settings']['triangle_budget']==1000


def test_queued_cancellation_preserves_manifest(tmp_path):
    store=Store(tmp_path);a=make_asset(store);manager=JobManager(store,start=False)
    job=manager.submit(a['id'],'process');manager.cancel(job['id']);manager.execute(job['id'])
    assert store.get_job(job['id'])['state']=='cancelled'
    assert store.get(a['id'])['history'][-1]['state']=='cancelled'


def test_retry_budget_requires_reason_and_rejects_paid_backend(tmp_path):
    store=Store(tmp_path);a=make_asset(store);manager=JobManager(store,start=False)
    with pytest.raises(ValueError,match='Paid'):manager.submit(a['id'],'generate',{'backend':'meshy'})
    first=manager.submit(a['id'],'generate')
    first['state']='failed';store.save_job(first)
    with pytest.raises(ValueError,match='reason'):manager.submit(a['id'],'generate')
    for i in range(2):
        job=manager.submit(a['id'],'generate',reason='Inspect a targeted silhouette change')
        job['state']='failed';store.save_job(job)
    with pytest.raises(ValueError,match='budget'):manager.submit(a['id'],'generate',reason='Fourth try')


def test_background_process_timeout_and_cancellation_are_real(tmp_path):
    store=Store(tmp_path);a=make_asset(store);manager=JobManager(store,start=False)
    job=manager.submit(a['id'],'process');context=Context(manager,job)
    with pytest.raises(TimeoutError):
        context.run_process([sys.executable,'-c','import time; time.sleep(20)'],timeout=0.05,stage='timeout_test')
    context.cancel.set()
    with pytest.raises(Cancelled):
        context.run_process([sys.executable,'-c','import time; time.sleep(20)'],timeout=10,stage='cancel_test')
