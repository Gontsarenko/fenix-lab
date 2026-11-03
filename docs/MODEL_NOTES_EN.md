# FENIX Lab 1.1 — mathematical specification

## Source and scope

Source: S. Gontsarenko, *Decoherence without facts*, draft v1.4, 2 November 2026.
This document specifies the implemented simulator. It is not a new review or a claim of
priority. Source results and additional error models are separated below. Every numerical
example is a model calculation, not a measurement. The numerical core is unchanged from v1.0.0.

## 1. One witness: the exact core

The environment state and conditional unitary are

\[
\rho_E=\tfrac12(I+\eta X),\quad U=\operatorname{diag}(1,e^{i\varphi}),\quad 0\le\eta\le1.
\]

The interface starts S in |+⟩; the API also accepts an arbitrary positive, trace-one qubit
state. S and E are initially uncorrelated. Joint matrix ordering is S, then E.
For an environment projector P_o the unnormalised conditional system state is

\[
\tau_o=\begin{pmatrix}
\rho_{00}\operatorname{Tr}(P_o\rho_E)&\rho_{01}\operatorname{Tr}(P_o\rho_E U^\dagger)\\
\rho_{10}\operatorname{Tr}(P_o U\rho_E)&\rho_{11}\operatorname{Tr}(P_o U\rho_E U^\dagger)
\end{pmatrix}.
\]

The upper-right entry fixes the phase convention. Conditional states are not separately
normalised before being combined; their traces are the outcome probabilities.
Before readout, ρ′01 = ρ01(1 + exp(−iφ))/2.

The paper’s readout family is

\[
\hat d=(\sin(\varphi/2),-\cos(\varphi/2),0),\qquad
\hat n=\cos\theta\,\hat z+\sin\theta\,\hat d.
\]

For ideal readout and input |+⟩:

\[
K=\eta|\sin\theta\sin(\varphi/2)|,\qquad
V=\sqrt{1-\sin^2\theta\sin^2(\varphi/2)}.
\]

Z, X, Y, d and arbitrary projective axes are available. The interface does **not** accept a
user-defined general POVM: it displays Proposition 3’s bound but implements binary projective
readouts followed by classical mixing of labels.

### Extension: readout-label errors

After ideal outcome o the recorded label y is drawn with

\[
C_{yo}=\begin{cases}1-\varepsilon,&y=o,\\\varepsilon,&y\ne o,\end{cases}\qquad
\widetilde\tau_y=\sum_o C_{yo}\tau_o.
\]

This is a classical reporting error, not a rotation of the physical basis or an interaction
error. The supported range is 0 ≤ ε ≤ 1/2. Errors above 1/2 could be relabelled, but that is
outside this interface. Under equal prior path probabilities,

\[
K=\sum_y|p(0,y)-p(1,y)|,\qquad P_{\rm guess}=(1+K)/2.
\]

Classical mutual information is calculated separately from p(s,y); K is not an entropy.

### Actual correction

Let t_y be the factor multiplying the input coherence in the recorded branch:

\[
t_y=\sum_o C_{yo}\operatorname{Tr}(P_o\rho_EU^\dagger),\qquad
D_y=\operatorname{diag}(1,e^{i\arg t_y}),\qquad
\rho_{\rm corr}=\sum_yD_y\widetilde\tau_yD_y^\dagger.
\]

When t_y is numerically zero the correction phase is set to zero. Calibrating with t_y,
not with the input coherence’s phase, preserves an unknown input phase. Nominal feedback
uses t_y for ε = 0. With feedback disabled, D = I.

The code combines **actually corrected matrices** and then calculates 2|ρ01|. Merely adding
branch magnitudes does not verify that the chosen operations aligned the phases.

### Extension: feedback phase noise

One independent phase δ ∼ N(0,σ²) acts after correction, giving
⟨exp(−iδ)⟩ = exp(−σ²/2). This is one final noise channel, not N separate errors.
It is not applied when correction is disabled. Populations do not relax.

## 2. The displayed boundary

For one witness, input |+⟩, phase-only feedback and all outcomes retained:

\[
(K/\eta)^2+V^2\le1,\quad K\le\eta|\sin(\varphi/2)|,\quad\eta>0.
\]

At η = 0, K = 0 and Z readout attains V = 1. There is no division by zero.
For other API-supported inputs, `bound_visibility_equal_superposition` remains a **reference
for |+⟩**, not a new theorem for unequal paths. Classical label errors give a noisy measurement;
additional independent phase noise cannot increase recovered coherence.

## 3. Many witnesses: fixed scope

