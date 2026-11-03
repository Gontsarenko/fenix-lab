"""Offline packaging and localisation checks; no third-party HTML parser required."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def test_catalog_keys_match_and_have_values():
    en=json.loads((ROOT/'i18n/en.json').read_text());ru=json.loads((ROOT/'i18n/ru.json').read_text())
    assert set(en)==set(ru)
    assert all(isinstance(s,str) and s for s in list(en.values())+list(ru.values()))
def test_english_catalog_has_no_untranslated_cyrillic():
    en=json.loads((ROOT/'i18n/en.json').read_text())
    assert not re.search('[А-Яа-яЁё]',''.join(en.values()))
def test_numerical_sources_unchanged():
    p=json.loads((ROOT/'docs/provenance.json').read_text())
    for name,expected in p['numerical_core_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected

def test_build_is_reproducible_and_has_no_missing_injections():
    before=(ROOT/'index.html').read_bytes()
    subprocess.run([sys.executable,'build.py'],cwd=ROOT,check=True,capture_output=True)
    after=(ROOT/'index.html').read_bytes()
    assert before==after
    assert b'_INJECT */' not in after
    assert b'<html lang="en">' in after

def test_all_static_and_dynamic_translation_keys_exist():
    keys=set(json.loads((ROOT/'i18n/en.json').read_text()))
    html=(ROOT/'app.template.html').read_text();js=(ROOT/'app_ui.js').read_text()
    refs=set(re.findall(r'data-i18n(?:-html|-title|-aria-label|-placeholder)?="([^"]+)"',html))
    refs.update(re.findall(r"trn\('([^']+)'\)",js))
    assert refs<=keys, refs-keys
