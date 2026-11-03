/* FENIX Lab interface localisation. No calculation lives in this file.
 * build.py embeds reviewed local JSON catalogs; no remote translation service.
 */
(function (root) {
  'use strict';
  const catalogs = /* CATALOGS_INJECT */;
  const coreEnglish = /* CORE_TRANSLATIONS_INJECT */;
  const storageKey = 'fenix-lab.language';
  let language = 'en'; // Intentionally English on a first visit, not browser-language detection.
  let override = null;
  try { override = new URLSearchParams(root.location.search).get('lang'); } catch (_) {}
  if (override === 'en' || override === 'ru') language = override;
  else { try {
    const remembered = root.localStorage.getItem(storageKey);
    if (remembered === 'en' || remembered === 'ru') language = remembered;
  } catch (_) { /* Local files and private browsing may deny storage. */ } }
  function t(key, params = {}) {
    let value = catalogs[language][key] ?? catalogs.en[key];
    if (value === undefined) throw new Error('Missing translation: ' + key);
    return value.replace(/\{([A-Za-z0-9_]+)\}/g, (match, k) =>
      Object.prototype.hasOwnProperty.call(params, k) ? String(params[k]) : match);
  }
  function coreText(value, target = language) {
    const text = String(value);
    if (target === 'ru') return text;
    if (Object.prototype.hasOwnProperty.call(coreEnglish, text)) return coreEnglish[text];
    let match = text.match(/^(.*): требуется число от (.*) до (.*)$/);
    if (match) return coreText(match[1], target) + ': enter a number from ' + match[2] + ' to ' + match[3];
    match = text.match(/^(.*): требуется целое число$/);
    if (match) return coreText(match[1], target) + ': enter an integer';
    return text;
  }
  // Keep machine-readable exports in one canonical language; numbers and keys are untouched.
  function canonical(value) {
    if (Array.isArray(value)) return value.map(canonical);
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,canonical(v)]));
    return typeof value === 'string' ? coreText(value, 'en') : value;
  }
  function apply() {
    document.documentElement.lang = language;
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    // Only bundled, reviewed catalog markup is passed to innerHTML. Imported JSON is never markup.
    document.querySelectorAll('[data-i18n-html]').forEach(el => { el.innerHTML = t(el.dataset.i18nHtml); });
    for (const attr of ['title', 'aria-label', 'placeholder']) {
      document.querySelectorAll('[data-i18n-' + attr + ']').forEach(el => el.setAttribute(attr, t(el.getAttribute('data-i18n-' + attr))));
    }
    document.querySelectorAll('[data-language]').forEach(el => el.setAttribute('aria-pressed', String(el.dataset.language === language)));
  }
  function setLanguage(next, persist = true) {
    if (next !== 'en' && next !== 'ru') throw new Error('Unsupported interface language');
    language = next;
    if (persist) { try { root.localStorage.setItem(storageKey, language); } catch (_) {} }
    apply();
  }
  root.FenixI18n = Object.freeze({t,coreText,canonical,apply,setLanguage,
    getLanguage:()=>language,locale:()=>language==='ru'?'ru-RU':'en-US',
    keys:()=>Object.keys(catalogs.en)});
})(typeof globalThis === 'undefined' ? window : globalThis);
