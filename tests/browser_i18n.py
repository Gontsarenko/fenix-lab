"""Browser regression checks for English/Russian UI, real calculations and offline use.
Requires Playwright + Chromium. Does not access any remote website.
"""
from pathlib import Path
import json,re,shutil,zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
checks=[];errors=[];requests=[]
def check(name, condition=True):
    assert condition,name
    checks.append(name)
def values(page):
    return page.evaluate('FenixApp.snapshot().ui_state')
def payload(page):
    return page.evaluate('(()=>{const s=FenixApp.snapshot();return {single:s.single,many:s.many,mc:s.monte_carlo,ui:s.ui_state,tab:s.active_tab};})()')
def healthy(page):
    assert page.locator('#error-box').is_hidden(),page.locator('#error-box').inner_text()
def english_only(page):
    text=page.locator('body').inner_text()
    assert not re.search('[А-Яа-яЁё]',text),re.findall('.{0,20}[А-Яа-яЁё].{0,40}',text)

en=json.loads((ROOT/'i18n/en.json').read_text());ru=json.loads((ROOT/'i18n/ru.json').read_text())
check('EN and RU catalogs have matching keys',set(en)==set(ru))
check('English catalog has no untranslated Cyrillic',not re.search('[А-Яа-яЁё]',''.join(en.values())))
with sync_playwright() as p:
    exe=shutil.which('chromium') or p.chromium.executable_path
    browser=p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1080},accept_downloads=True,locale='ru-RU')
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url))
    page.set_content((ROOT/'index.html').read_text(),wait_until='load')
    healthy(page);english_only(page)
    check('First visit is English even in a Russian browser',page.locator('html').get_attribute('lang')=='en')
    check('Live numerical checks pass', '14/14' in page.locator('#test-status').inner_text())
    check('English number formatting',page.locator('#s-rec').inner_text()=='100.0%')
    check('Both use-case introductions are present',page.locator('[data-launch]').count()==2)
    page.screenshot(path=str(OUT/'ui_en_landing.png'))
    page.locator('[data-launch="no-facts"]').click();healthy(page)
    check('Teaching entry loads the recovery example',page.locator('#s-eta').input_value()=='0' and page.locator('#s-basis').input_value()=='z')
    check('Teaching example is 0% / 50% / 100%', [page.locator('#s-'+k).inner_text() for k in ['raw','guess','rec']]==['0.0%','50.0%','100.0%'])
    page.locator('#s-eps').fill('2.3');page.locator('#s-eps').dispatch_event('input');page.wait_for_timeout(80)
    before=payload(page);page.locator('#lang-ru').click();healthy(page)
    check('RU switch preserves all settings and computed outputs',before==payload(page))
    check('Russian document language and status',page.locator('html').get_attribute('lang')=='ru' and 'проверок' in page.locator('#test-status').inner_text())
    page.locator('#lang-en').click();healthy(page);english_only(page)
    check('EN round trip preserves settings and outputs',before==payload(page))
    # Every one-witness preset in both languages, with the same numerical answers.
    expected={'no-facts':(0,.5,1),'path':(0,1,0),'phase':(2**-.5,.5,1),'y':(0,.5,.6)}
    for lang in ['en','ru']:
      page.locator('#lang-'+lang).click()
      for preset,(raw,guess,rec) in expected.items():
        page.locator('[data-preset="'+preset+'"]').click();healthy(page)
        q=payload(page)['single'];check(f'{lang}: preset {preset}',abs(q['system']['visibility']-raw)<1e-12 and abs(q['environment']['p_guess_reported']-guess)<1e-12 and abs(q['corrected']['visibility']-rec)<1e-12)
      for basis in ['family','z','path','y','x','custom']:
        page.locator('#s-basis').select_option(basis);page.wait_for_timeout(35);healthy(page)
      check(f'{lang}: all six readout choices work')
    page.locator('#lang-en').click();page.locator('[data-preset="phase"]').click()
    page.locator('#s-policy').select_option('none');page.wait_for_timeout(60);healthy(page)
    check('Measuring without correction retains the uncorrected state',page.locator('#s-rec').inner_text()=='70.7%')
    page.locator('[data-preset="phase"]').click()
    with page.expect_download() as dl:page.locator('#export-json').click()
    dl.value.save_as(OUT/'browser_export_en.json');e=json.loads((OUT/'browser_export_en.json').read_text())
    check('JSON exports application and numerical-core versions separately',e['version']=='1.1.0' and e['core_version']=='1.0.0')
    check('JSON descriptions are canonical English',not re.search('[А-Яа-яЁё]',json.dumps(e,ensure_ascii=False)))
    with page.expect_download() as dl:page.locator('#export-csv').click()
    dl.value.save_as(OUT/'browser_export.csv')
    check('Fringe CSV contains all scan points',len((OUT/'browser_export.csv').read_text(encoding='utf-8-sig').splitlines())==182)
    before=payload(page);page.locator('#lang-ru').click()
    with page.expect_download() as dl:page.locator('#export-json').click()
    dl.value.save_as(OUT/'browser_export_ru.json');r=json.loads((OUT/'browser_export_ru.json').read_text())
    check('RU export uses the same numerical payload and canonical descriptions',r['single']==e['single'] and r['many']==e['many'] and not re.search('[А-Яа-яЁё]',json.dumps(r,ensure_ascii=False)))
    page.locator('[data-preset="path"]').click()
    page.locator('#import-file').set_input_files(OUT/'browser_export_en.json');page.wait_for_timeout(120);healthy(page)
    check('Import preserves the chosen UI language',page.locator('html').get_attribute('lang')=='ru')
    check('Import restores settings and recalculates',payload(page)['single']==before['single'])
    page.locator('#lang-en').click()
    page.locator('#import-file').set_input_files({'name':'broken.json','mimeType':'application/json','buffer':b'{broken'})
    page.wait_for_timeout(80)
    check('Malformed JSON has an English error message',page.locator('#error-box').is_visible() and 'Invalid JSON' in page.locator('#error-box').inner_text())
    page.locator('[data-launch="good-chain"]').click();healthy(page)
    check('Protocol entry opens the comparison',page.locator('#panel-many').is_visible())
    check('Default error comparison preserved',page.locator('#m-local').inner_text()=='13.3%' and page.locator('#m-chain').inner_text()=='80.4%' and page.locator('#m-direct').inner_text()=='96.0%')
    for preset in ['good-chain','bad-chain','boundary','ideal-many']:
      page.locator('[data-preset="'+preset+'"]').click();healthy(page);before=payload(page)
      page.locator('#lang-ru').click();healthy(page);check(f'Comparison preset {preset} is language-invariant',before==payload(page))
      page.locator('#lang-en').click()
    page.locator('[data-preset="bad-chain"]').click();q=payload(page)['many']['rows']
    check('Noisy CNOT chain can lose',q[2]['coherence_factor']<q[1]['coherence_factor'])
    page.locator('[data-preset="good-chain"]').click()
    for state in ['plus','plusi','zero','tilted','mixed']:
      page.locator('#m-state').select_option(state);page.wait_for_timeout(35);healthy(page)
    check('All five input-state choices work')
    page.locator('#m-state').select_option('zero');page.wait_for_timeout(60)
    check('State fidelity is distinguished from visibility',all(abs(x['fidelity']-1)<1e-12 and x['visibility']<1e-12 for x in payload(page)['many']['rows']))
    page.locator('[data-preset="good-chain"]').click()
    page.locator('#m-n').fill('1000');page.wait_for_timeout(80)
    page.locator('#m-k').fill('800');page.locator('#m-k').dispatch_event('input');page.wait_for_timeout(50)
    with page.expect_download() as dl:page.locator('#export-json').click()
    dl.value.save_as(OUT/'large_fragment.json');page.locator('[data-preset="good-chain"]').click()
    page.locator('#import-file').set_input_files(OUT/'large_fragment.json');page.wait_for_timeout(120);healthy(page)
    check('Large-fragment import updates the slider limit',page.locator('#m-n').input_value()=='1000' and page.locator('#m-k').input_value()=='800')
    page.locator('[data-preset="good-chain"]').click();page.locator('#mc-shots').select_option('5000')
    page.locator('#run-mc').click();page.wait_for_function("document.querySelectorAll('#mc-results tbody tr').length===3")
    mc=payload(page)['mc'];check('Seeded synthetic trials run',mc is not None)
    page.locator('#lang-ru').click();healthy(page)
    check('Changing language keeps Monte Carlo samples',payload(page)['mc']==mc and page.locator('#mc-results tbody tr').count()==3)
    page.locator('#lang-en').click();english_only(page);check('Monte Carlo output is translated back to English')
    page.locator('#m-eps').fill('2');page.wait_for_timeout(60)
    check('Changing physics parameters invalidates old trials',payload(page)['mc'] is None and page.locator('#mc-results tbody tr').count()==0)
    page.locator('#m-n').fill('0');page.wait_for_timeout(60)
    check('Invalid input is rejected in English',page.locator('#error-box').is_visible() and not re.search('[А-Яа-яЁё]',page.locator('#error-box').inner_text()))
    page.locator('#lang-ru').click()
    check('Validation messages follow the language',bool(re.search('[А-Яа-яЁё]',page.locator('#error-box').inner_text())))
    page.locator('[data-preset="good-chain"]').click();healthy(page)
    page.locator('#lang-en').click()
    # Every visible mode is English, including plots, definitions and live test names.
    for mode in ['single','many','notes']:
      page.locator('#tab-'+mode).click();healthy(page);english_only(page)
      check(f'No untranslated visible Russian text in English {mode} mode')
    page.locator('#tab-single').focus();page.keyboard.press('ArrowRight')
    check('Keyboard tab navigation',page.locator('#panel-many').is_visible())
    # Desktop and narrow layouts in both languages, all tabs.
    for lang in ['en','ru']:
      page.locator('#lang-'+lang).click()
      for width in [320,390,768,1280,1440]:
        page.set_viewport_size({'width':width,'height':960})
        for mode in ['single','many','notes']:
          page.locator('#tab-'+mode).click();page.wait_for_timeout(30);healthy(page)
          check(f'No page overflow: {lang}, {width}px, {mode}',not page.evaluate('document.documentElement.scrollWidth > innerWidth + 2'))
      page.set_viewport_size({'width':1440,'height':1080});page.locator('#tab-single').click();page.evaluate('scrollTo(0,0)')
      page.screenshot(path=str(OUT/f'ui_{lang}_landing.png'))
      page.locator('[data-launch="good-chain"]').click();page.screenshot(path=str(OUT/f'ui_{lang}_many.png'))
      page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)')
      page.screenshot(path=str(OUT/f'ui_{lang}_mobile.png'),full_page=True)
    check('No uncaught JavaScript errors',not errors)
    check('Self-contained app makes no network requests',not requests)
    page.close()
    browser.close()
result={'file_navigation_note':'Managed Chromium blocks file and HTTP navigation. Browser UI is tested with set_content; language persistence and URL selection are tested separately with a mocked browser environment in tests/i18n_runtime.test.js.', 'checks':len(checks),'passed':len(checks),'details':checks,'method':'Chromium; offline set_content; EN/RU; 320–1440px','network_requests':requests,'page_errors':errors}
(OUT/'browser_i18n.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
