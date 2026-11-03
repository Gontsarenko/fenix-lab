# FENIX Lab 1.1

**Lost interference. What can you recover?**

An offline, interactive calculator for quantum students, educators and protocol researchers.
Calculate fringe visibility, path-guessing probability and state fidelity; compare recovery
methods under explicitly specified readout and gate errors — without writing a simulation first.

**English by default · EN / RU switch · No installation · Local JSON / CSV export**

By **Sergei Gontsarenko**, ORCID [0009-0003-5377-9951](https://orcid.org/0009-0003-5377-9951).
A software companion to *Decoherence without facts: a one-knob model of where which-path
records live*, draft v1.4, 2 November 2026.

**Scope:** a research and teaching model, not a hardware benchmark, experimental data,
or a universal quantum-error corrector. The mathematical cores are unchanged from v1.0.0;
v1.1.0 adds bilingual presentation, introductory use cases and interface regression tests.

[Русская инструкция](README_RU.md) · [Model & assumptions](docs/MODEL_NOTES_EN.md) ·
[Verification report](TEST_REPORT_EN.md) · [Changelog](CHANGELOG.md)

![FENIX Lab — English interface](results/ui_en_landing.png)

## Open the calculator

Download the project, extract it and open **`index.html`** in a normal browser.
The separately supplied `FENIX_Lab_v1_1.html` is the same standalone file.
No Python, account, API key or network connection is required for the browser interface.

On a first visit the language is **English**, regardless of your browser language.
Use **EN / RU** in the header to switch. Settings, calculated states and any completed
Monte Carlo samples stay unchanged. Your explicit language choice is remembered when
local storage is available; a `?lang=en` or `?lang=ru` URL takes precedence.
Storage being blocked does not stop the calculator or language switch.

A managed browser may block local HTML files. An alternative, from this folder, is:

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8000/index.html`. This serves the file locally; all interface
calculations still happen in your browser.

The intended hosted address is `https://gontsarenko.github.io/fenix-lab/`.
This package does **not** enable GitHub Pages, upload files, or verify that this address is live.

## Two useful starting points

### For students and educators: understand a quantum eraser

**Question:** can interference return even when the environment does not reveal the path?

Choose **Try the recovery example** in the introduction. It loads η = 0, φ = π and Z readout.
In this ideal case, the system has no fringes before readout, path guessing remains at 50%,
and phase correction restores 100% visibility. Change the readout direction or introduce errors
to see why loss of interference, knowledge of the path and recoverability are separate questions.

### For protocol researchers: compare noisy recovery strategies

**Question:** is it better to read every environment qubit or first concentrate their parity?

Choose **Compare noisy protocols**. The starting scenario uses N = 100, a 1% individual
readout error and a 0.1% target-X error after each ideal CNOT. Compare visibility, state
fidelity, readout counts and CNOT counts; then increase the gate error and see when the
chain ceases to help. A collective-parity protocol is shown separately with its own total error.

These are comparisons **within the stated error model**, not recommendations for a particular
processor. A published general gate-infidelity value cannot simply be substituted for the
specified target-X error probability.

## What it calculates

### One witness

A controlled-phase interaction couples S to E, initially ρE = (I + ηX)/2.
The interface starts S in |+⟩. Choose the paper’s readout family, Z, X, Y,
the optimal path direction d, or a custom projective axis.

The three result panels show:

1. **System:** visibility before environment readout.
2. **Environment:** path-guessing success, advantage K and classical information in the recorded label.
3. **Correction:** visibility, squared fidelity and the actual final density matrix.

Corrected, unnormalised conditional matrices are added **before** final visibility is evaluated.
All measurement outcomes are kept. The optimal trade-off curve is a reference for the paper’s
single-witness assumptions, not a universal bound for all noisy devices.

The feedback selector can account for known readout error, use an ideal-device calibration,
or measure without applying a correction. Gaussian phase noise can be added after feedback.

### Errors and recovery

This mode fixes **φ = π** and uses N independently prepared witnesses. It compares:

| Method | Operation |
| --- | --- |
| No readout | Dephasing with no feedback |
| Individual Z readout | Read N labels and calculate their parity |
| CNOT chain → one readout | N−1 CNOT gates concentrate parity into one witness |
| Collective parity | A separate protocol with independently specified total error q |
| Ideal reference | Recovery with all errors disabled |

The chain’s gate error is an independent **X flip on the target after each ideal CNOT**.
It is not general two-qubit gate infidelity. The collective protocol is not assumed free:
q must represent its whole implementation. This interface holds q constant in the N scan.

Available input states include |+⟩, |+i⟩, |0⟩, a tilted pure state and a mixed state.
This makes the distinction between visibility and fidelity visible: |0⟩ can be perfectly
preserved even though its visibility is zero.

The fragment panel calculates path information in a **separate X-readout experiment**.
It does not perform incompatible path and parity measurements on the same copy.

## Language, export and reproducibility

The switch translates controls, descriptions, graph labels, result explanations, validation
messages and live test names. Numbers use English or Russian display formatting. JSON and
CSV retain stable machine-readable field names and decimal points; core-generated descriptive
strings in browser JSON exports are normalised to English.

**Export JSON** saves both configurations, states, assumptions and available Monte Carlo
results. **Import** restores settings and recalculates; it does not trust saved numerical answers.
Import keeps your current interface language. Version 1.0 configurations remain compatible.

**CSV** exports either the fringe scan or the protocol table (UTF-8 with BOM).
**Synthetic trials** use a reproducible seed. JavaScript uses Mulberry32 and Python uses
NumPy Generator; identical cross-language seeds do not promise identical random samples.
The final detector’s quantum shot noise is not included in these trials.

## Python API and verification

The browser app does not need Python. For the optional Python core:

```bash
python -m pip install -r requirements.txt
python fenix_core.py --mode single --eta 0 --basis z --epsilon 0 --out result.json
python fenix_core.py --mode many --n 100 --epsilon 0.01 --gate-error 0.001 --out compare.json
```

The numerical core still reports version **1.0.0**; the interface and software release are
**1.1.0**. This is intentional: numerical sources are byte-for-byte unchanged.
Browser JSON records both `version` and `core_version`.

```bash
python -m pip install -r requirements-dev.txt
python verify.py
```

With Node.js available this also runs JavaScript self-tests, numerical cross-language
comparisons and localisation preference tests. A missing optional tool is reported as skipped,
not passed. Browser regression tests additionally require Playwright and Chromium:

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/browser_i18n.py
python tests/browser_smoke.py
```

See `TEST_REPORT_EN.md` for what was actually run and the testing environment’s limitations.
The independent reference in `tests/reference_density.py` explicitly constructs full density
matrices for small N. Passing tests does not establish physical novelty or hardware performance.

## Build and modify the interface

```bash
python build.py
```

This embeds the mathematical core, UI, localisation runtime and both reviewed dictionaries
in one `index.html`. No JavaScript package manager or remote translation service is used.

| File | Purpose |
| --- | --- |
| `index.html` | Standalone English-first EN/RU app |
| `fenix_core.py`, `fenix_core.js` | Unmodified v1.0.0 numerical cores |
| `app.template.html`, `app_ui.js` | Interface layout and behaviour |
| `i18n.js`, `i18n/` | Language handling and EN/RU catalogs |
| `build.py` | Offline single-file build |
| `tests/`, `results/` | Reproducible tests and reports |
| `examples/` | Importable configurations and Python examples |
| `docs/` | Mathematical assumptions and provenance |
| `CITATION.cff` | Software citation metadata |

When adding a static translation, also update its English fallback in the HTML template.
Keep EN and RU catalog keys in sync. `build.py` validates keys; `verify.py` checks source
integrity and reproducible builds. Never put untrusted user-supplied markup into the catalogs.

## Authorship and status

Project author: **Sergei Gontsarenko**. Development and verification were AI-assisted.
The paper’s results and the calculator’s additional noise models are distinguished in the notes.
No source PDF or author verification script was modified by this release.

No software DOI is assigned in this package. Cite the repository and the precise version or
commit used. A licence has not yet been selected, and this package does not assign new usage terms.
