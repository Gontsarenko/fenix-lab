"""Run from the project folder: python examples/python_example.py."""
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fenix_core import single_witness, recovery_comparison, RecoveryConfig, state

one=single_witness(eta=0,phi=math.pi,basis='z')
print('No path facts, but ideal recovery:')
print('V before:',one['system']['visibility'])
print('Pguess:',one['environment']['p_guess_reported'])
print('V after:',one['corrected']['visibility'])

print('\nRecovery strategies, N=100:')
for row in recovery_comparison(RecoveryConfig())['rows']:
    print(f"{row['strategy']:14s} C={row['coherence_factor']:.6f} F={row['fidelity']:.6f}")

# An arbitrary mixed input: correction does not assume knowledge of its phase.
rho=state(theta=1.1,phase=.7,bloch_radius=.8)
recovered=single_witness(eta=.3,phi=.84,basis='z',rho_in=rho)
print('\nUnknown input phase, ideal recovery fidelity:',recovered['corrected']['fidelity'])
