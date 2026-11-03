/* Unit tests for preference handling with a controlled browser environment.
   This does not claim a live browser-navigation or storage-permission test. */
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const catalogs={en:JSON.parse(fs.readFileSync(path.join(root,'i18n/en.json'))),ru:JSON.parse(fs.readFileSync(path.join(root,'i18n/ru.json')))};
let src=fs.readFileSync(path.join(root,'i18n.js'),'utf8')
 .replace('/* CATALOGS_INJECT */',JSON.stringify(catalogs))
 .replace('/* CORE_TRANSLATIONS_INJECT */',fs.readFileSync(path.join(root,'i18n/core_en.json'),'utf8'));
const results=[];
function test(name,fn){fn();results.push({name,pass:true});}
function load(store={},search='',blocked=false){
 const ctx={URLSearchParams,location:{search},document:{documentElement:{lang:''},querySelectorAll:()=>[]}};
 Object.defineProperty(ctx,'localStorage',{get(){if(blocked)throw new Error('blocked');return {getItem:k=>store[k]??null,setItem:(k,v)=>{store[k]=v;}};}});
 vm.createContext(ctx);vm.runInContext(src,ctx);return ctx.FenixI18n;
}
test('Default English',()=>assert.equal(load().getLanguage(),'en'));
test('Stored Russian choice',()=>assert.equal(load({'fenix-lab.language':'ru'}).getLanguage(),'ru'));
test('Unknown stored value ignored',()=>assert.equal(load({'fenix-lab.language':'xx'}).getLanguage(),'en'));
test('Explicit English URL wins',()=>assert.equal(load({'fenix-lab.language':'ru'},'?lang=en').getLanguage(),'en'));
test('Explicit Russian URL wins',()=>assert.equal(load({},'?lang=ru').getLanguage(),'ru'));
test('URL still works when storage is denied',()=>assert.equal(load({},'?lang=ru',true).getLanguage(),'ru'));
test('Denied storage defaults safely',()=>assert.equal(load({},'',true).getLanguage(),'en'));
test('Choice is written and reused on next initialisation',()=>{const store={};load(store).setLanguage('ru');assert.equal(load(store).getLanguage(),'ru');});
test('Switching works when storage is denied',()=>{const i=load({},'',true);i.setLanguage('ru');assert.equal(i.getLanguage(),'ru');});
test('Catalog fallback is deterministic',()=>assert.throws(()=>load().t('missing.key'),/Missing translation/));
test('Unsupported language is rejected',()=>assert.throws(()=>load().setLanguage('xx'),/Unsupported/));
test('Core error text is translated, parameter bounds retained',()=>assert.equal(load().coreText('Ошибка чтения: требуется число от 0 до 0.5'),'Readout error: enter a number from 0 to 0.5'));
test('Canonical export leaves numbers and keys intact',()=>{const out=load().canonical({x:.612,n:[3,4],label:'Некорректная матрица плотности'});assert.equal(out.x,.612);assert.equal(out.label,'Invalid density matrix');assert.deepEqual(Array.from(out.n),[3,4]);});
const report={checks:results.length,passed:results.length,method:'Node VM with mocked location, localStorage and DOM',results};
fs.writeFileSync(path.join(root,'results/i18n_runtime.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
