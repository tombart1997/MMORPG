import copy
import pytest
from forge import reviewflow
from forge.store import Store,digest
from test_contracts import triangle_glb


@pytest.fixture
def asset(tmp_path):
    store=Store(tmp_path);a=store.create('Inspection','equipment',{})
    path=store.file(a['id'],'imports/source.glb');path.parent.mkdir();triangle_glb(path)
    c=store.candidate(a['id'],'imports/source.glb','imported')
    evidence=store.file(a['id'],'mesh.json');evidence.write_text('{}')
    store.update(a['id'],lambda a:a.update(artifacts={'files':{'runtime.glb':'imports/source.glb','mesh.json':'mesh.json'},'validation':{'technical_status':'passed'},'runtime_sha256':digest(path),
        'godot':{'technical':{'status':'passed'},'runtime_sha256':digest(path)}}))
    diagnosis={'status':'POLISH','source_sha256':digest(path),'criteria':['Straight blade and readable guard'],
        'confidence':'high','evidence':[{'kind':'mesh','path':'mesh.json'}],'defects':[{'region':'blade','description':'Shading'}],
        'plan':[{'operation':'normals_repair','parameters':{'object':'Blade'}}],'remaining_review':[]}
    reviewflow.save_diagnosis(store,a['id'],diagnosis)
    return store,a['id'],diagnosis


def test_diagnosis_requires_exact_mesh_and_evidence(asset):
    store,aid,d=asset
    d['source_sha256']='wrong'
    with pytest.raises(ValueError,match='exact'):reviewflow.save_diagnosis(store,aid,d)
    d['source_sha256']=reviewflow.current_hash(store,store.get(aid));d['evidence']=[{'kind':'render','path':'mesh.json'}]
    with pytest.raises(ValueError,match='mesh inspection'):reviewflow.save_diagnosis(store,aid,d)


def test_unsupported_parameters_and_paid_generation_are_refused():
    with pytest.raises(ValueError,match='Unsupported'):
        reviewflow.validate_plan([{'operation':'normals_repair','parameters':{'object':'a','make_beautiful':True}}])
    with pytest.raises(ValueError,match='Paid'):
        reviewflow.validate_plan([{'operation':'regenerate','parameters':{'backend':'meshy'}}])
    with pytest.raises(ValueError,match='explicit region'):
        reviewflow.validate_plan([{'operation':'selective_smooth','parameters':{'object':'a'}}])


def test_attempt_budgets_and_failed_approach_cannot_repeat(asset):
    store,aid,d=asset;t=reviewflow.begin_attempt(store,aid)
    with pytest.raises(ValueError,match='Review'):reviewflow.begin_attempt(store,aid)
    store.update(aid,lambda a:a['reviewflow']['attempts'][0].update(state='rejected'))
    with pytest.raises(ValueError,match='Change the approach'):reviewflow.begin_attempt(store,aid)
    d['plan'][0]['parameters']['object']='AnotherBlade';reviewflow.save_diagnosis(store,aid,d)
    reviewflow.begin_attempt(store,aid)
    store.update(aid,lambda a:a['reviewflow']['attempts'][1].update(state='failed'))
    d['plan'][0]['parameters']['object']='Third';reviewflow.save_diagnosis(store,aid,d)
    with pytest.raises(ValueError,match='budget'):reviewflow.begin_attempt(store,aid)


def test_rejected_attempt_preserves_result_and_restores_working_mapping(asset):
    store,aid,d=asset;original=store.get(aid);t=reviewflow.begin_attempt(store,aid)
    store.update(aid,lambda a:a['reviewflow']['attempts'][0].update(state='requires_review',result_sha256=reviewflow.current_hash(store,a),
        before_artifacts=original['artifacts'],before_candidate_id=original['selected_candidate']))
    reviewflow.review_attempt(store,aid,t['id'],{'decision':'rejected','notes':'Silhouette worsened','evidence':['mesh.json'],'regressions':['blade']})
    a=store.get(aid);assert a['artifacts']==original['artifacts'];assert a['reviewflow']['attempts'][0]['rejected_artifacts']
    assert store.file(aid,'imports/source.glb').is_file()


def test_immutable_versions_require_review_and_exact_godot_hash(asset):
    store,aid,d=asset
    r={'notes':'Reviewed source and actual imported material.','evidence':['mesh.json'],'checks':{k:True for k in ['reference_fidelity','silhouette','materials','no_regressions','gameplay_distance','integration']}}
    store.update(aid,lambda a:a['artifacts']['godot'].update(runtime_sha256='outdated'))
    with pytest.raises(ValueError,match='different runtime'):reviewflow.promote(store,aid,r)
    store.update(aid,lambda a:a['artifacts']['godot'].update(runtime_sha256=a['artifacts']['runtime_sha256']))
    first=reviewflow.promote(store,aid,r);second=reviewflow.promote(store,aid,r)
    assert second['previous']==first['id']
    reviewflow.rollback(store,aid,first['id']);assert reviewflow.state(store.get(aid))['accepted_version']==first['id']
    store.file(aid,first['runtime']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):reviewflow.rollback(store,aid,first['id'])


