"""Build one fully offline bilingual HTML file. Python standard library only."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
catalogs={lang:json.loads((ROOT/'i18n'/f'{lang}.json').read_text(encoding='utf-8')) for lang in ('en','ru')}
if set(catalogs['en'])!=set(catalogs['ru']):
    raise ValueError('Translation catalogs must have identical keys')
# Prevent an embedded closing script token, even if one is accidentally put in a catalog.
def packed(data):return json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
i18n=(ROOT/'i18n.js').read_text(encoding='utf-8')
i18n=i18n.replace('/* CATALOGS_INJECT */',packed(catalogs))
i18n=i18n.replace('/* CORE_TRANSLATIONS_INJECT */',packed(json.loads((ROOT/'i18n/core_en.json').read_text(encoding='utf-8'))))
html=(ROOT/'app.template.html').read_text(encoding='utf-8')
for key in re.findall(r'data-i18n(?:-html|-title|-aria-label|-placeholder)?="([^"]+)"',html):
    if key not in catalogs['en']:raise ValueError(f'Missing translation key: {key}')
# Recompile the default English text and attributes, keeping build.py dependency-free.
# The checked-in template is already English; updated static translations should update
# its fallback text too. The runtime always applies the bundled catalogs on load.
html=html.replace('/* I18N_INJECT */',i18n)
html=html.replace('/* CORE_INJECT */',(ROOT/'fenix_core.js').read_text(encoding='utf-8'))
html=html.replace('/* UI_INJECT */',(ROOT/'app_ui.js').read_text(encoding='utf-8'))
(ROOT/'index.html').write_text(html,encoding='utf-8')
print(f'Built {ROOT / "index.html"} ({len(html.encode())} bytes; {len(catalogs["en"])} strings × 2 languages)')
