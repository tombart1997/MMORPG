"""Exercise the real multi-view editor; do not queue expensive inference."""
import json
import importlib.metadata
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/evidence/multiview'
OUT.mkdir(parents=True, exist_ok=True)
errors, checks = [], []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page = browser.new_page(viewport={'width':1500,'height':1050})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8743/?asset=4c42176e618f', wait_until='networkidle')
    page.get_by_role('button', name='References', exact=True).click()
    page.wait_for_selector('.mv-set')
    assert page.locator('.mv-thumbs img').count() == 4
    for thumb in page.locator('.mv-thumbs img').all():
        assert thumb.evaluate('(img) => img.complete && img.naturalWidth > 0')
    checks.append('Four distinct approved horse views load in the reference editor')
    page.locator('.multiview-panel').screenshot(path=str(OUT/'horse_reference_editor.png'))
    page.get_by_role('button', name='Workbench', exact=True).click()
    assert page.locator('#generation-backend').input_value() == 'trellis'
    assert page.locator('#mv-generation-set').input_value() == '31a1ad66a56e'
    assert page.locator('#generate').is_enabled()
    page.locator('#mv-generation-set').select_option('')
    page.locator('#generation-backend').select_option('triposg')
    assert page.locator('#mv-mode').is_disabled()
    assert page.locator('#mv-generation-set').is_disabled()
    checks.append('Single-image backend disables combined-view settings')
    page.locator('#generation-backend').select_option('trellis')
    assert page.locator('#mv-generation-set').input_value() == ''
    page.locator('#mv-generation-set').select_option('31a1ad66a56e')
    page.locator('#mv-mode').select_option('stochastic')
    assert page.locator('#mv-mode').input_value() == 'stochastic'
    page.locator('#mv-project-colors').uncheck()
    assert page.locator('#mv-project-colors').is_checked() is False
    page.locator('#mv-project-colors').check()
    page.locator('#mv-mode').select_option('multidiffusion')
    page.screenshot(path=str(OUT/'horse_generation_controls.png'), full_page=True)
    checks.append('Approved set, conditioning mode and color projection remain selectable without starting a job')
    for aid, count in [('676305c94d3e',4),('234a200b7ba4',2),('8af3d45eaca9',3)]:
        page.goto('http://127.0.0.1:8743/?asset='+aid, wait_until='networkidle')
        page.get_by_role('button', name='References', exact=True).click()
        assert page.locator('.mv-thumbs img').count() == count
    checks.append('Spider, fern and tower load their reviewed sets; omitted views stay omitted')
    browser.close()
report={'page_errors':errors,'checks':checks,'playwright_version':importlib.metadata.version('playwright'),
    'screenshots':[x.name for x in OUT.glob('*.png')]}
(OUT/'browser_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
if errors: raise SystemExit(1)
