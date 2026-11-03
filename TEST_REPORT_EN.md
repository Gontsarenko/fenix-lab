# FENIX Lab 1.1 — verification report

This report concerns the supplied local build, not a deployed GitHub Pages site or hardware.
The numerical model is unchanged from release 1.0.0; release 1.1.0 adds bilingual presentation.

## Executed checks

| Suite | Result | Scope |
| --- | ---: | --- |
| Python / packaging | 25 / 25 | Original 20 numerical tests plus 5 localisation/build/integrity checks |
| JavaScript core self-tests | 14 / 14 | Existing numerical regression cases |
| Python–JavaScript comparison | 147 / 147 | Independent calculations; maximum absolute difference 1.5543122344752192e−15 |
| Localisation runtime | 13 / 13 | English default, stored preference, URL precedence, unavailable storage, canonical export descriptions |
| Bilingual browser regression | 81 / 81 | EN/RU, presets, controls, state retention, import/export, synthetic trials, errors and layout |
| Existing browser smoke suite | 23 / 23 | Original end-to-end scenarios, run in Russian after explicit language selection |

The sources `fenix_core.py` and `fenix_core.js` were compared with the v1.0 package:
both are **byte-for-byte identical**. See `results/core_integrity.json`.

## What the bilingual browser tests verify

The first visit opens in English even with a Russian browser locale. Switching EN/RU
preserves every experiment control, computed state, active mode and cached Monte Carlo
samples. It changes number presentation, not numerical values. Tests compare entire
calculated payloads, not just rounded labels.

Both new introductory buttons load the intended presets. All readout directions, recovery
presets and input-state choices work. English tabs, charts, explanations and live test names
contain no untranslated visible Russian text. Invalid input and malformed JSON are handled.
Imports restore parameters and recalculate while keeping the chosen UI language; old numeric
configuration format remains supported. JSON descriptions are canonical English in either UI language.

All three tabs were checked at 320, 390, 768, 1280 and 1440 pixels in both languages, with
no page-wide horizontal overflow. Numerical tables have their own horizontal scroll when needed.
No uncaught JavaScript errors or network requests occurred in the self-contained UI run.

## Environment limitation

The available managed Chromium blocks navigation to both `file://` and local HTTP URLs.
The browser suites therefore use Playwright `set_content` with the complete standalone HTML.
Language preference/URL logic is separately tested in Node with a **mocked** location,
localStorage and DOM, including denied-storage cases. This is not a claim that real browser
persistence across navigation was verified in this environment. The local-file delivery has
no remote assets or dependencies, and storage failure is handled without disabling the app.

## Reproduction

```bash
python build.py
python -m pip install -r requirements-dev.txt
python verify.py
python -m pip install playwright
python -m playwright install chromium
python tests/browser_i18n.py
python tests/browser_smoke.py
```

A missing optional Node.js is reported as a skipped check, not success. The browser suites
are separate from `verify.py`. They require a usable Chromium installation.

Reports: `results/verification_summary.json`, `results/cross_language.json`,
`results/js_self_tests.json`, `results/i18n_runtime.json`, `results/browser_i18n.json`,
`results/browser_smoke.json`. Commands and output are retained in the adjacent logs.

`SHA256SUMS.txt` describes the delivered files. Rebuilding an identical build is deterministic;
rerunning tests can update timestamps, machine details, screenshots and output hashes.
Passing these checks does not establish scientific novelty or validate performance on a device.
