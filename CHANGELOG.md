# Changelog

## 1.1.0 — 2026-11-03

- English on first use; EN/RU header switch, explicit language preference and URL override.
- Plain-language introduction: purpose, calculated quantities and model scope.
- Two audience-specific examples linked directly to existing experiment presets.
- Translated labels, plot text, explanations, validation and live test names.
- Language changes keep controls, computed outputs and existing Monte Carlo trials intact.
- Canonical English descriptions in browser JSON; numerical keys and CSV format stay stable.
- English documentation and mathematical specification; Russian documentation retained.
- Added catalog, runtime-preference and bilingual browser regression tests.
- Prevent stale delayed Monte Carlo output from being applied after the setup changes.
- Improved small-screen layout and tab keyboard navigation.

Numerical source files `fenix_core.py` and `fenix_core.js` are unchanged, including their
internal 1.0.0 version. This is an interface/documentation release, not a change of physics.
No external deployment, source-paper update, licence assignment or hardware validation is implied.

## 1.0.0 — 2026-11-02

Original Russian-language offline interface, two numerical cores, specified noise models,
examples and reproducibility tests, based on the supplied paper draft v1.4.
