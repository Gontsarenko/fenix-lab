/* UI only: numerical definitions live in fenix_core.js. */
'use strict';
(() => {
const I18n=window.FenixI18n, trn=I18n.t;
I18n.apply();
const $=id=>document.getElementById(id), val=id=>Number($(id).value), deg=x=>x*Math.PI/180;
const fmt=(x,n=3)=>Number.isFinite(x)?(Math.abs(x)<.5*10**(-n)?0:x).toLocaleString(I18n.locale(),{minimumFractionDigits:n,maximumFractionDigits:n}):'—';
const pct=(x,n=1)=>fmt(100*x,n)+'%', radDeg=x=>fmt(x*180/Math.PI,1)+'°';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function strategyName(key){return {none:trn('d001'),individual:trn('d002'),concentrated:trn('d003'),collective:trn('d004'),ideal:trn('d005')}[key];}
let active='single',lastSingle=null,lastMany=null,lastMC=null,testReport=null,scheduled=null;
const ALL_IDS=['s-eta','s-phi','s-basis','s-theta','s-polar','s-azimuth','s-eps','s-sigma','s-policy','m-n','m-eta','m-eps','m-gate','m-parity','m-sigma','m-state','m-k','mc-shots','mc-seed'];
function note(text){$('message').textContent=text;$('message').hidden=false;clearTimeout(note.timer);note.timer=setTimeout(()=>$('message').hidden=true,4500);}
function error(e){$('error-box').textContent=e instanceof SyntaxError?trn('error.jsonParse'):I18n.coreText(e.message||String(e));$('error-box').hidden=false;}
function sParams(){return{eta:val('s-eta'),phi:deg(val('s-phi')),theta:deg(val('s-theta')),basis:$('s-basis').value,polar:deg(val('s-polar')),azimuth:deg(val('s-azimuth')),readout_error:val('s-eps')/100,phase_std:val('s-sigma'),correction:$('s-policy').value};}
function mParams(){return{n:val('m-n'),eta:val('m-eta'),readout_error:val('m-eps')/100,gate_flip_error:val('m-gate')/100,collective_error:val('m-parity')/100,phase_std:val('m-sigma')};}
function inputState(){switch($('m-state').value){case'plusi':return Fenix.state(Math.PI/2,Math.PI/2);case'zero':return Fenix.state(0);case'tilted':return Fenix.state(Math.PI/3,Math.PI/5);case'mixed':return Fenix.state(Math.PI/3,Math.PI/5,.7);default:return Fenix.plus();}}
function complex(z){const re=Math.abs(z[0])<5e-5?0:z[0],im=Math.abs(z[1])<5e-5?0:z[1];if(im===0)return fmt(re,4);if(re===0)return (im<0?'−':'')+fmt(Math.abs(im),4)+'i';return fmt(re,4)+(im<0?' − ':' + ')+fmt(Math.abs(im),4)+'i';}
function matrixHTML(title,m){return'<div class="matrix-box"><h4>'+esc(title)+'</h4><div class="matrix">'+m.flat().map(c=>'<span>'+complex(c)+'</span>').join('')+'</div></div>';}
function plot(id,{series,xmax=1,ymax=1,xlabel='',ylabel='',xticks=null,yticks=null,points=[],vline=null}){
 const w=520,h=258,l=48,r=16,t=14,b=44,iw=w-l-r,ih=h-t-b,X=x=>l+iw*x/xmax,Y=y=>t+ih*(1-y/ymax);
 xticks=xticks||[0,xmax/4,xmax/2,3*xmax/4,xmax];yticks=yticks||[0,ymax/2,ymax];let s=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(ylabel+trn('d006')+xlabel)}">`;
 for(const y of yticks)s+=`<line class="gridline" x1="${l}" y1="${Y(y)}" x2="${w-r}" y2="${Y(y)}"/><text class="tick" x="${l-9}" y="${Y(y)+4}" text-anchor="end">${fmt(y,y<2&&y%1?2:0)}</text>`;
 for(const x of xticks)s+=`<text class="tick" x="${X(x)}" y="${h-b+20}" text-anchor="middle">${fmt(x,xmax<=2&&x%1?2:0)}</text>`;
 s+=`<text class="tick" x="${l}" y="11">${esc(ylabel)}</text><text class="tick" x="${l+iw/2}" y="${h-3}" text-anchor="middle">${esc(xlabel)}</text>`;
 if(vline!=null)s+=`<line class="curve" x1="${X(vline)}" y1="${t}" x2="${X(vline)}" y2="${h-b}" stroke-width="1" opacity=".35" stroke-dasharray="3 5"/>`;
 series.forEach(line=>{const d=line.data.map(([x,y],i)=>(i?'L':'M')+X(x).toFixed(3)+','+Y(y).toFixed(3)).join(' ');s+=`<path class="curve" d="${d}" stroke-width="${line.width||2}" opacity="${line.opacity??1}" ${line.dash?`stroke-dasharray="${line.dash}"`:''}/>`;});
 for(const p of points)s+=`<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${p.r||4.5}" fill="currentColor"/><text x="${X(p.x)+(p.x>xmax*.75?-9:9)}" y="${Y(p.y)+(p.y>ymax*.85?18:-9)}" text-anchor="${p.x>xmax*.75?'end':'start'}">${esc(p.label||'')}</text>`;
 $(id).innerHTML=s+'</svg>';
}
function probability(rho,alpha){const c=rho[0][1];return .5+c[0]*Math.cos(alpha)-c[1]*Math.sin(alpha);}
function updateLabels(){for(const p of['s-eta','m-eta'])$(p+'-value').textContent=fmt(val(p),2);for(const p of['s-phi','s-theta','s-polar','s-azimuth'])$(p+'-value').textContent=fmt(val(p),0)+'°';$('s-eps-value').textContent=fmt(val('s-eps'),1)+'%';for(const p of['s-sigma','m-sigma'])$(p+'-value').textContent=fmt(val(p),2)+trn('d007');$('theta-field').hidden=$('s-basis').value!=='family';$('custom-fields').hidden=$('s-basis').value!=='custom';}
function renderSingle(){
 const p=sParams(),r=Fenix.single(p);lastSingle=r;
 $('s-raw').textContent=pct(r.system.visibility);$('s-raw-sub').textContent=trn('d008');
 $('s-guess').textContent=pct(r.environment.p_guess_reported);$('s-guess-sub').textContent=trn('d009')+pct(r.environment.p_guess_helstrom_ideal)+'.';
 $('s-rec').textContent=pct(r.corrected.visibility);$('s-rec-sub').textContent=trn('d010')+pct(r.corrected.fidelity)+'.';
 let meaning;
 if(p.correction==='none')meaning=trn('d011');
 else if(p.eta===0&&r.corrected.visibility>.98)meaning=trn('d012');
 else if(r.environment.knowledge_reported>.95)meaning=trn('d013');
 else if(p.basis==='y'&&Math.abs(p.phi-Math.PI)<1e-8)meaning=trn('d014');
 else meaning=trn('d015')+fmt(r.environment.knowledge_reported,3)+trn('d016')+fmt(r.corrected.visibility,3)+trn('d017');
 $('s-meaning').innerHTML=meaning;
 const scans=[r.input.rho,r.system.rho,r.corrected.rho].map(rho=>Array.from({length:181},(_,i)=>[2*i,probability(rho,deg(2*i))]));
 plot('fringe-chart',{series:[{data:scans[0],dash:'2 5',opacity:.45},{data:scans[1],dash:'8 5',opacity:.7},{data:scans[2],width:3}],xmax:360,ymax:1,xlabel:trn('d018'),ylabel:'P',xticks:[0,90,180,270,360]});
 const bestK=p.eta*Math.abs(Math.sin(p.phi/2));const bound=p.eta>0?Array.from({length:101},(_,i)=>{const k=bestK*i/100;return[k,Math.sqrt(Math.max(0,1-(k/p.eta)**2))];}):[[0,0],[0,1]];
 const circle=Array.from({length:101},(_,i)=>[i/100,Math.sqrt(Math.max(0,1-(i/100)**2))]);
 plot('trade-chart',{series:[{data:circle,dash:'2 5',opacity:.35},{data:bound,width:2.5}],points:[{x:r.environment.knowledge_reported,y:r.corrected.visibility,label:trn('d019')}],xmax:1.05,ymax:1.05,xlabel:trn('d020'),ylabel:'V',xticks:[0,.25,.5,.75,1],yticks:[0,.5,1]});
 $('outcome-rows').innerHTML=r.outcomes.map(o=>'<tr><td>'+o.reported_label+'</td><td>'+pct(o.probability,2)+'</td><td>'+(o.path0_given_label_equal_priors==null?'—':pct(o.path0_given_label_equal_priors,2))+'</td><td>'+radDeg(o.correction_radians)+'</td><td>'+complex(o.corrected_rho_unnormalized[0][1])+'</td></tr>').join('');
 $('single-info').textContent=trn('d021')+fmt(r.environment.information_reported_bits,4)+trn('d022')+fmt((1+p.eta*p.eta)/2,4)+trn('d023');
 $('single-matrices').innerHTML=matrixHTML(trn('d024'),r.input.rho)+matrixHTML(trn('d025'),r.system.rho)+matrixHTML(trn('d026'),r.corrected.rho);
}
function renderMany(){
 const p=mParams();if(p.n>2000)throw new Error(trn('d027'));const r=Fenix.many(p,inputState());lastMany=r;
 const local=r.rows[1],chain=r.rows[2],direct=r.rows[3];
 for(const [id,row]of[['local',local],['chain',chain],['direct',direct]]){$('m-'+id).textContent=pct(row.coherence_factor);$('m-'+id+'-sub').textContent='V = '+pct(row.visibility)+'; F = '+pct(row.fidelity)+'.';}
 const d=chain.coherence_factor-local.coherence_factor;let msg;
 if(p.n===1)msg=trn('d028');
 else if(p.readout_error===.5)msg=trn('d029');
 else if(p.gate_flip_error===p.readout_error)msg=trn('d030');
 else if(Math.abs(d)<1e-12)msg=trn('d031');
 else msg='<strong>'+(d>0?trn('d032'):trn('d033'))+trn('d034')+pct(p.gate_flip_error,3)+', ε = '+pct(p.readout_error,3)+'.';
 $('m-meaning').innerHTML=msg+trn('d035');
 const maxN=Math.max(100,Math.min(2000,Math.ceil(p.n*1.4))),ns=Array.from(new Set([1,p.n,...Array.from({length:100},(_,i)=>1+Math.round(i*(maxN-1)/99))])).sort((a,b)=>a-b),rows=ns.map(n=>Fenix.strategyRows({...p,n}));
 plot('recovery-chart',{series:[{data:rows.map((a,i)=>[ns[i],a[1].coherence_factor]),width:3},{data:rows.map((a,i)=>[ns[i],a[2].coherence_factor]),dash:'9 5'},{data:rows.map((a,i)=>[ns[i],a[3].coherence_factor]),dash:'2 5',opacity:.65}],xmax:maxN,ymax:1,xlabel:trn('d036'),ylabel:'C',xticks:[0,Math.round(maxN/4),Math.round(maxN/2),Math.round(3*maxN/4),maxN],vline:p.n});
 const best=Math.max(local.fidelity,chain.fidelity,direct.fidelity);
 $('strategy-rows').innerHTML=r.rows.map(row=>'<tr class="'+(row.strategy!=='ideal'&&row.strategy!=='none'&&Math.abs(row.fidelity-best)<1e-12?'best':'')+'"><td>'+strategyName(row.strategy)+(row.strategy==='concentrated'||row.strategy==='collective'?trn('d037'):'')+'</td><td>'+pct(row.visibility,2)+'</td><td>'+pct(row.fidelity,2)+'</td><td>'+(row.strategy==='none'?'—':pct(row.residual_parity_error,3))+'</td><td>'+(row.strategy==='collective'?trn('d038'):row.readouts)+'</td><td>'+(row.strategy==='collective'?trn('d039'):row.cnot_count)+'</td></tr>').join('');
 $('many-matrices').innerHTML=r.rows.slice(1,4).map(row=>matrixHTML(strategyName(row.strategy),row.rho)).join('');
 $('m-k').max=String(p.n);if(val('m-k')>p.n)$('m-k').value=String(p.n);renderFragment();
}
let thresholdCache=new Map();
function renderFragment(){
 const p=mParams(),k=val('m-k');$('m-k-value').textContent=k+' / '+p.n;
 const a=Fenix.fragment(k,p.eta),b=Fenix.fragment(k,p.eta,p.readout_error);
 $('fragment-chi').textContent=fmt(a.path_information_bits,4);$('fragment-noisy').textContent=fmt(b.path_information_bits,4);$('fragment-guess').textContent=pct(b.p_guess,2);
 let threshold=thresholdCache.get(p.eta);if(threshold===undefined){threshold=Fenix.threshold(p.eta);thresholdCache.set(p.eta,threshold);}
 const end=Fenix.fragment(p.n,p.eta),msg=threshold===null?(p.eta===0?trn('d040'):trn('d041')):(trn('d042')+threshold+(threshold>p.n?trn('d043'):'.'));
 $('fragment-extra').textContent=msg+trn('d044')+fmt(end.path_information_bits,4)+trn('d045')+fmt(1+end.path_information_bits,4)+trn('d046');
}
function render(){try{$('error-box').hidden=true;updateLabels();if(active==='single')renderSingle();else if(active==='many')renderMany();}catch(e){error(e);}}
function schedule(){if(scheduled)cancelAnimationFrame(scheduled);scheduled=requestAnimationFrame(()=>{scheduled=null;render();});}
function setTab(tab){if(!['single','many','notes'].includes(tab))return;active=tab;for(const el of document.querySelectorAll('[data-tab]'))el.setAttribute('aria-selected',String(el.dataset.tab===tab));for(const p of['single','many','notes'])$('panel-'+p).hidden=p!==tab;render();}
function resetMC(){lastMC=null;mcRevision++;renderMC();}
const presets={
 'no-facts':{tab:'single','s-eta':0,'s-phi':180,'s-basis':'z','s-theta':0,'s-eps':0,'s-sigma':0,'s-policy':'calibrated'},
 'path':{tab:'single','s-eta':1,'s-phi':180,'s-basis':'path','s-theta':90,'s-eps':0,'s-sigma':0,'s-policy':'calibrated'},
 'phase':{tab:'single','s-eta':.6,'s-phi':90,'s-basis':'z','s-theta':0,'s-eps':0,'s-sigma':0,'s-policy':'calibrated'},
 'y':{tab:'single','s-eta':.6,'s-phi':180,'s-basis':'y','s-eps':0,'s-sigma':0,'s-policy':'calibrated'},
 'good-chain':{tab:'many','m-n':100,'m-eta':.6,'m-eps':1,'m-gate':.1,'m-parity':2,'m-sigma':0,'m-state':'plus'},
 'bad-chain':{tab:'many','m-n':100,'m-eta':.6,'m-eps':.1,'m-gate':2,'m-parity':2,'m-sigma':0,'m-state':'plus'},
 'boundary':{tab:'many','m-n':100,'m-eta':.6,'m-eps':1,'m-gate':1,'m-parity':2,'m-sigma':0,'m-state':'plus'},
 'ideal-many':{tab:'many','m-n':100,'m-eta':0,'m-eps':0,'m-gate':0,'m-parity':0,'m-sigma':0,'m-state':'plus'}
};
function loadPreset(key, scroll=false){
 const p=presets[key]; if(!p)return;
 for(const [k,v] of Object.entries(p))if(k!=='tab')$(k).value=String(v);
 resetMC();setTab(p.tab);
 if(scroll){$('lab-tabs').scrollIntoView({behavior:'auto',block:'start'});$('tab-'+p.tab).focus({preventScroll:true});note(trn('launch.notice'));}
}
for(const b of document.querySelectorAll('[data-preset]'))b.addEventListener('click',()=>loadPreset(b.dataset.preset));
for(const b of document.querySelectorAll('[data-launch]'))b.addEventListener('click',()=>loadPreset(b.dataset.launch,true));
for(const b of document.querySelectorAll('[data-tab]'))b.addEventListener('click',()=>setTab(b.dataset.tab));
for(const id of ALL_IDS){$(id).addEventListener('input',()=>{if(id==='m-k'){try{renderFragment();}catch(e){error(e);}return;}if(id.startsWith('m-')||id.startsWith('mc-'))resetMC();schedule();});}
function renderTests(){
 if(!testReport)return;
 $('test-status').textContent='● '+testReport.passed+'/'+testReport.total+trn('d048');
 $('test-list').innerHTML=testReport.results.map(r=>'<div class="test-line"><span class="'+(r.pass?'pass':'fail')+'">'+(r.pass?'PASS':'FAIL')+'</span><span>'+esc(I18n.coreText(r.name))+(r.message?' — '+esc(I18n.coreText(r.message)):'')+'</span></div>').join('');
}
function runTests(){try{testReport=Fenix.selfTests();renderTests();if(testReport.passed!==testReport.total)error(new Error(trn('d049')));}catch(e){error(e);}}
$('run-tests').addEventListener('click',runTests);
let mcBusy=false, mcRevision=0;
function renderMC(){
 $('run-mc').disabled=mcBusy;$('run-mc').textContent=trn(mcBusy?'d050':'d053');
 if(!lastMC){$('mc-results').innerHTML='<p class="explain">'+trn('mc.empty')+'</p>';return;}
 const shots=lastMC.shots,seed=lastMC.seed;
 $('mc-results').innerHTML=trn('d051')+Object.entries(lastMC.results).map(([key,r])=>'<tr><td>'+strategyName(key)+'</td><td>'+fmt(r.theory,5)+'</td><td>'+fmt(r.signed_quadrature,5)+'</td><td>'+fmt(2*r.standard_error_real,5)+'</td><td>'+r.residual_flip_count+' / '+shots+'</td></tr>').join('')+'</tbody></table></div><p class="explain">Seed '+seed+trn('d052');
}
$('run-mc').addEventListener('click',()=>{try{
 const params=mParams();Fenix.many(params);const shots=val('mc-shots'),seed=val('mc-seed'),revision=mcRevision;
 mcBusy=true;renderMC();setTimeout(()=>{try{const result=Fenix.monteCarlo(params,shots,seed);if(revision===mcRevision)lastMC=result;}catch(e){error(e);}finally{mcBusy=false;renderMC();}},20);
}catch(e){error(e);}});
function download(name,text,type){const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);}
function snapshot(){const sp=sParams(),mp=mParams();const source={title:'Decoherence without facts: a one-knob model of where which-path records live',author:'Sergei Gontsarenko',version:'draft v1.4',date:'2026-11-02',sections:['2','4','5','6','9']};return{software:'FENIX Lab',version:'1.1.0',core_version:Fenix.VERSION,interface_language:I18n.getLanguage(),created_utc:new Date().toISOString(),source,active_tab:active,ui_state:Object.fromEntries(ALL_IDS.map(id=>[id,$(id).value])),single:Fenix.single(sp),many:Fenix.many(mp,inputState()),monte_carlo:lastMC,browser_tests:testReport,model_notes:{single_readout_error:'Symmetric classical bit flip after ideal projective measurement.',gate_error:'Independent target-X after each perfect CNOT; not general gate infidelity.',collective_error:'Independent total parity-protocol error, not inferred from individual readout.',phase_error:'Independent zero-mean Gaussian phase after feedback; not from the article.',path_vs_recovery:'Path calibration and parity recovery are alternative experiments.',postselection:false,experimental_data:false}};}
$('export-json').addEventListener('click',()=>{try{download('fenix_experiment.json',JSON.stringify(I18n.canonical(snapshot()),null,2),'application/json');note(trn('d054'));}catch(e){error(e);}});
function csv(rows){return '\ufeff'+rows.map(row=>row.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\r\n');}
$('export-csv').addEventListener('click',()=>{try{let rows;if(active==='many'){const p=mParams(),r=Fenix.many(p,inputState());rows=[['strategy','N','eta','readout_error','gate_X_error','collective_error','phase_std_rad','coherence_factor','visibility','fidelity','parity_error_before_phase_noise','readouts','cnot_count'],...r.rows.map(x=>[x.strategy,p.n,p.eta,p.readout_error,p.gate_flip_error,p.collective_error,p.phase_std,x.coherence_factor,x.visibility,x.fidelity,x.residual_parity_error,x.readouts,x.strategy==='collective'?'unspecified':x.cnot_count])];}else{const r=Fenix.single(sParams());rows=[['scan_phase_deg','P_input','P_before','P_corrected','eta','phi_rad','theta_rad','basis','readout_error','phase_std','correction','K','P_guess'],...Array.from({length:181},(_,i)=>[i*2,probability(r.input.rho,deg(i*2)),probability(r.system.rho,deg(i*2)),probability(r.corrected.rho,deg(i*2)),r.parameters.eta,r.parameters.phi,r.parameters.theta,r.parameters.basis,r.parameters.readout_error,r.parameters.phase_std,r.parameters.correction,r.environment.knowledge_reported,r.environment.p_guess_reported])];}download('fenix_'+active+'.csv',csv(rows),'text/csv;charset=utf-8');}catch(e){error(e);}});
$('import-json').addEventListener('click',()=>$('import-file').click());
$('import-file').addEventListener('change',async()=>{const file=$('import-file').files[0];if(!file)return;const old=Object.fromEntries(ALL_IDS.map(id=>[id,$(id).value]));try{if(file.size>3000000)throw new Error(trn('d055'));const data=JSON.parse(await file.text());if(data.software!=='FENIX Lab'||!data.ui_state)throw new Error(trn('d056'));const importedN=Number(data.ui_state['m-n']??$('m-n').value);if(!Number.isInteger(importedN)||importedN<1||importedN>2000)throw new Error(trn('d057'));$('m-k').max=String(importedN);for(const id of ALL_IDS){if(!Object.prototype.hasOwnProperty.call(data.ui_state,id))continue;const el=$(id),v=String(data.ui_state[id]);if(el.tagName==='SELECT'){if(!Array.from(el.options).some(o=>o.value===v))throw new Error(trn('d058')+id);}else{const num=Number(v);if(!Number.isFinite(num)||num<Number(el.min)||num>Number(el.max)||((id==='m-n'||id==='m-k'||id==='mc-seed')&&!Number.isInteger(num)))throw new Error(trn('d059')+id);}el.value=v;}Fenix.single(sParams());Fenix.many(mParams(),inputState());resetMC();setTab(['single','many','notes'].includes(data.active_tab)?data.active_tab:'single');note(trn('d060'));}catch(e){$('m-k').max=old['m-n'];for(const [id,v]of Object.entries(old))$(id).value=v;render();error(e);}finally{$('import-file').value='';}});
// Test harness access is read-only with respect to files, network and DOM code.
function changeLanguage(language){
 I18n.setLanguage(language);renderTests();renderMC();render();note(trn('language.notice'));
}
for(const button of document.querySelectorAll('[data-language]'))button.addEventListener('click',()=>changeLanguage(button.dataset.language));
// Arrow-key navigation follows the tablist order.
const tabs=['single','many','notes'];
for(const tab of tabs)$('tab-'+tab).addEventListener('keydown',event=>{
 const i=tabs.indexOf(tab);let j=null;
 if(event.key==='ArrowRight')j=(i+1)%tabs.length;else if(event.key==='ArrowLeft')j=(i+tabs.length-1)%tabs.length;else if(event.key==='Home')j=0;else if(event.key==='End')j=tabs.length-1;
 if(j!==null){event.preventDefault();setTab(tabs[j]);$('tab-'+tabs[j]).focus();}
});
window.FenixApp={snapshot,setTab,render,loadPreset,setLanguage:changeLanguage,language:I18n.getLanguage,activeTab:()=>active};
runTests();renderMC();render();
})();