The second mode fixes φ = π, N ≥ 1 and independent E_i = (I + ηX)/2.
Each Z outcome is equiprobable. The system’s phase flip depends on
p = z_1 XOR … XOR z_N; reading the whole parity and applying Z^p restores any input ideally.
For parity-estimation error q_err,

\[
\mathcal R(\rho)=(1-q_{\rm err})\rho+q_{\rm err}Z\rho Z.
\]

With C_0 = 1 − 2q_err and C = C_0 exp(−σ²/2), the final channel is equivalently an I/Z mixture
with effective error (1 − C)/2. The code constructs that output matrix, not just its scalar C.
This reduced channel is exact within the model at large N. Independent small-N tests construct
full joint matrices and explicitly apply operations and noise channels.

### Individual readouts — source Eq. (8) plus final phase noise

\[
C_{\rm ind}=(1-2\varepsilon)^N e^{-\sigma^2/2}.
\]

The factor without σ is from the paper. With 0 ≤ ε ≤ 1/2, C is non-negative.

### CNOT concentration — source’s ideal circuit plus an added gate-error channel

Apply CNOT E_j → E_1 for j = 2,…,N. After every ideal CNOT:

\[
\mathcal N_g(\rho)=(1-p_g)\rho+p_gX_{E_1}\rho X_{E_1}.
\]

These errors are independent. Target-X commutes with subsequent CNOTs sharing that target,
so the residual flip is the XOR of N−1 gate errors and one readout error:

\[
C_{\rm chain}=(1-2p_g)^{N-1}(1-2\varepsilon)e^{-\sigma^2/2}.
\]

Only the ideal concentration circuit is from the paper; this gate-error channel and its
formula are simulator extensions. **Do not substitute general published gate infidelity
for p_g without identifying an equivalent channel.** For N > 1, ε < 1/2 and finite σ, the
crossover is p_g = ε. At ε = 1/2 both methods give C = 0.

### Collective parity — a separate assumption

A whole collective protocol returns the wrong parity with probability q:

\[
C_{\rm coll}=(1-2q)e^{-\sigma^2/2}.
\]

q describes the **entire protocol**. “1 protocol” is not one free or elementary operation.
A real protocol’s q may depend on N; the interface holds q fixed in its N scan.

## 4. State metrics

For normalised qubit matrices:

\[
V=2|\rho_{01}|,\qquad F(\rho,\sigma)=\operatorname{Tr}(\rho\sigma)+2\sqrt{\det\rho\det\sigma}.
\]

F is squared Uhlmann fidelity. For the real phase channel and input |+⟩, F = (1+C)/2.
For |0⟩, F = 1 regardless of C, while V = 0. The Python API additionally reports entanglement
fidelity (1+C)/2 and average pure-input fidelity (2+C)/3, for this reduced channel only.

## 5. Reading path information

CZ records commute in X. With equal path priors,

\[
P(j|0)=\binom{k}{j}p^j(1-p)^{k-j},\quad P(j|1)=P(k-j|0),\quad p=(1+\eta)/2,
\]
\[
\chi_k=1-\sum_j\frac{P(j|0)+P(j|1)}2H_2\!\left(\frac{P(j|0)}{P(j|0)+P(j|1)}\right),
\qquad P_e=\frac12\sum_j\min(P(j|0),P(j|1)).
\]

For symmetric errors in X readout, replace η by η(1−2ε) when calculating information in
**recorded outcomes**. This is not a claim that the environment’s physical preparation changed.
Binomial weights are built from the mode and normalised, avoiding an underflow-prone start
at (1−p)^k. Exact recurrence, not a Gaussian approximation, determines k_0.9.

For input |+⟩, proper fragments have I(S:F_k) = χ_k; the whole environment has I(S:E) = 1+χ_N.
The additional bit is not path information. For other inputs the fragment panel remains an
equal-prior calibration. Path readout and parity recovery are alternative experiments, not
simultaneous incompatible readings on a single copy.

## 6. Not included

General processors, energy relaxation, leakage, loss, unknown coupling parameters, correlated
errors, CNOT control-qubit noise, interacting witnesses, incomplete-environment parity recovery,
many-witness parity recovery at arbitrary φ, operation duration, energy/resource costs, and
final-detector shot noise in Monte Carlo trials are not modelled.

## 7. Verification and implementation references

The physical source is the supplied paper v1.4, not a reconstruction from websites.
The numerical implementation uses NumPy. One test compares binomial recurrence with SciPy;
SciPy is not needed by the numerical core itself.

`tests/reference_density.py` is an independent full-matrix reference rather than a call to the
formula under test. `tests/cross_language.py` compares Python and JavaScript implementations.
Random checks support numerical implementation, not priority or a replacement for the proof.

Implementation documentation retained from v1.0:
- https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigvalsh.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html
