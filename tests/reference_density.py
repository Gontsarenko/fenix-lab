"""Independent full-density-matrix reference (small N only).

These routines deliberately do not call the fast formulas in fenix_core.
They are slow, explicit cross-checks. S is first (most significant) qubit.
"""
import math
import numpy as np

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Z=np.diag([1,-1]).astype(complex)


def joint_state(rho,eta,n,phi=math.pi):
    env=np.array([[1,eta],[eta,1]],complex)/2
    initial=rho.copy()
    for _ in range(n): initial=np.kron(initial,env)
    d=2**n
    phases=np.array([1]*d+[np.exp(1j*phi*b.bit_count()) for b in range(d)])
    return phases[:,None]*initial*phases.conj()[None,:]


def partial_environment(joint,n):
    d=2**n
    return np.trace(joint.reshape(2,d,2,d),axis1=1,axis2=3)


def recover(joint,n,kind,epsilon=0.,gate_error=0.,collective_error=0.,phase_std=0.):
    d=2**n; state=joint.copy()
    if kind=='concentrated':
        idx=np.arange(2*d)
        target=1<<(n-1)
        for control in range(n-2,-1,-1):
            perm=np.array([i^target if i&(1<<control) else i for i in idx])
            state=state[np.ix_(perm,perm)]
            flip=idx^target
            state=(1-gate_error)*state+gate_error*state[np.ix_(flip,flip)]
    out=np.zeros((2,2),complex)
    for true_record in range(d):
        ix=[true_record,d+true_record]
        tau=state[np.ix_(ix,ix)]
        if kind=='individual':
            # Enumerate all classical error strings independently of Eq. (8).
            for err in range(d):
                w=err.bit_count()
                prob=epsilon**w*(1-epsilon)**(n-w)
                parity=(true_record^err).bit_count()%2
                op=Z if parity else I
                out+=prob*(op@tau@op)
        else:
            true_bit=((true_record>>(n-1))&1) if kind=='concentrated' else (true_record.bit_count()%2)
            error=epsilon if kind=='concentrated' else collective_error
            for wrong in (0,1):
                prob=error if wrong else 1-error
                op=Z if (true_bit^wrong) else I
                out+=prob*(op@tau@op)
    out[0,1]*=math.exp(-phase_std**2/2)
    out[1,0]=out[0,1].conjugate()
    return out


def single_reference(eta,phi,n,epsilon=0.,correction='calibrated',rho=None,sigma=0.):
    if rho is None: rho=np.ones((2,2),complex)/2
    env=np.array([[1,eta],[eta,1]],complex)/2
    init=np.kron(rho,env)
    U=np.diag([1,1,1,np.exp(1j*phi)])
    joint=U@init@U.conj().T
    pauli=[X,np.array([[0,-1j],[1j,0]]),Z]
    axis=sum(n[k]*pauli[k] for k in range(3))
    projectors=[(I+axis)/2,(I-axis)/2]
    true=[]; cal=[]
    joint_cal=U@np.kron(np.ones((2,2))/2,env)@U.conj().T
    for p in projectors:
        op=np.kron(I,p)
        post=op@joint@op
        true.append(np.trace(post.reshape(2,2,2,2),axis1=1,axis2=3))
        post=op@joint_cal@op
        cal.append(np.trace(post.reshape(2,2,2,2),axis1=1,axis2=3))
    report=[(1-epsilon)*true[i]+epsilon*true[1-i] for i in range(2)]
    cal_report=[(1-epsilon)*cal[i]+epsilon*cal[1-i] for i in range(2)]
    corrected=np.zeros((2,2),complex)
    for i in range(2):
        c=(cal[i] if correction=='nominal' else cal_report[i])[0,1]
        angle=np.angle(c) if abs(c)>1e-14 and correction!='none' else 0.
        op=np.diag([1,np.exp(1j*angle)])
        corrected+=op@report[i]@op.conj().T
    if correction!='none':
        corrected[0,1]*=math.exp(-sigma**2/2)
        corrected[1,0]=corrected[0,1].conjugate()
    k=sum(abs(float((a[0,0]-a[1,1]).real)) for a in cal_report)
    return partial_environment(joint,1), corrected, k
