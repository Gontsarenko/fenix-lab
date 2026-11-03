/* FENIX Lab 1.0.0. Source model: Gontsarenko, draft v1.4, 2026-11-02.
 * All angles are radians. Complex numbers = [real, imaginary].
 * Standalone numerical core, usable in browsers and Node; no dependencies.
 * Engineering extensions are explicitly listed in MODEL_NOTES_RU.md.
 */
(function(root,factory){const api=factory(); if(typeof module==='object'&&module.exports)module.exports=api;else root.Fenix=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const VERSION='1.0.0';
const C=(r=0,i=0)=>[r,i], add=(a,b)=>[a[0]+b[0],a[1]+b[1]], sub=(a,b)=>[a[0]-b[0],a[1]-b[1]], mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]], scale=(a,s)=>[a[0]*s,a[1]*s], conj=a=>[a[0],-a[1]], abs=a=>Math.hypot(a[0],a[1]), arg=a=>Math.atan2(a[1],a[0]), expi=x=>[Math.cos(x),Math.sin(x)];
const zero=()=>[[C(),C()],[C(),C()]], ident=()=>[[C(1),C()],[C(),C(1)]], plus=()=>[[C(.5),C(.5)],[C(.5),C(.5)]];
const madd=(a,b)=>a.map((row,i)=>row.map((v,j)=>add(v,b[i][j]))), mscale=(a,s)=>a.map(row=>row.map(v=>scale(v,s))), dag=a=>a[0].map((_,i)=>a.map(row=>conj(row[i]))), tr=a=>add(a[0][0],a[1][1]);
function mmul(a,b){return a.map(row=>b[0].map((_,j)=>row.reduce((s,v,k)=>add(s,mul(v,b[k][j])),C())));}
function bound(x,lo,hi,name){x=Number(x);if(!Number.isFinite(x)||x<lo||x>hi)throw new Error(name+': требуется число от '+lo+' до '+hi);return x;}
function integer(x,lo,hi,name){x=bound(x,lo,hi,name);if(!Number.isInteger(x))throw new Error(name+': требуется целое число');return x;}
function angle(x){x=Number(x);if(!Number.isFinite(x))throw new Error('Угол должен быть конечным');return x;}
const clamp=(x,lo=0,hi=1)=>Math.max(lo,Math.min(hi,x));
function det(a){return sub(mul(a[0][0],a[1][1]),mul(a[0][1],a[1][0]));}
function validateRho(a){if(!Array.isArray(a)||a.length!==2||a.some(r=>!Array.isArray(r)||r.length!==2||r.some(c=>!Array.isArray(c)||c.length!==2||c.some(v=>!Number.isFinite(v)))))throw new Error('Нужна конечная матрица 2×2');if(abs(sub(a[0][1],conj(a[1][0])))>1e-10||Math.abs(a[0][0][1])+Math.abs(a[1][1][1])>1e-10||Math.abs(tr(a)[0]-1)>1e-10||Math.min(a[0][0][0],a[1][1][0])<-1e-10||det(a)[0]<-1e-10)throw new Error('Некорректная матрица плотности');return a;}
function state(theta=Math.PI/2,phase=0,r=1){theta=angle(theta);phase=angle(phase);r=bound(r,0,1,'Радиус Блоха');const x=r*Math.sin(theta)*Math.cos(phase),y=r*Math.sin(theta)*Math.sin(phase),z=r*Math.cos(theta);return [[C((1+z)/2),C(x/2,-y/2)],[C(x/2,y/2),C((1-z)/2)]];}
function fidelity(a,b){return clamp(tr(mmul(a,b))[0]+2*Math.sqrt(Math.max(0,det(a)[0])*Math.max(0,det(b)[0])));}
function metrics(rho,target=plus()){return {visibility:clamp(2*abs(rho[0][1])),fidelity:fidelity(rho,target),bloch:[2*rho[0][1][0],-2*rho[0][1][1],rho[0][0][0]-rho[1][1][0]],purity:tr(mmul(rho,rho))[0],rho};}
function direction(phi,theta=0,basis='family',polar=0,azimuth=0){[phi,theta,polar,azimuth].forEach(angle);const d=[Math.sin(phi/2),-Math.cos(phi/2),0];switch(basis){case'family':return[d[0]*Math.sin(theta),d[1]*Math.sin(theta),Math.cos(theta)];case'z':return[0,0,1];case'path':return d;case'y':return[0,1,0];case'x':return[1,0,0];case'custom':return[Math.sin(polar)*Math.cos(azimuth),Math.sin(polar)*Math.sin(azimuth),Math.cos(polar)];default:throw new Error('Неизвестный базис');}}
function applyPhase(rho,phase){const d=[[C(1),C()],[C(),expi(phase)]];return mmul(mmul(d,rho),dag(d));}
function phaseNoise(rho,sigma){const out=rho.map(row=>row.map(v=>v.slice()));out[0][1]=scale(out[0][1],Math.exp(-sigma*sigma/2));out[1][0]=conj(out[0][1]);return out;}
function information(j){let result=0;const ps=j.map(r=>r.reduce((a,b)=>a+b,0)),po=j[0].map((_,i)=>j[0][i]+j[1][i]);for(let s=0;s<2;s++)for(let o=0;o<j[0].length;o++)if(j[s][o]>0)result+=j[s][o]*Math.log2(j[s][o]/(ps[s]*po[o]));return Math.max(0,result);}
function single(options={}){
 const p={eta:.6,phi:Math.PI,theta:0,basis:'family',polar:0,azimuth:0,readout_error:0,phase_std:0,correction:'calibrated',...options};
 p.eta=bound(p.eta,0,1,'η');p.readout_error=bound(p.readout_error,0,.5,'Ошибка чтения');p.phase_std=bound(p.phase_std,0,100,'σ');
 if(!['calibrated','nominal','none'].includes(p.correction))throw new Error('Неизвестный режим коррекции');
 const rho=validateRho(p.rho_in||plus()),n=direction(p.phi,p.theta,p.basis,p.polar,p.azimuth),env=[[C(.5),C(p.eta/2)],[C(p.eta/2),C(.5)]],u=[[C(1),C()],[C(),expi(p.phi)]];
 const env1=mmul(mmul(u,env),dag(u)),cross=mmul(env,dag(u));
 const projectors=[1,-1].map(sign=>[[C((1+sign*n[2])/2),C(sign*n[0]/2,-sign*n[1]/2)],[C(sign*n[0]/2,sign*n[1]/2),C((1-sign*n[2])/2)]]);
 const tau=[],factors=[],j=[[],[]];
 projectors.forEach(pr=>{const a=tr(mmul(pr,env))[0],b=tr(mmul(pr,env1))[0],t=tr(mmul(pr,cross));tau.push([[scale(rho[0][0],a),mul(rho[0][1],t)],[mul(rho[1][0],conj(t)),scale(rho[1][1],b)]]);factors.push(t);j[0].push(a/2);j[1].push(b/2);});
 const e=p.readout_error,reported=[0,1].map(i=>madd(mscale(tau[i],1-e),mscale(tau[1-i],e))),tf=[0,1].map(i=>add(scale(factors[i],1-e),scale(factors[1-i],e))),jr=j.map(row=>[0,1].map(i=>(1-e)*row[i]+e*row[1-i]));
 let out=zero();const outcomes=[];
 for(let i=0;i<2;i++){const f=p.correction==='nominal'?factors[i]:tf[i],phase=abs(f)>1e-14&&p.correction!=='none'?arg(f):0;const branch=applyPhase(reported[i],phase);out=madd(out,branch);const prob=tr(reported[i])[0],den=jr[0][i]+jr[1][i];outcomes.push({reported_label:i===0?'+':'−',probability:prob,path0_given_label_equal_priors:den>1e-14?jr[0][i]/den:null,correction_radians:phase,conditional_rho_unnormalized:reported[i],corrected_rho_unnormalized:branch});}
 if(p.correction!=='none')out=phaseNoise(out,p.phase_std);
 const k=jr[0].reduce((sum,a,i)=>sum+Math.abs(a-jr[1][i]),0),best=p.eta*Math.abs(Math.sin(p.phi/2));
 delete p.rho_in;
 return {mode:'single',parameters:p,input:metrics(rho,rho),system:metrics(madd(tau[0],tau[1]),rho),environment:{knowledge_reported:k,p_guess_reported:(1+k)/2,information_reported_bits:information(jr),knowledge_ideal_chosen:j[0].reduce((sum,a,i)=>sum+Math.abs(a-j[1][i]),0),helstrom_knowledge_ideal:best,p_guess_helstrom_ideal:(1+best)/2,conditional_states:[env,env1],equal_prior_calibration:true},corrected:metrics(out,rho),outcomes,bound_visibility_equal_superposition:p.eta>0?Math.sqrt(Math.max(0,1-(k/p.eta)**2)):1};
}
function h2(p){return p<=0||p>=1?0:-p*Math.log2(p)-(1-p)*Math.log2(1-p);}
function binomial(n,p){n=integer(n,0,100000,'n');p=bound(p,0,1,'p');const a=new Float64Array(n+1);if(p===0){a[0]=1;return a;}if(p===1){a[n]=1;return a;}const m=Math.min(n,Math.floor((n+1)*p));a[m]=1;for(let j=m;j>0;j--)a[j-1]=a[j]*j/(n-j+1)*(1-p)/p;for(let j=m;j<n;j++)a[j+1]=a[j]*(n-j)/(j+1)*p/(1-p);let sum=0;for(const v of a)sum+=v;for(let i=0;i<=n;i++)a[i]/=sum;return a;}
function fragment(k,eta,epsilon=0){k=integer(k,0,100000,'k');eta=bound(eta,0,1,'η');epsilon=bound(epsilon,0,.5,'Ошибка чтения');const eff=eta*(1-2*epsilon),a=binomial(k,(1+eff)/2);let conditional=0,pe=0;for(let j=0;j<=k;j++){const x=a[j],y=a[k-j],s=x+y;if(s>0)conditional+=s/2*h2(x/s);pe+=Math.min(x,y)/2;}return{k,eta,eta_effective:eff,readout_error:epsilon,path_information_bits:clamp(1-conditional),p_error:pe,p_guess:1-pe,knowledge:1-2*pe};}
function threshold(eta,target=.9,maxK=100000){eta=bound(eta,0,1,'η');target=bound(target,1e-12,1-1e-12,'Порог');maxK=integer(maxK,1,100000,'maxK');if(eta===0)return null;let lo=0,hi=1;while(fragment(hi,eta).path_information_bits<target){if(hi>=maxK)return null;lo=hi;hi=Math.min(maxK,hi*2);}while(hi-lo>1){const m=Math.floor((lo+hi)/2);if(fragment(m,eta).path_information_bits>=target)hi=m;else lo=m;}return hi;}
function checkedConfig(options={}){const p={n:100,eta:.6,readout_error:.01,gate_flip_error:.001,collective_error:.02,phase_std:0,...options};p.n=integer(p.n,1,100000,'N');p.eta=bound(p.eta,0,1,'η');for(const key of['readout_error','gate_flip_error','collective_error'])p[key]=bound(p[key],0,.5,key);p.phase_std=bound(p.phase_std,0,100,'σ');return p;}
function flipChannel(rho,factor){factor=bound(factor,-1,1,'Фактор когерентности');const z=[[C(1),C()],[C(),C(-1)]];return madd(mscale(rho,(1+factor)/2),mscale(mmul(mmul(z,rho),z),(1-factor)/2));}
function strategyRows(options={},rho=plus()){
 const p=checkedConfig(options);validateRho(rho);const n=p.n,e=p.readout_error,g=p.gate_flip_error,q=p.collective_error,phase=Math.exp(-(p.phase_std**2)/2);
 const defs=[['none',0,0,0,'paper'],['individual',(1-2*e)**n,n,0,'paper + optional Gaussian phase noise'],['concentrated',(1-2*e)*(1-2*g)**(n-1),1,n-1,'extension: target-X errors'],['collective',1-2*q,1,0,'extension: total collective-protocol error'],['ideal',1,1,0,'ideal benchmark; errors disabled']];
 return defs.map(([strategy,coh,readouts,cnot_count,model])=>{const factor=coh*(['none','ideal'].includes(strategy)?1:phase),out=flipChannel(rho,factor);return{strategy,coherence_factor:factor,factor_before_phase_noise:coh,residual_parity_error:(1-coh)/2,readouts,cnot_count,model,...metrics(out,rho),entanglement_fidelity:(1+factor)/2,average_pure_state_fidelity:(2+factor)/3};});
}
function many(options={},rho=plus()){
 const p=checkedConfig(options),ideal=fragment(p.n,p.eta),noisy=fragment(p.n,p.eta,p.readout_error);
 return{mode:'many_CZ',parameters:p,input:metrics(rho,rho),rows:strategyRows(p,rho),path_calibration:{ideal,noisy_X_readout:noisy,quantum_mutual_information_full_environment_plus_input:1+ideal.path_information_bits,different_measurement_than_recovery:true},threshold_gate_flip_error:p.n>1?p.readout_error:null};
}
function rngSeed(seed){let t=seed>>>0;return()=>{t+=0x6D2B79F5;let a=t;a=Math.imul(a^(a>>>15),a|1);a^=a+Math.imul(a^(a>>>7),a|61);return((a^(a>>>14))>>>0)/4294967296;};}
function cdfOf(pmf){let s=0;return Array.from(pmf,v=>s+=v);}
function sampleCDF(cdf,rng){const u=rng();let lo=0,hi=cdf.length-1;while(lo<hi){const mid=(lo+hi)>>>1;if(u<cdf[mid])hi=mid;else lo=mid+1;}return lo;}
function monteCarlo(options={},shots=20000,seed=20261102){
 const p=checkedConfig(options);shots=integer(shots,1,1000000,'shots');seed=integer(seed,0,4294967295,'seed');const rng=rngSeed(seed),cdfLocal=cdfOf(binomial(p.n,p.readout_error)),cdfGate=cdfOf(binomial(p.n-1,p.gate_flip_error));
 const theory=Object.fromEntries(strategyRows(p).map(r=>[r.strategy,r.coherence_factor])),results={};
 for(const strategy of['individual','concentrated','collective']){let sx=0,sy=0,sxx=0,bad=0;for(let i=0;i<shots;i++){let odd;if(strategy==='individual')odd=sampleCDF(cdfLocal,rng)%2;else if(strategy==='concentrated')odd=(sampleCDF(cdfGate,rng)+(rng()<p.readout_error?1:0))%2;else odd=rng()<p.collective_error?1:0;bad+=odd;let phase=0;if(p.phase_std>0)phase=p.phase_std*Math.sqrt(-2*Math.log(Math.max(Number.MIN_VALUE,rng())))*Math.cos(2*Math.PI*rng());const sign=1-2*odd,x=sign*Math.cos(phase),y=-sign*Math.sin(phase);sx+=x;sy+=y;sxx+=x*x;}const re=sx/shots,im=sy/shots,se=shots>1?Math.sqrt(Math.max(0,(sxx-sx*sx/shots)/(shots-1))/shots):null;results[strategy]={signed_quadrature:re,quadrature_imag:im,visibility_estimate:Math.hypot(re,im),standard_error_real:se,theory:theory[strategy],residual_flip_count:bad};}
 return{shots,seed,results,kind:'Синтетические испытания, не экспериментальные данные',generator:'Mulberry32; binomial inverse CDF; Box-Muller'};
}
function selfTests(){
 const results=[];const test=(name,fn)=>{try{fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false,message:e.message});}};
 const close=(a,b,tol=1e-11)=>{if(!Number.isFinite(a)||Math.abs(a-b)>tol)throw new Error(`${a} != ${b}`);};
 test('Таблица 1: η = 0, 0.6, 1',()=>{for(const eta of[0,.6,1]){const r=single({eta});close(r.system.visibility,0);close(r.corrected.visibility,1);close(r.environment.p_guess_helstrom_ideal,(1+eta)/2);}});
 test('Контрпример: Y-чтение даёт V = η',()=>{close(single({eta:.6,basis:'y'}).corrected.visibility,.6);});
 test('Регрессия знака: φ = π/2, Z-чтение',()=>{const r=single({phi:Math.PI/2,basis:'z'});close(r.corrected.visibility,1);close(r.corrected.fidelity,1);let wrong=zero();for(const o of r.outcomes)wrong=madd(wrong,applyPhase(o.conditional_rho_unnormalized,-o.correction_radians));close(2*abs(wrong[0][1]),0);});
 test('Неизвестная входная фаза сохраняется',()=>{const r=state(.8,.7,.8);close(single({phi:1.7,basis:'z',rho_in:r}).corrected.fidelity,1);});
 test('Измерение без коррекции не возвращает полосы',()=>{close(single({correction:'none'}).corrected.visibility,0);});
 test('Eq. (10): семейство насыщает границу',()=>{for(const theta of[0,.3,.9,1.4]){const r=single({eta:.6,phi:1.8,theta});close((r.environment.knowledge_reported/.6)**2+r.corrected.visibility**2,1);}});
 test('Eq. (8): N = 100, ε = 1%',()=>{close(strategyRows()[1].visibility,.98**100);});
 test('Порог цепочки p = ε',()=>{const r=strategyRows({n:100,readout_error:.01,gate_flip_error:.01});close(r[1].coherence_factor,r[2].coherence_factor);});
 test('η = 0: χN = 0, I(S:E) = 1',()=>{const r=many({eta:0});close(r.path_calibration.ideal.path_information_bits,0);close(r.path_calibration.quantum_mutual_information_full_environment_plus_input,1);});
 test('Пороги k₀.₉: 3, 9, 40, 92, 374',()=>{for(const [eta,k]of[[.9,3],[.6,9],[.3,40],[.2,92],[.1,374]])close(threshold(eta),k,0);});
 test('50% ошибок уничтожают информацию метки',()=>{const r=single({basis:'path',eta:1,readout_error:.5});close(r.environment.p_guess_reported,.5);close(r.corrected.visibility,0);});
 test('F не равно V: состояние |0⟩',()=>{for(const r of strategyRows({},state(0))){close(r.visibility,0);close(r.fidelity,1);}});
 test('Монте-Карло: воспроизводимый seed',()=>{const a=monteCarlo({},1000,812),b=monteCarlo({},1000,812);if(JSON.stringify(a)!==JSON.stringify(b))throw new Error('Seed mismatch');});
 test('Валидация отвергает η > 1',()=>{let threw=false;try{single({eta:1.1});}catch(_){threw=true;}if(!threw)throw new Error('No validation');});
 return{version:VERSION,total:results.length,passed:results.filter(r=>r.pass).length,results};
}
return{VERSION,single,many,strategyRows,fragment,threshold,monteCarlo,selfTests,state,metrics,direction,binomial,h2,plus,applyPhase,
 math:{C,add,sub,mul,scale,conj,abs,arg,expi,zero,ident,madd,mscale,mmul,dag,tr,det,validateRho,fidelity,flipChannel}};
});
