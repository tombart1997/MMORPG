import copy
import json

import pytest
from PIL import Image

from forge import reference_sets as rs
from forge.backends import BACKENDS
from forge.jobs import JobManager
from forge.store import Store, digest, atomic_json
from test_contracts import triangle_glb


@pytest.fixture
def view_asset(tmp_path):
    store = Store(tmp_path)
    asset = store.create('Boar','creature',{'generation_seed':42,'trellis_steps':12})
    aid = asset['id']
    refs = []
    for i, angle in enumerate(('front','left','back')):
        path = store.file(aid,'references/'+angle+'.png')
        path.parent.mkdir(exist_ok=True)
        Image.new('RGB',(40+i,60),(100+i*30,90,80)).save(path)
        refs.append({'id':angle,'path':'references/'+angle+'.png','role':'primary' if i==0 else 'additional',
                     'resolution':[40+i,60],'sha256':digest(path)})
    store.update(aid,lambda a:a.update(references=refs))
    body = {'name':'Standing boar','source_reference_id':'front','pose':'Same neutral four-leg standing pose.',
            'scale_notes':'Matching head/body proportions and material palette.',
            'views':[{'angle':r['id'],'reference_id':r['id']} for r in refs]}
    return store, aid, body


def test_sets_reject_duplicate_angles_images_and_foreign_references(view_asset):
    store, aid, body = view_asset
    for replacement, message in [({'angle':'front','reference_id':'left'},'distinct'),
                                  ({'angle':'left','reference_id':'front'},'multiple'),
                                  ({'angle':'left','reference_id':'foreign'},'belong')]:
        invalid = copy.deepcopy(body)
        invalid['views'][1] = replacement
        with pytest.raises(ValueError,match=message):rs.create(store,aid,invalid)
    assert store.get(aid).get('reference_sets',[]) == []


def test_consistency_review_and_exact_file_hash_are_required(view_asset):
    store, aid, body = view_asset
    record = rs.create(store,aid,body)
    with pytest.raises(ValueError,match='approve'):rs.freeze(store,store.get(aid),record['id'])
    rs.review(store,aid,record['id'],True,'Opened all angles; inspected matching pose, tusks, limb spacing and materials.')
    snapshot = rs.freeze(store,store.get(aid),record['id'])
    store.file(aid,snapshot['views'][1]['path']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):rs.validate_snapshot(store,aid,snapshot)


def test_all_views_route_to_one_combined_backend_call_and_resume_is_frozen(view_asset,monkeypatch):
    store, aid, body = view_asset
    record = rs.create(store,aid,body)
    rs.review(store,aid,record['id'],True,'Opened all angles and checked consistent identity, silhouette and neutral pose.')
    calls = []
    def combined(paths,out,settings,ctx):
        calls.append(paths)
        atomic_json(out/'generation.json',{'model':'test adapter only','image_count':len(paths)})
        return triangle_glb(out/'source.glb')
    monkeypatch.setattr(BACKENDS['trellis'],'generate_multiview',combined)
    manager = JobManager(store,start=False)
    with pytest.raises(ValueError,match='one image'):
        manager.submit(aid,'generate',{'backend':'triposg','reference_set_id':record['id']})
    job = manager.submit(aid,'generate',{'backend':'trellis','reference_set_id':record['id']})
    manager.execute(job['id'])
    assert store.get_job(job['id'])['state']=='succeeded'
    assert calls == [[store.file(aid,v['path']) for v in record['views']]]
    assert len(store.get(aid)['candidates']) == 1
    assert store.get(aid)['candidates'][0]['reference_set']['signature'] == record['signature']
    # A retained failed job resumes its exact backend/settings/set, regardless of new UI options.
    frozen = store.get_job(job['id']); frozen['state']='failed'; store.save_job(frozen)
    resumed = manager.submit(aid,'generate',{'backend':'triposg'},resume_id=job['id'])
    assert resumed['options']['backend']=='trellis'
    assert resumed['reference_set']['signature']==record['signature']


def test_changed_reference_never_reaches_backend(view_asset,monkeypatch):
    store, aid, body = view_asset
    record=rs.create(store,aid,body)
    rs.review(store,aid,record['id'],True,'Opened all views and verified matching pose, scale, materials and full extremities.')
    manager=JobManager(store,start=False)
    job=manager.submit(aid,'generate',{'backend':'trellis','reference_set_id':record['id']})
    store.file(aid,record['views'][2]['path']).write_bytes(b'mutated after enqueue')
    monkeypatch.setattr(BACKENDS['trellis'],'generate_multiview',lambda *args: pytest.fail('Changed input reached inference'))
    manager.execute(job['id'])
    assert store.get_job(job['id'])['state']=='failed'
    assert not store.get(aid)['candidates']
