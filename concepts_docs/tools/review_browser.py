"""Inspect offline pages with installed Chrome; save visible-page review captures."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parents[1]
REVIEW=BASE/'review'

def review():
    REVIEW.mkdir(exist_ok=True)
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto((BASE/'index.html').as_uri());page.screenshot(path=str(REVIEW/'index.png'))
        assert page.locator('.tile').count()==17
        assert page.evaluate('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
        page.goto((BASE/'bestiary.html').as_uri());page.screenshot(path=str(REVIEW/'bestiary.png'))
        assert page.locator('.mob').count()==37
        page.locator('#player-level').fill('1')
        meadow=page.locator('.mob[data-name="meadow wolf"]')
        assert meadow.locator('.effective').first.text_content()=='22.500%'
        page.locator('#player-level').fill('25')
        assert meadow.locator('.effective').first.text_content()=='0%'
        page.locator('#family').select_option('spider')
        assert page.locator('.mob:visible').count()==6
        page.locator('#family').select_option('all');page.locator('#search').fill('moonfang')
        assert page.locator('.mob:visible').count()==1
        page.locator('#search').fill('');page.locator('#player-level').fill('8')
        moon=page.locator('.mob[data-name="moonfang"]')
        assert moon.locator('.factor').text_content().startswith('Proposed level multiplier: 1.0000')
        for name in ['young mossling','bristle boar','ash bandit']:
            page.locator(f'.mob[data-name="{name}"]').screenshot(path=str(REVIEW/f'{name.replace(" ","_")}.png'))
        page.goto((BASE/'sheets/01_smithing_upgrades.html').as_uri());page.screenshot(path=str(REVIEW/'smithing.png'))
        assert page.locator('table').count()==2
        assert page.evaluate('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
        page.goto((BASE/'sheets/16_quality_performance.html').as_uri())
        page.screenshot(path=str(REVIEW/'quality_performance.png'))
        assert '15.253 ms' in page.locator('body').inner_text()
        assert '111' in page.locator('body').inner_text()
        page.set_viewport_size({'width':390,'height':844});page.goto((BASE/'index.html').as_uri())
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(REVIEW/'mobile_index.png'))
        browser.close()
    assert not errors,errors
    (REVIEW/'browser_report.json').write_text(json.dumps({'result':'PASS','checks':['17 topic links','37 mob cards','images load offline','equal-level base rates','far-gap zero rates','family filter','search filter','Moonfang level-8 multiplier','smithing tables and art','mobile viewport has no horizontal overflow','no JavaScript page errors']},indent=2)+'\n',encoding='utf-8')
    print('PASS: offline browser pages, interactive drop preview, filters, images and mobile layout.')

if __name__=='__main__':
    review()
