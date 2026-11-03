"""Compare the independent Python and JavaScript implementations numerically."""
import sys,json,subprocess,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import fenix_core as f
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(28176)
requests=[]; expected=[]
for _ in range(100):
    opts=dict(eta=float(rng.random()),phi=float(rng.random()*2*math.pi),theta=float(rng.random()*math.pi),
              basis=str(rng.choice(['family','z','path','x','y','custom'])),polar=float(rng.random()*math.pi),
              azimuth=float(rng.random()*2*math.pi),readout_error=float(rng.random()/2),phase_std=float(rng.random()),
              correction=str(rng.choice(['calibrated','nominal','none'])))
    r=f.single_witness(**opts)
    requests.append({'type':'single','opts':opts})
    expected.append([r['system']['visibility'],r['corrected']['visibility'],r['corrected']['fidelity'],r['environment']['knowledge_reported'],r['environment']['information_reported_bits']]+[x for row in r['corrected']['rho'] for c in row for x in (c.real,c.imag)])
for _ in range(40):
    opts=dict(n=int(rng.integers(1,2001)),eta=float(rng.random()),readout_error=float(rng.random()/2),gate_flip_error=float(rng.random()/2),collective_error=float(rng.random()/2),phase_std=float(rng.random()))
    r=f.recovery_comparison(f.RecoveryConfig(**opts))
    requests.append({'type':'many','opts':opts})
    expected.append([x for row in r['rows'] for x in [row['coherence_factor'],row['visibility'],row['fidelity']]]+[r['path_calibration']['ideal']['path_information_bits'],r['path_calibration']['noisy_X_readout']['p_guess']])
for k,eta in [(0,0),(60,.1),(374,.1),(1502,.05),(37586,.01),(100000,.001),(100000,.99)]:
    r=f.fragment_information(k,eta)
    requests.append({'type':'fragment','k':k,'eta':eta})
    expected.append([r['path_information_bits'],r['p_guess']])
js="""
const fs=require('fs'),F=require('./fenix_core.js');
const req=JSON.parse(fs.readFileSync(0,'utf8'));
const out=req.map(q=>{
 if(q.type==='single'){const r=F.single(q.opts);return[r.system.visibility,r.corrected.visibility,r.corrected.fidelity,r.environment.knowledge_reported,r.environment.information_reported_bits,...r.corrected.rho.flat(2)];}
 if(q.type==='many'){const r=F.many(q.opts);return[...r.rows.flatMap(x=>[x.coherence_factor,x.visibility,x.fidelity]),r.path_calibration.ideal.path_information_bits,r.path_calibration.noisy_X_readout.p_guess];}
 const r=F.fragment(q.k,q.eta);return[r.path_information_bits,r.p_guess];
});console.log(JSON.stringify(out));
"""
proc=subprocess.run(['node','-e',js],cwd=ROOT,input=json.dumps(requests),text=True,capture_output=True,check=True)
actual=json.loads(proc.stdout)
max_error=0
for i,(a,b) in enumerate(zip(actual,expected)):
    error=float(np.max(np.abs(np.array(a)-np.array(b))))
    max_error=max(max_error,error)
    if error>5e-10: raise AssertionError((i,requests[i],error,a,b))
result={'tests':len(requests),'passed':len(requests),'max_abs_difference':max_error,'seed':28176}
(ROOT/'results/cross_language.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