def test_archiving_retains_original_but_disables_selection(asset):
    store,aid,d=asset;cid=store.get(aid)['selected_candidate']
    reviewflow.archive_candidate(store,aid,cid,'Unacceptable candidate')
    a=store.get(aid);assert a['selected_candidate'] is None and a['candidates'][0]['archived']
    assert store.file(aid,'imports/source.glb').is_file()


def test_interruption_restores_source_archives_output_and_consumes_budget(asset):
    store,aid,d=asset;original=store.get(aid);t=reviewflow.begin_attempt(store,aid)
    path=store.file(aid,'imports/failed.glb');path.write_bytes(b'failed output')
    candidate=store.candidate(aid,'imports/failed.glb','repair')
    def running(a):
        a['reviewflow']['attempts'][-1].update(state='running',before_artifacts=original['artifacts'],before_candidate_id=original['selected_candidate'])
        a['artifacts']={'candidate_id':candidate['id'],'files':{'runtime.glb':'imports/failed.glb'}}
    store.update(aid,running)
    reviewflow.fail_attempt(store,aid,t['id'],'Application interrupted',32)
    a=store.get(aid)
    assert a['artifacts']==original['artifacts'] and a['selected_candidate']==original['selected_candidate']
    assert next(c for c in a['candidates'] if c['id']==candidate['id'])['archived']
    assert a['reviewflow']['attempts'][-1]['elapsed_seconds']==32
    assert path.read_bytes()==b'failed output'
    with pytest.raises(ValueError,match='Change the approach'):reviewflow.begin_attempt(store,aid)


def test_fallback_is_explicit_and_does_not_claim_reference_fidelity(asset):
    store,aid,d=asset
    review={'notes':'Saved clean previous mesh; generated limbs fail animation.','evidence':['mesh.json'],
        'checks':{k:True for k in ['silhouette','materials','no_regressions','gameplay_distance','integration']}}
    with pytest.raises(ValueError,match='independent'):reviewflow.promote(store,aid,review)
    review['fallback']=True
    with pytest.raises(ValueError,match='limitations'):reviewflow.promote(store,aid,review)
    review['fallback_reason']='Temporary previous model has simpler armor than the concept.'
    version=reviewflow.promote(store,aid,review)
    assert version['review']['fallback'] and not version['review']['checks'].get('reference_fidelity')


def test_game_promotion_hash_guard_and_rollback_preserve_entities(asset,tmp_path,monkeypatch):
    from forge import game_bridge
    store,aid,d=asset;game=tmp_path/'game';monkeypatch.setattr(game_bridge,'GAME',game)
    source=game/'assets/original.glb';source.parent.mkdir(parents=True);source.write_bytes(b'working scene')
    entity=game/'authored_spawns.json';entity.write_text('153 authored camps')
    store.update(aid,lambda a:a['reviewflow'].update(game_binding={'target':'res://assets/original.glb'}))
    review={'notes':'Reviewed exact candidate in isolated and game scenes.','evidence':['mesh.json'],
        'checks':{k:True for k in ['reference_fidelity','silhouette','materials','no_regressions','gameplay_distance','integration']}}
    version=reviewflow.promote(store,aid,review);runtime=store.file(aid,version['runtime']);retained=runtime.read_bytes()
    runtime.write_bytes(b'mutated after review')
    with pytest.raises(ValueError,match='hash changed'):game_bridge.apply_version(store,aid,version['id'])
    registry=game/'data/visuals/reviewed_versions.json';assert not registry.exists()
    runtime.write_bytes(retained);mapped=game_bridge.apply_version(store,aid,version['id']);before=registry.read_bytes()
    runtime.write_bytes(b'mutated again')
    with pytest.raises(ValueError,match='hash changed'):game_bridge.apply_version(store,aid,version['id'])
    assert registry.read_bytes()==before
    previous=game/mapped['previous']['path'][6:];backup=previous.read_bytes();previous.write_bytes(b'mutated baseline')
    with pytest.raises(ValueError,match='Rollback file changed'):game_bridge.rollback_game(store,aid)
    assert registry.read_bytes()==before
    previous.write_bytes(backup);restored=game_bridge.rollback_game(store,aid)
    assert restored['sha256']==mapped['previous']['sha256'] and source.read_bytes()==b'working scene'
    assert entity.read_text()=='153 authored camps'
