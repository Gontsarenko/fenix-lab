import sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
import fenix_core as f
from reference_density import joint_state, partial_environment, recover, single_reference


def random_state(rng):
    a=rng.normal(size=(2,2))+1j*rng.normal(size=(2,2))
    r=a@a.conj().T
    return r/np.trace(r)


@pytest.mark.parametrize('eta',[0,.1,.6,1])
def test_table_1(eta):
    for basis in ['z','path','y']:
        r=f.single_witness(eta,math.pi,basis=basis)
        assert r['system']['visibility']<1e-12
        assert r['environment']['p_guess_helstrom_ideal']==pytest.approx((1+eta)/2)
        assert r['corrected']['visibility']==pytest.approx({'z':1,'path':0,'y':eta}[basis],abs=1e-12)


def test_sign_regression_and_phase_of_unknown_input():
    r=f.single_witness(.6,math.pi/2,basis='z')
    np.testing.assert_allclose(r['corrected']['rho'],f.PLUS,atol=1e-14)
    # Reproduce the historical wrong-sign failure by using conjugate corrections.
    wrong=np.zeros((2,2),complex)
    for outcome in r['outcomes']:
        d=np.diag([1,np.exp(-1j*outcome['correction_radians'])])
        wrong+=d@outcome['conditional_rho_unnormalized']@d.conj().T
    assert 2*abs(wrong[0,1])<1e-12
    for phi in [.2,math.pi/2,math.pi,4.3]:
        rho=f.state(1.1,.77,.82)
        result=f.single_witness(.27,phi,basis='z',rho_in=rho)
        np.testing.assert_allclose(result['corrected']['rho'],rho,atol=1e-13)


def test_random_single_full_density():
    rng=np.random.default_rng(7301)
    for _ in range(180):
        eta,eps=rng.random(),rng.random()/2
        phi,theta,az=rng.uniform(-2*math.pi,2*math.pi,3)
        polar=rng.uniform(0,math.pi); sigma=rng.random()
        basis=rng.choice(['family','custom','y','z','path'])
        rho=random_state(rng)
        for correction in ['calibrated','nominal','none']:
            r=f.single_witness(eta,phi,theta,basis,polar,az,eps,sigma,correction,rho)
            n=f.direction(phi,theta,basis,polar,az)
            raw,out,k=single_reference(eta,phi,n,eps,correction,rho,sigma)
            np.testing.assert_allclose(r['system']['rho'],raw,atol=2e-13)
            np.testing.assert_allclose(r['corrected']['rho'],out,atol=2e-13)
            assert r['environment']['knowledge_reported']==pytest.approx(k,abs=1e-13)
            assert abs(np.trace(out)-1)<1e-12
            assert np.linalg.eigvalsh(out).min()>-1e-12


def test_ideal_family_and_bound_with_noise():
    rng=np.random.default_rng(1731)
    for _ in range(350):
        eta=rng.uniform(.0001,1); phi=rng.uniform(0,2*math.pi); theta=rng.uniform(-math.pi,math.pi)
        r=f.single_witness(eta,phi,theta)
        k=eta*abs(math.sin(theta)*math.sin(phi/2))
        v=math.sqrt(max(0,1-math.sin(theta)**2*math.sin(phi/2)**2))
        assert r['environment']['knowledge_reported']==pytest.approx(k,abs=1e-12)
        assert r['corrected']['visibility']==pytest.approx(v,abs=1e-12)
        r=f.single_witness(eta,phi,theta,readout_error=rng.random()/2,phase_std=rng.random())
        assert (r['environment']['knowledge_reported']/eta)**2+r['corrected']['visibility']**2<=1+1e-12


@pytest.mark.parametrize('n',[1,2,3,4,5])
def test_many_strategies_against_explicit_matrices(n):
    rng=np.random.default_rng(420+n)
    for eta in [0,.37,1]:
        rho=random_state(rng)
        cfg=f.RecoveryConfig(n,eta,.07,.023,.19,.16)
        model=f.recovery_comparison(cfg,rho)
        joint=joint_state(rho,eta,n)
        np.testing.assert_allclose(partial_environment(joint,n),model['rows'][0]['rho'],atol=1e-12)
        for row in model['rows'][1:4]:
            out=recover(joint,n,row['strategy'],cfg.readout_error,cfg.gate_flip_error,cfg.collective_error,cfg.phase_std)
            np.testing.assert_allclose(out,row['rho'],atol=2e-12)


