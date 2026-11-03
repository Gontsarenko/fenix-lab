"""FENIX Lab 1.0: source-grounded decoherence and recovery simulator.

Source: Sergei Gontsarenko, Decoherence without facts, draft v1.4,
2 November 2026, sections 2, 4, 5, 6, 9. No experimental data.

Article model: independent E qubits (I+eta X)/2 and controlled phases.
Added engineering models (explicitly NOT claims of the paper): symmetric
classical label errors; independent target-X errors after accumulator CNOTs;
a separately specified error of a collective parity protocol; independent
zero-mean Gaussian phase error of feed-forward.

All states are density matrices, with the system the most significant qubit.
Visibility is calculated from the final summed density matrix, not from the
sum of absolute values of individual branch coherences.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
from typing import Any, Literal
import numpy as np

VERSION = '1.0.0'
SOURCE = 'Gontsarenko, Decoherence without facts, draft v1.4, 2026-11-02'
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1, -1]).astype(complex)
PLUS = np.ones((2, 2), complex) / 2


def bounded(x: float, lo: float, hi: float, name: str) -> float:
    x = float(x)
    if not math.isfinite(x) or not lo <= x <= hi:
        raise ValueError(f'{name} must be finite and in [{lo}, {hi}].')
    return x


def count(x: int, lo: int, hi: int, name: str) -> int:
    if isinstance(x, bool) or not math.isfinite(float(x)) or int(x) != x or not lo <= int(x) <= hi:
        raise ValueError(f'{name} must be an integer in [{lo}, {hi}].')
    return int(x)


def density(rho: np.ndarray) -> np.ndarray:
    r = np.asarray(rho, dtype=complex)
    if r.shape != (2, 2) or not np.isfinite(r).all():
        raise ValueError('A finite 2x2 density matrix is required.')
    if not np.allclose(r, r.conj().T, atol=1e-11, rtol=0):
        raise ValueError('Density matrix is not Hermitian.')
    if abs(np.trace(r) - 1) > 1e-10 or np.linalg.eigvalsh(r).min() < -1e-10:
        raise ValueError('Density matrix must have unit trace and be positive semidefinite.')
    return r.copy()


def state(theta: float = math.pi/2, phase: float = 0., bloch_radius: float = 1.) -> np.ndarray:
    """Bloch radius `bloch_radius` (not Tr rho^2), polar theta and azimuth phase."""
    r = bounded(bloch_radius, 0, 1, 'Bloch radius')
    for v in (theta, phase):
        if not math.isfinite(float(v)):
            raise ValueError('Angles must be finite radians.')
    b = r*np.array([math.sin(theta)*math.cos(phase), math.sin(theta)*math.sin(phase), math.cos(theta)])
    return (I2+b[0]*X+b[1]*Y+b[2]*Z)/2


def fidelity(a: np.ndarray, b: np.ndarray) -> float:
    """Squared Uhlmann fidelity for normalized qubit density matrices."""
    a, b = density(a), density(b)
    f = np.trace(a@b).real + 2*math.sqrt(max(0., np.linalg.det(a).real)*max(0., np.linalg.det(b).real))
    return float(np.clip(f, 0, 1))


def metrics(rho: np.ndarray, target: np.ndarray = PLUS) -> dict:
    rho = density(rho)
    return {'visibility': float(2*abs(rho[0,1])), 'fidelity': fidelity(rho, target),
            'bloch': [float(2*rho[0,1].real), float(-2*rho[0,1].imag), float((rho[0,0]-rho[1,1]).real)],
            'purity': float(np.trace(rho@rho).real), 'rho': rho}


def direction(phi: float, theta: float = 0., basis: str = 'family',
              polar: float = 0., azimuth: float = 0.) -> np.ndarray:
    """Projective measurement direction. All angles in radians."""
    if not all(math.isfinite(float(v)) for v in (phi, theta, polar, azimuth)):
        raise ValueError('Angles must be finite.')
    d = np.array([math.sin(phi/2), -math.cos(phi/2), 0.])
    if basis == 'family': return math.sin(theta)*d+np.array([0.,0.,math.cos(theta)])
    if basis == 'z': return np.array([0.,0.,1.])
    if basis == 'path': return d
    if basis == 'y': return np.array([0.,1.,0.])
    if basis == 'x': return np.array([1.,0.,0.])
    if basis == 'custom': return np.array([math.sin(polar)*math.cos(azimuth), math.sin(polar)*math.sin(azimuth), math.cos(polar)])
    raise ValueError('Unknown basis.')


def classical_information(joints: np.ndarray) -> float:
    p = np.asarray(joints, float)
    ps, po = p.sum(axis=1), p.sum(axis=0)
    total = 0.
    for s in range(2):
        for o in range(p.shape[1]):
            if p[s,o] > 0:
                total += p[s,o]*math.log2(p[s,o]/(ps[s]*po[o]))
    return float(max(0, total))


def _phase_noise(rho: np.ndarray, sigma: float) -> np.ndarray:
    out = rho.copy()
    out[0,1] *= math.exp(-sigma*sigma/2)
    out[1,0] = out[0,1].conjugate()
    return out


def single_witness(eta: float = .6, phi: float = math.pi, theta: float = 0.,
                   basis: str = 'family', polar: float = 0., azimuth: float = 0.,
                   readout_error: float = 0., phase_std: float = 0.,
                   correction: Literal['calibrated','nominal','none'] = 'calibrated',
                   rho_in: np.ndarray | None = None) -> dict:
    """Exact S+E calculation, followed by a classical confusion channel.

    `calibrated`: phases derived from the reported (noisy) instrument;
    `nominal`: phases calibrated as if labels were perfect;
    `none`: retain all outcomes but do not apply correction.
    Calibration uses channel factors, never the unknown system phase.
    K and information use equal-prior path calibration, even for rho_in != |+>.
    """
    eta = bounded(eta, 0, 1, 'eta')
    eps = bounded(readout_error, 0, .5, 'readout_error')
    sigma = bounded(phase_std, 0, 100, 'phase_std')
    if correction not in ('calibrated','nominal','none'):
        raise ValueError('correction must be calibrated, nominal or none.')
    rho = density(PLUS if rho_in is None else rho_in)
    n = direction(phi,theta,basis,polar,azimuth)
    env = (I2+eta*X)/2
    u = np.diag([1.,np.exp(1j*phi)])
    env1 = u@env@u.conj().T
    cross = env@u.conj().T
    projectors = [(I2+sign*(n[0]*X+n[1]*Y+n[2]*Z))/2 for sign in (1,-1)]
    tau, factors, j = [], [], np.zeros((2,2),float)
    for idx,p in enumerate(projectors):
        a, b = float(np.trace(p@env).real), float(np.trace(p@env1).real)
        t = np.trace(p@cross)
        tau.append(np.array([[rho[0,0]*a, rho[0,1]*t], [rho[1,0]*t.conjugate(),rho[1,1]*b]],complex))
        factors.append(t)
        j[:,idx] = [a/2,b/2]
    confusion = np.array([[1-eps,eps],[eps,1-eps]]) # reported rows, true columns
    reported = [sum((confusion[y,o]*tau[o] for o in range(2)),np.zeros((2,2),complex)) for y in range(2)]
    t_rep = confusion@np.array(factors)
    j_rep = j@confusion.T
    out = np.zeros((2,2),complex)
    outcomes = []
    for y in range(2):
        t_cal = factors[y] if correction == 'nominal' else t_rep[y]
        angle = float(np.angle(t_cal)) if abs(t_cal)>1e-14 and correction!='none' else 0.
        d = np.diag([1.,np.exp(1j*angle)])
        branch = d@reported[y]@d.conj().T
        out += branch
        prob = float(np.trace(reported[y]).real)
        outcomes.append({'reported_label': '+' if y==0 else '-', 'probability': prob,
            'path0_given_label_equal_priors': float(j_rep[0,y]/j_rep[:,y].sum()) if j_rep[:,y].sum()>1e-14 else None,
            'correction_radians': angle, 'conditional_rho_unnormalized': reported[y],
            'corrected_rho_unnormalized': branch})
    if correction!='none': out = _phase_noise(out, sigma)
    raw = sum(tau, np.zeros((2,2),complex))
    k = float(np.abs(j_rep[0]-j_rep[1]).sum())
    optimum_k = eta*abs(math.sin(phi/2))
    return {'mode':'single','parameters':{'eta':eta,'phi':float(phi),'theta':float(theta),'basis':basis,
                'polar':float(polar),'azimuth':float(azimuth),'readout_error':eps,'phase_std':sigma,'correction':correction},
        'input':metrics(rho,rho),'system':metrics(raw,rho),
        'environment':{'knowledge_reported':k,'p_guess_reported':(1+k)/2,
            'information_reported_bits':classical_information(j_rep),
            'knowledge_ideal_chosen':float(np.abs(j[0]-j[1]).sum()),
            'helstrom_knowledge_ideal':optimum_k,'p_guess_helstrom_ideal':(1+optimum_k)/2,
            'conditional_states':[env,env1], 'equal_prior_calibration':True},
        'corrected':metrics(out,rho),'outcomes':outcomes,
        'bound_visibility_equal_superposition': math.sqrt(max(0.,1-(k/eta)**2)) if eta>0 else 1.,
        'assumptions':['one witness','independent initial S and E','controlled phase',
            'all reported outcomes retained','phase-only correction','symmetric classical label errors',
            'independent Gaussian feed-forward phase noise']}


def binary_entropy(p: float) -> float:
    if p <= 0 or p >= 1: return 0.
    return -p*math.log2(p)-(1-p)*math.log2(1-p)


def binomial_probabilities(n: int, p: float) -> np.ndarray:
    """Mode-centered recurrence; no factorial overflow or tail underflow at j=0."""
    n = count(n,0,100000,'n'); p=bounded(p,0,1,'p')
    result=np.zeros(n+1)
    if p==0: result[0]=1; return result
    if p==1: result[n]=1; return result
    mode=min(n,int(math.floor((n+1)*p)))
    result[mode]=1.
    for j in range(mode,0,-1): result[j-1]=result[j]*j/(n-j+1)*(1-p)/p
    for j in range(mode,n): result[j+1]=result[j]*(n-j)/(j+1)*p/(1-p)
    result/=result.sum()
    return result


def fragment_information(k: int, eta: float, readout_error: float = 0.) -> dict:
    """CZ commuting records: noisy local X readout (NOT parity readout).

    Bit-flips give eta_eff=eta*(1-2 eps). The returned noisy information is
    classical information of the recorded outcomes, not quantum MI of E.
    """
    k=count(k,0,100000,'k'); eta=bounded(eta,0,1,'eta'); eps=bounded(readout_error,0,.5,'readout_error')
    eff=eta*(1-2*eps)
    a=binomial_probabilities(k,(1+eff)/2); b=a[::-1]
    total=a+b
    mask=total>0
    posterior=np.divide(a,total,out=np.zeros_like(a),where=mask)
    h=np.array([binary_entropy(float(x)) for x in posterior])
    chi=float(np.clip(1-np.sum(total*h)/2,0,1))
    pe=float(np.minimum(a,b).sum()/2)
    return {'k':k,'eta':eta,'eta_effective':eff,'readout_error':eps,
            'path_information_bits':chi,'p_error':pe,'p_guess':1-pe,
            'knowledge':1-2*pe,'count_distribution_path0':a,'count_distribution_path1':b}


def threshold_records(eta: float, target: float=.9, max_k: int=100000) -> int | None:
    eta=bounded(eta,0,1,'eta'); target=bounded(target,1e-12,1-1e-12,'target')
    max_k=count(max_k,1,100000,'max_k')
    if eta==0: return None
    lo,hi=0,1
    while fragment_information(hi,eta)['path_information_bits']<target:
        if hi>=max_k: return None
        lo,hi=hi,min(max_k,2*hi)
    while hi-lo>1:
        mid=(lo+hi)//2
        if fragment_information(mid,eta)['path_information_bits']>=target: hi=mid
        else: lo=mid
    return hi


@dataclass(frozen=True)
class RecoveryConfig:
    n: int = 100
    eta: float = .6
    readout_error: float = .01
    gate_flip_error: float = .001
    collective_error: float = .02
    phase_std: float = 0.

    def checked(self) -> 'RecoveryConfig':
        count(self.n,1,100000,'n')
        bounded(self.eta,0,1,'eta')
        for name in ('readout_error','gate_flip_error','collective_error'):
            bounded(getattr(self,name),0,.5,name)
        bounded(self.phase_std,0,100,'phase_std')
        return self


def phase_flip_channel(rho: np.ndarray, factor: float) -> np.ndarray:
    """Explicit mixture of I and Z after the error parity is marginalized."""
    rho=density(rho); factor=bounded(factor,-1,1,'coherence factor')
    return (1+factor)/2*rho+(1-factor)/2*(Z@rho@Z)


def recovery_comparison(config: RecoveryConfig | None=None, rho_in: np.ndarray | None=None) -> dict:
    cfg=(config or RecoveryConfig()).checked(); r=density(PLUS if rho_in is None else rho_in)
    n=int(cfg.n); e=cfg.readout_error; p=cfg.gate_flip_error; q=cfg.collective_error
    noise=math.exp(-cfg.phase_std**2/2)
    lam_local=(1-2*e)**n
    lam_chain=(1-2*e)*(1-2*p)**(n-1)
    lam_collective=1-2*q
    descriptions=[('none',0.,0,0,'paper: unrecovered CZ channel'),
        ('individual',lam_local,n,0,'paper Eq. (8); optional Gaussian phase error added'),
        ('concentrated',lam_chain,1,n-1,'extension: independent target-X error after every CNOT'),
        ('collective',lam_collective,1,0,'extension: collective parity protocol with total error q'),
        ('ideal',1.,1,0,'ideal parity recovery; all imperfections disabled')]
    rows=[]
    for key,coh,reads,gates,model in descriptions:
        factor=coh*(noise if key not in ('none','ideal') else 1.)
        out=phase_flip_channel(r,factor)
        rows.append({'strategy':key,'coherence_factor':factor,'factor_before_phase_noise':coh,
             'residual_parity_error':(1-coh)/2,'readouts':reads,'cnot_count':gates,
             'model':model, **metrics(out,r),
             'entanglement_fidelity':(1+factor)/2,'average_pure_state_fidelity':(2+factor)/3})
    # These path metrics belong to an alternative X-readout calibration, not to
    # the same run as Z/parity recovery. They do NOT encode which-path leakage
    # produced by the illustrated recovery operation.
    f0=fragment_information(n,cfg.eta)
    f1=fragment_information(n,cfg.eta,e)
    ideal_mi=1+f0['path_information_bits']
    return {'mode':'many_CZ','parameters':asdict(cfg),'input':metrics(r,r),'rows':rows,
        'path_calibration':{'ideal':f0,'noisy_X_readout':f1,
            'quantum_mutual_information_full_environment_plus_input':ideal_mi,
            'different_measurement_than_recovery':True},
        'threshold_gate_flip_error': e if n>1 else None,
        'assumptions':['phi=pi','N independent equal witnesses','only phase errors of S',
            'independent symmetric label errors','no amplitude damping, loss or leakage',
            'CNOT noise is target-X probability, not general gate infidelity',
            'collective error is an independent total-protocol parameter',
            'Gaussian phase error is an added phenomenological model']}


def monte_carlo(config: RecoveryConfig, shots: int=20000, seed: int=20261102) -> dict:
    """Explicit stochastic error counts, not synthetic perturbations of a result.

    Sampling is a numerical experiment under the declared model, not hardware data.
    Signed X quadrature is reported; its standard error is not a confidence claim.
    """
    c=config.checked(); shots=count(shots,1,1000000,'shots'); rng=np.random.default_rng(seed)
    signs={
        'individual':1-2*(rng.binomial(int(c.n),c.readout_error,shots)%2),
        'concentrated':1-2*((rng.binomial(max(0,int(c.n)-1),c.gate_flip_error,shots)+rng.binomial(1,c.readout_error,shots))%2),
        'collective':1-2*rng.binomial(1,c.collective_error,shots)}
    theoretical={r['strategy']:r['coherence_factor'] for r in recovery_comparison(c)['rows']}
    result={}
    for strategy,sign in signs.items():
        phase=rng.normal(0,c.phase_std,shots)
        values=sign*np.exp(-1j*phase)
        factor=values.mean()
        se=float(values.real.std(ddof=1)/math.sqrt(shots)) if shots>1 else None
        result[strategy]={'signed_quadrature':float(factor.real),'quadrature_imag':float(factor.imag),
            'visibility_estimate':float(abs(factor)),'standard_error_real':se,
            'theory':theoretical[strategy],'residual_flip_count':int((sign<0).sum())}
    return {'shots':shots,'seed':seed,'results':result,'kind':'synthetic simulation, not measured data'}


def serializable(value: Any) -> Any:
    if isinstance(value,np.ndarray): return serializable(value.tolist())
    if isinstance(value,(complex,np.complexfloating)): return [float(value.real),float(value.imag)]
    if isinstance(value,np.generic): return value.item()
    if isinstance(value,dict): return {k:serializable(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [serializable(v) for v in value]
    return value


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['single','many'],default='single')
    parser.add_argument('--eta',type=float,default=.6)
    parser.add_argument('--phi-deg',type=float,default=180.)
    parser.add_argument('--theta-deg',type=float,default=0.)
    parser.add_argument('--basis',choices=['family','z','path','x','y'],default='family')
    parser.add_argument('--n',type=int,default=100)
    parser.add_argument('--epsilon',type=float,default=.01)
    parser.add_argument('--gate-error',type=float,default=.001)
    parser.add_argument('--collective-error',type=float,default=.02)
    parser.add_argument('--phase-std',type=float,default=0.)
    parser.add_argument('--correction',choices=['calibrated','nominal','none'],default='calibrated')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    try:
        if args.mode=='single':
            r=single_witness(args.eta,math.radians(args.phi_deg),math.radians(args.theta_deg),
                basis=args.basis,readout_error=args.epsilon,phase_std=args.phase_std,correction=args.correction)
        else:
            r=recovery_comparison(RecoveryConfig(args.n,args.eta,args.epsilon,args.gate_error,args.collective_error,args.phase_std))
        obj={'software':'FENIX Lab','version':VERSION,'source':SOURCE,'result':serializable(r)}
        text=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)
        if args.out: args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(text+'\n',encoding='utf-8')
        else: print(text)
    except (ValueError,TypeError) as exc:
        parser.error(str(exc))


if __name__=='__main__': main()
