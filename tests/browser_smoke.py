"""Optional browser end-to-end checks. Requires Playwright and Chromium.
Uses set_content: the build is self-contained. Does not require a web server.
"""
from pathlib import Path
import json, shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[]
with sync_playwright() as p:
    exe=shutil.which('chromium') or p.chromium.executable_path
    browser=p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1050},accept_downloads=True)
    errors=[]; requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda req:requests.append(req.url))
    page.set_content((ROOT/'index.html').read_text(encoding='utf-8'),wait_until='load')
    page.locator('#lang-ru').click()  # Historical smoke assertions use Russian labels.
    assert '14/14' in page.locator('#test-status').inner_text();checks.append('live browser self-tests')
    page.locator('[data-preset="no-facts"]').click()
    assert page.locator('#s-guess').inner_text()=='50,0%'
    assert page.locator('#s-rec').inner_text()=='100,0%';checks.append('no facts but full recovery')
    page.locator('[data-preset="path"]').click()
    assert page.locator('#s-guess').inner_text()=='100,0%'
    assert page.locator('#s-rec').inner_text()=='0,0%';checks.append('path readout')
    page.locator('[data-preset="y"]').click()
    assert page.locator('#s-rec').inner_text()=='60,0%';checks.append('Y counterexample')
    page.locator('#s-basis').select_option('custom');page.wait_for_timeout(80)
    assert page.locator('#custom-fields').is_visible();checks.append('custom axis')
    page.locator('[data-preset="phase"]').click()
    assert page.locator('#s-rec').inner_text()=='100,0%';checks.append('phase-sign regression')
    page.locator('#s-policy').select_option('none');page.wait_for_timeout(60)
    assert page.locator('#s-rec').inner_text()=='70,7%';checks.append('ignore measurement outcome')
    page.locator('[data-preset="phase"]').click()
    with page.expect_download() as dl:
        page.locator('#export-json').click()
    dl.value.save_as(ROOT/'results/browser_export.json')
    data=json.loads((ROOT/'results/browser_export.json').read_text())
    assert data['single']['corrected']['fidelity']>.999999;checks.append('JSON export')
    with page.expect_download() as dl:
        page.locator('#export-csv').click()
    dl.value.save_as(ROOT/'results/browser_export.csv')
    assert len((ROOT/'results/browser_export.csv').read_text(encoding='utf-8-sig').splitlines())==182;checks.append('CSV export')
    page.locator('#tab-many').click()
    page.locator('[data-preset="good-chain"]').click()
    assert page.locator('#m-local').inner_text()=='13,3%'
    assert page.locator('#m-chain').inner_text()=='80,4%';checks.append('many-witness default')
    page.locator('[data-preset="bad-chain"]').click()
    snap=page.evaluate('FenixApp.snapshot()')
    assert snap['many']['rows'][2]['coherence_factor']<snap['many']['rows'][1]['coherence_factor'];checks.append('bad CNOT chain loses')
    page.locator('[data-preset="boundary"]').click()
    assert page.locator('#m-local').inner_text()==page.locator('#m-chain').inner_text();checks.append('crossover')
    page.locator('#m-state').select_option('zero');page.wait_for_timeout(80)
    snap=page.evaluate('FenixApp.snapshot()')
    assert all(abs(row['fidelity']-1)<1e-12 for row in snap['many']['rows']);checks.append('V versus fidelity for |0>')
    page.locator('[data-preset="good-chain"]').click()
    page.locator('#m-n').fill('1000');page.wait_for_timeout(80)
    page.locator('#m-k').fill('800');page.locator('#m-k').dispatch_event('input')
    with page.expect_download() as dl: page.locator('#export-json').click()
    dl.value.save_as(ROOT/'results/large_fragment.json')
    page.locator('[data-preset="good-chain"]').click()
    page.locator('#import-file').set_input_files(ROOT/'results/large_fragment.json');page.wait_for_timeout(150)
    assert page.locator('#m-n').input_value()=='1000' and page.locator('#m-k').input_value()=='800';checks.append('import N and k beyond previous slider maximum')
    page.locator('[data-preset="good-chain"]').click()
    page.locator('#mc-shots').select_option('5000')
    page.locator('#run-mc').click()
    page.wait_for_function("document.querySelector('#mc-results').textContent.includes('Seed')")
    assert page.locator('#mc-results tbody tr').count()==3;checks.append('Monte Carlo')
    page.locator('#m-eps').fill('2');page.wait_for_timeout(80)
    assert page.locator('#mc-results tbody tr').count()==0;checks.append('stale Monte Carlo cleared')
    page.locator('#m-n').fill('0');page.wait_for_timeout(60)
    assert page.locator('#error-box').is_visible();checks.append('invalid input rejected')
    page.locator('[data-preset="good-chain"]').click()
    assert page.locator('#error-box').is_hidden()
    page.screenshot(path=str(ROOT/'results/ui_many.png'),full_page=True)
    page.locator('#tab-single').click();page.locator('[data-preset="phase"]').click()
    page.screenshot(path=str(ROOT/'results/ui_single.png'),full_page=True)
    page.locator('#tab-notes').click()
    assert page.locator('#test-list .pass').count()==14;checks.append('model and tests tab')
    for width in [390,768,1280]:
        page.set_viewport_size({'width':width,'height':900})
        for mode in ['single','many','notes']:
            page.locator('#tab-'+mode).click();page.wait_for_timeout(50)
            overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
            assert not overflow,(width,mode,'horizontal overflow')
        checks.append('responsive layout '+str(width))
    page.set_viewport_size({'width':390,'height':900});page.locator('#tab-single').click()
    page.screenshot(path=str(ROOT/'results/ui_mobile.png'),full_page=True)
    assert not errors,errors;assert not requests,requests
    checks.extend(['no JavaScript exceptions','no network requests'])
    browser.close()
result={'checks':len(checks),'passed':len(checks),'details':checks,'method':'Chromium, self-contained HTML via set_content; desktop and mobile viewports','network_requests':requests,'page_errors':errors}
(ROOT/'results/browser_smoke.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