def test_many_nonzero_phase_raw():
    rho=f.state(1.1,.72,.8)
    for n in [1,2,4]:
        for eta in [0,.2,1]:
            for phi in [.1,.9,2.3,math.pi]:
                actual=partial_environment(joint_state(rho,eta,n,phi),n)
                expected=rho.copy(); expected[0,1]*=((1+np.exp(-1j*phi))/2)**n
                expected[1,0]=expected[0,1].conjugate()
                np.testing.assert_allclose(actual,expected,atol=1e-12)


def test_readout_scaling_and_crossover():
    cfg=f.RecoveryConfig(n=100,readout_error=.01,gate_flip_error=.001)
    a=f.recovery_comparison(cfg)
    assert a['rows'][1]['visibility']==pytest.approx(.98**100)
    assert a['rows'][2]['visibility']>a['rows'][1]['visibility']
    equal=f.recovery_comparison(f.RecoveryConfig(n=60,readout_error=.01,gate_flip_error=.01))
    assert equal['rows'][1]['visibility']==pytest.approx(equal['rows'][2]['visibility'])
    bad=f.recovery_comparison(f.RecoveryConfig(n=60,readout_error=.01,gate_flip_error=.04))
    assert bad['rows'][2]['visibility']<bad['rows'][1]['visibility']


def test_fragment_thresholds_and_labels():
    for eta,k in [(.9,3),(.6,9),(.3,40),(.2,92),(.1,374),(.05,1502)]:
        assert f.threshold_records(eta)==k
    assert f.threshold_records(0) is None
    assert f.fragment_information(0,.6)['path_information_bits']==pytest.approx(0)
    assert f.fragment_information(60,.1)['path_information_bits']==pytest.approx(.33713,abs=1e-5)
    r=f.recovery_comparison(f.RecoveryConfig(n=60,eta=0))
    assert r['path_calibration']['ideal']['path_information_bits']==pytest.approx(0)
    assert r['path_calibration']['quantum_mutual_information_full_environment_plus_input']==pytest.approx(1)
    assert f.fragment_information(10,.3,.5)['p_guess']==pytest.approx(.5)


def test_binomial_vs_independent_scipy_if_available():
    scipy=pytest.importorskip('scipy.stats')
    for n in [1,60,2000,10000]:
        for p in [.001,.1,.5,.82,.999]:
            ref=scipy.binom.pmf(np.arange(n+1),n,p)
            np.testing.assert_allclose(f.binomial_probabilities(n,p),ref,atol=2e-12)


def test_noise_calibration_never_worse_than_nominal():
    rng=np.random.default_rng(1912)
    for _ in range(100):
        args=dict(eta=rng.random(),phi=rng.random()*6.2,basis='custom',polar=rng.random()*3.14,azimuth=rng.random()*6.28,readout_error=rng.random()/2)
        optimal=f.single_witness(**args,correction='calibrated')['corrected']['visibility']
        nominal=f.single_witness(**args,correction='nominal')['corrected']['visibility']
        assert optimal>=nominal-1e-12


def test_monte_carlo_and_reproducibility():
    c=f.RecoveryConfig(27,.6,.017,.009,.07,.18)
    a=f.monte_carlo(c,50000,812)
    assert a==f.monte_carlo(c,50000,812)
    for entry in a['results'].values():
        assert abs(entry['signed_quadrature']-entry['theory'])<5*entry['standard_error_real']


def test_input_safety():
    for kwargs in [{'eta':-1},{'readout_error':.51},{'phi':float('nan')},{'phase_std':-1},{'basis':'invalid'},{'correction':'anything'}]:
        with pytest.raises(ValueError): f.single_witness(**kwargs)
    for cfg in [f.RecoveryConfig(n=0),f.RecoveryConfig(n=1.2),f.RecoveryConfig(gate_flip_error=.9)]:
        with pytest.raises(ValueError): f.recovery_comparison(cfg)
    with pytest.raises(ValueError): f.single_witness(rho_in=np.array([[1,1],[0,0]]))


def test_poles_and_zero_phase():
    for eta in [0,1]:
        for eps in [0,.5]:
            for theta in [0,math.pi/2,math.pi]:
                r=f.single_witness(eta,0,theta,readout_error=eps)
                assert r['system']['visibility']==pytest.approx(1)
                assert r['environment']['p_guess_reported']==pytest.approx(.5)
                assert r['corrected']['visibility']==pytest.approx(1)
    rho=f.state(0)
    for row in f.recovery_comparison(f.RecoveryConfig(),rho)['rows']:
        assert row['fidelity']==pytest.approx(1)
        assert row['visibility']==pytest.approx(0,abs=1e-15)
