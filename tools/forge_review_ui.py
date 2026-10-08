"""Actual Chrome UI integration: editable plans, comparisons and version history."""
from pathlib import Path
import json,urllib.request,copy
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/asset_review/ui';OUT.mkdir(exist_ok=True)
URL='http://127.0.0.1:8742'
def api(path,body=None,method=None):
    request=urllib.request.Request(URL+'/api'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Content-Type':'application/json','Origin':URL,'X-Forge-Request':'1'})
    with urllib.request.urlopen(request,timeout=30) as r:return json.load(r)
errors=[];checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1080},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    def selected(aid):
        asset=api('/assets/'+aid)
        page.wait_for_function("arg=>document.querySelector('#asset-title').textContent===arg.name && JSON.parse(document.querySelector('#diagnosis-editor').value||'{}').source_sha256===arg.sha",arg={'name':asset['name'],'sha':asset['reviewflow']['diagnosis']['source_sha256']})
    page.goto(URL+'/?asset=f03ebd870fd5',wait_until='networkidle');page.locator('#asset-title').wait_for()
    page.locator('#library-status').select_option('KEEP')
    page.locator('[data-id="f03ebd870fd5"]').click()
    page.locator('[data-tab="repairs"]').click()
    selected('f03ebd870fd5')
    page.wait_for_function("document.querySelector('#repair-status').textContent.includes('KEEP')")
    page.wait_for_function("document.querySelectorAll('#repair-comparisons img').length===2 && Array.from(document.querySelectorAll('#repair-comparisons img')).every(i=>i.complete&&i.naturalWidth>0)")
    assert page.locator('#repair-comparisons span').all_text_contents()==['before.png','after.png']
    assert 'accepted' in page.locator('#repair-versions').inner_text()
    assert page.locator('[data-rollback]').count()>0 and page.locator('[data-deploy]').count()>0
    assert 'rejected' in page.locator('#repair-attempts').inner_text()
    assert page.locator('#run-repair').is_disabled()
    checks+=['Asset deep link','Status filter','Accepted version and rollback controls','Opened before/after comparison images loaded','Rejected attempt history and time/cost','KEEP excludes unnecessary repair']
    page.screenshot(path=str(OUT/'tower.png'))
    page.locator('#library-search').fill('ironhide')
    page.locator('[data-id="ec2c860e6fb3"]').click()
    selected('ec2c860e6fb3')
    page.wait_for_function("document.querySelector('#repair-versions').textContent.includes('temporary fallback')")
    assert 'Future art work' in page.locator('#repair-remaining').inner_text()
    page.wait_for_function("Array.from(document.querySelectorAll('#repairs img')).every(i=>i.complete&&i.naturalWidth>0)")
    assert 'temporary fallback' in page.locator('#repair-status').inner_text()
    page.screenshot(path=str(OUT/'fallback.png'))
    page.locator('#repair-comparisons').scroll_into_view_if_needed()
    page.screenshot(path=str(OUT/'fallback_comparison.png'))
    checks+=['Search filter','Temporary fallback limitations and remaining art work visible']
    page.locator('[data-tab="workspace"]').click()
    a=api('/assets/ec2c860e6fb3');archived=[c for c in a['candidates'] if c.get('archived')]
    assert archived
    for c in archived:assert page.locator(f'[data-candidate="{c["id"]}"]').is_disabled()
    checks.append('Archived candidates cannot be selected')
    # Exercise a reversible budget edit through the real editor; restore it.
    page.locator('#library-status').select_option('POLISH');page.locator('#library-search').fill('meadow')
    page.locator('[data-id="560e5a5320c9"]').click();page.locator('[data-tab="repairs"]').click()
    selected('560e5a5320c9')
    page.wait_for_function("document.querySelector('#repair-status').textContent.includes('POLISH')")
    original=api('/assets/560e5a5320c9/diagnosis')['diagnosis']
    modified=copy.deepcopy(original);modified['budget']['elapsed_seconds']=361
    try:
        page.locator('#diagnosis-editor').fill(json.dumps(modified,indent=2))
        with page.expect_response(lambda r:r.url.endswith('/diagnosis') and r.request.method=='PUT') as response:
            page.locator('#save-diagnosis').click()
        assert response.value.status==200
        assert api('/assets/560e5a5320c9/diagnosis')['budget']['elapsed_seconds']==361
        page.wait_for_timeout(1500)
        unsupported=copy.deepcopy(modified);unsupported['plan']=[{'operation':'make_beautiful','parameters':{}}]
        page.locator('#diagnosis-editor').fill(json.dumps(unsupported))
        with page.expect_response(lambda r:r.url.endswith('/diagnosis') and r.request.method=='PUT') as response:
            page.locator('#save-diagnosis').click()
        assert response.value.status==400,(response.value.status,response.value.text())
        checks+=['Editable budget saved through UI','Unsupported repair operation refused by API']
    finally:api('/assets/560e5a5320c9/diagnosis',original,'PUT')
    browser.close()
assert not errors,errors
(OUT/'report.json').write_text(json.dumps({'status':'passed','checks':checks,'page_errors':errors,'scope':'Actual Chrome and live API; no game deployment or rollback triggered by the UI smoke test.'},indent=2)+'\n')
print('PASS:',len(checks),'live review UI checks')
