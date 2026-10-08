"""Reviewed, ordered, immutable multi-image input snapshots."""
import copy
import hashlib
import json
import uuid

from .store import digest, now

ANGLES = ('front', 'left', 'back', 'right', 'three_quarter', 'top')


def members(store, asset, views):
    if not 2 <= len(views) <= 6:
        raise ValueError('A view set requires two to six separate images')
    angles, refs, hashes, result = set(), set(), set(), []
    for view in views:
        angle, ref_id = view['angle'], view['reference_id']
        if angle not in ANGLES or angle in angles:
            raise ValueError('Choose a distinct supported angle for each view')
        if ref_id in refs:
            raise ValueError('One image cannot stand for multiple angles')
        ref = next((r for r in asset['references'] if r['id'] == ref_id), None)
        if not ref:
            raise ValueError('View reference does not belong to this asset')
        path = store.file(asset['id'], ref['path'])
        current = digest(path)
        if current != ref['sha256']:
            raise ValueError('Reference bytes changed; upload the changed image as a new reference')
        if current in hashes:
            raise ValueError('Duplicate image content cannot provide another view')
        angles.add(angle)
        refs.add(ref_id)
        hashes.add(current)
        result.append({'angle':angle, 'reference_id':ref_id, 'path':ref['path'],
                       'sha256':current, 'resolution':ref['resolution']})
    return sorted(result, key=lambda v: ANGLES.index(v['angle']))


def signature(record):
    # Review binds the exact ordered inputs AND pose/design constraints.
    value = {k: record[k] for k in ('views','pose','scale_notes','source_reference_id')}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def create(store, asset_id, body):
    asset = store.get(asset_id)
    if not any(r['id'] == body['source_reference_id'] for r in asset['references']):
        raise ValueError('Original concept authority must belong to this asset')
    record = {'id':uuid.uuid4().hex[:12], 'name':body['name'], 'pose':body['pose'],
              'scale_notes':body['scale_notes'], 'source_reference_id':body['source_reference_id'],
              'views':members(store,asset,body['views']), 'created_at':now(),
              'review':{'status':'pending', 'notes':''}}
    record['signature'] = signature(record)
    def mutate(a):
        a.setdefault('reference_sets',[]).append(record)
        a['selected_reference_set'] = record['id']
    store.update(asset_id,mutate)
    return record


def get(asset, set_id):
    record = next((s for s in asset.get('reference_sets',[]) if s['id'] == set_id),None)
    if not record:
        raise ValueError('Reference set does not exist')
    return record


def review(store, asset_id, set_id, approved, notes):
    asset = store.get(asset_id)
    record = get(asset,set_id)
    members(store,asset,record['views'])
    if signature(record) != record['signature']:
        raise ValueError('View set changed; create a new reviewed set')
    if len(notes.strip()) < 20:
        raise ValueError('Record the pose, proportions and material consistency inspection')
    def mutate(a):
        get(a,set_id)['review'] = {'status':'approved' if approved else 'rejected',
                                 'notes':notes, 'signature':record['signature'], 'reviewed_at':now()}
    store.update(asset_id,mutate)
    return get(store.get(asset_id),set_id)


def freeze(store, asset, set_id):
    record = get(asset,set_id)
    if record['review']['status'] != 'approved' or record['review'].get('signature') != signature(record):
        raise ValueError('Inspect and approve view set consistency before combined-image generation')
    members(store,asset,record['views'])
    return copy.deepcopy(record)


def validate_snapshot(store, asset_id, record):
    if signature(record) != record['signature'] or record['review'].get('signature') != record['signature']:
        raise ValueError('Queued view set no longer matches its consistency review')
    for view in record['views']:
        if digest(store.file(asset_id,view['path'])) != view['sha256']:
            raise ValueError('Queued reference changed; retained job will not silently use new pixels')
