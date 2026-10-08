import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from forge import api
from forge.jobs import JobManager
from forge.store import Store, digest
from test_contracts import triangle_glb

H={'x-forge-request':'1'}


@pytest.fixture
def client(tmp_path,monkeypatch):
    store=Store(tmp_path);monkeypatch.setattr(api,'store',store);monkeypatch.setattr(api,'manager',JobManager(store,start=False))
    with TestClient(api.app) as client:yield client,store


def create(client):
    return client.post('/api/assets',json={'name':'Sword','preset':'equipment'},headers=H).json()


def test_browser_cross_origin_writes_and_paid_requests_are_blocked(client):
    c,store=client
    assert c.post('/api/assets',json={'name':'x'},headers={**H,'Origin':'https://outside.example'}).status_code==403
    assert c.post('/api/assets',json={'name':'x'}).status_code==403
    a=create(c)
    r=c.post(f"/api/assets/{a['id']}/jobs",json={'operation':'generate','options':{'backend':'meshy'}},headers=H)
    assert r.status_code==400
    assert store.jobs()==[]


def test_reference_crop_retains_original_resolution_and_hash(client):
    c,store=client;a=create(c);image=Image.new('RGB',(640,480),'white');buffer=io.BytesIO();image.save(buffer,format='PNG')
    r=c.post(f"/api/assets/{a['id']}/references",files={'file':('art.png',buffer.getvalue(),'image/png')},headers=H).json()
    original_hash=digest(store.file(a['id'],r['path']))
    result=c.post(f"/api/assets/{a['id']}/prepare",json={'reference_id':r['id'],'crop':[5,10,120,250]},headers=H)
    assert result.status_code==200 and result.json()['resolution']==[120,250]
    assert digest(store.file(a['id'],r['path']))==original_hash
    assert c.post(f"/api/assets/{a['id']}/prepare",json={'reference_id':r['id'],'crop':[600,0,100,100]},headers=H).status_code==400


def test_acceptance_and_export_are_version_bound(client,tmp_path):
    c,store=client;a=create(c);aid=a['id']
    assert c.get(f'/api/assets/{aid}/export').status_code==409
    assert c.put(f'/api/assets/{aid}/review',json={'status':'accepted'},headers=H).status_code==400
    path=store.file(aid,'processed/runtime.glb');path.parent.mkdir();triangle_glb(path)
    source=store.candidate(aid,'processed/runtime.glb','imported')
    store.update(aid,lambda a:a.update(artifacts={'files':{'runtime.glb':'processed/runtime.glb'},'validation':{'technical_status':'passed'},'runtime_sha256':digest(path)}))
    names=c.get(f'/api/assets/{aid}/review-checks').json()
    body={'status':'accepted','checklist':{name:True for name in names},'defects':[{'description':'Missing engraving','resolved':False}]}
    assert c.put(f'/api/assets/{aid}/review',json=body,headers=H).status_code==400
    body['override_reason']='Approved for temporary prototype use'
    assert c.put(f'/api/assets/{aid}/review',json=body,headers=H).status_code==200
    assert c.get(f'/api/assets/{aid}/export').status_code==200
    settings=c.get(f'/api/assets/{aid}').json()['settings'];settings['triangle_budget']=200
    assert c.put(f'/api/assets/{aid}/settings',json=settings,headers=H).status_code==200
    assert c.get(f'/api/assets/{aid}/export').status_code==409


def test_turnaround_consistency_gate_survives_derived_views(client):
    c,store=client;a=create(c);image=Image.new('RGB',(40,60),'gray');buffer=io.BytesIO();image.save(buffer,format='PNG')
    r=c.post(f"/api/assets/{a['id']}/references",files={'file':('view.png',buffer.getvalue(),'image/png')},data={'role':'turnaround_pending'},headers=H).json()
    body={'reference_id':r['id'],'crop':[0,0,40,60]}
    assert c.post(f"/api/assets/{a['id']}/prepare",json=body,headers=H).status_code==400
    body['role']='additional'
    derived=c.post(f"/api/assets/{a['id']}/prepare",json=body,headers=H).json()
    assert derived['consistency_review']=='pending'
    assert c.post(f"/api/assets/{a['id']}/prepare",json={'reference_id':derived['id']},headers=H).status_code==400
    response=c.put(f"/api/assets/{a['id']}/references/{r['id']}/review",json={'consistency_approved':True,'notes':'Silhouette and costume checked against the original'},headers=H)
    assert response.status_code==200
    assert c.post(f"/api/assets/{a['id']}/prepare",json={'reference_id':r['id']},headers=H).status_code==200
