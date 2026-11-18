#!/usr/bin/env python3
"""QuantumPhotonics-Lab - educational single-photon optics lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the honest scope is stated up front:

  * This lab computes EXACT amplitudes for a truncated two-mode
    Fock space (at most 3 photons total). Beam splitters and phase
    shifters are exact unitaries inside that space because both
    conserve total photon number, so nothing leaks out of the
    truncation - the arithmetic is exact for the toy, and the toy
    is all it is.
  * There are no real photons, sources, fibres, or detectors here.
    A fringe computed in this file is not a measurement of a real
    phase, a Hong-Ou-Mandel dip in this file does not certify a
    real single-photon source, and no number printed here is a
    sensing, imaging, ranging, or communications result.
  * What IS real is the optics logic: two indistinguishable
    photons bunch at a 50:50 beam splitter (coincidence -> 0),
    distinguishable ones do not (coincidence -> 1/2), a marked
    which-path destroys Mach-Zehnder visibility, photon statistics
    separate coherent (g2 = 1), Fock (g2 = 0), and thermal (g2 = 2)
    light, and a two-photon NOON state fringes twice as fast as a
    single photon.

Real sources, detectors, quantum communications, sensing, imaging,
ranging, random-number generation, and every other real-world use
are permanent HOLD gates - with Gemini Argon 4 Extended Thinking
as DECIDER (names-only, tighten-only), Muse as advisor (never
overrides HOLD), and Google Flow plan-only seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"
MAX_PHOTONS = 3  # truncated two-mode Fock space: n_a + n_b <= 3

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_photon_source_claim": "HOLD - no claim of a real single-photon source; the Fock states here are vectors in a toy basis",
    "quantum_communication_claim": "HOLD - no quantum-communication, QKD, or network use; interference arithmetic is not a channel",
    "quantum_sensing_claim": "HOLD - no sensing or metrology product claim; the phase-precision line is a textbook shot-noise note",
    "lidar_ranging_claim": "HOLD - no LiDAR, ranging, or remote-sensing use of these amplitudes",
    "medical_imaging_claim": "HOLD - no medical, diagnostic, or biological imaging claim",
    "detector_certification_claim": "HOLD - no certifying real detectors, efficiencies, dark counts, or timing jitter",
    "random_number_generation_claim": "HOLD - no quantum random-number generation claim from simulated statistics",
    "surveillance_claim": "HOLD - no surveillance, identification, or tracking use",
    "weapons_guidance_claim": "HOLD - no weapons, guidance, targeting, or military use",
    "commercial_product_claim": "HOLD - no commercial photonic product, component, or performance claim",
    "hardware_control_claim": "HOLD - no control of real lasers, optics benches, sources, or detectors",
    "interference_as_measurement_claim": "HOLD - a simulated fringe is not a measurement of a real phase, length, or field",
    "entanglement_certification_claim": "HOLD - HOM bunching and NOON amplitudes in a truncated basis do not certify real entanglement",
    "truncated_model_as_device_claim": "HOLD - a <=3-photon truncated toy must never be presented as a device model or specification",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Fock space
# Two modes (a, b), basis states |n_a, n_b> with n_a + n_b <= MAX_PHOTONS.
# Beam splitters and phase shifters conserve total photon number, so
# their action never leaves this basis: the truncated unitaries below
# are exact, not approximations, for every state in the space.

def _build_basis():
    states = []
    for total in range(MAX_PHOTONS + 1):
        for n_a in range(total + 1):
            states.append((n_a, total - n_a))
    return states


BASIS = _build_basis()
INDEX = {state: i for i, state in enumerate(BASIS)}
DIM = len(BASIS)


def basis_state(n_a, n_b):
    """Unit vector for |n_a, n_b>."""
    vec = [0j] * DIM
    vec[INDEX[(n_a, n_b)]] = 1.0 + 0j
    return vec


def _mat_mul(a, b):
    n = len(a)
    out = [[0j] * n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            aik = a[i][k]
            if aik == 0j:
                continue
            for j in range(n):
                out[i][j] += aik * b[k][j]
    return out


def _mat_dagger(a):
    return [[a[j][i].conjugate() for j in range(len(a))]
            for i in range(len(a))]


def _mat_vec(a, v):
    return [sum(a[i][j] * v[j] for j in range(len(v))) for i in range(len(a))]


def _identity(n):
    return [[1.0 + 0j if i == j else 0j for j in range(n)] for i in range(n)]


def unitarity_error(u):
    """Max |U^dagger U - I| entry: 0 for an exact unitary."""
    prod = _mat_mul(_mat_dagger(u), u)
    ident = _identity(DIM)
    return max(abs(prod[i][j] - ident[i][j])
               for i in range(DIM) for j in range(DIM))


def prob(state, n_a, n_b):
    """Born probability of finding |n_a, n_b> in a state vector."""
    amp = state[INDEX[(n_a, n_b)]]
    return amp.real ** 2 + amp.imag ** 2


def total_probability(state):
    return sum(amp.real ** 2 + amp.imag ** 2 for amp in state)


# ================================================================ 2. Beam splitter + phase shifter
# The beam splitter acts on creation operators as
#     a^dag ->  cos(t) a^dag + sin(t) b^dag
#     b^dag -> -sin(t) a^dag + cos(t) b^dag
# so transmissivity is cos^2(t) and reflectivity sin^2(t); t = pi/4 is
# the 50:50 splitter. Each output column is built by substituting the
# transformed operators into (a^dag)^na (b^dag)^nb / sqrt(na! nb!) and
# expanding the two binomials exactly - polynomial arithmetic on
# (power_a, power_b) monomials, no series truncation anywhere.

def _poly_mul(p, q):
    out = {}
    for (pa, pb), ca in p.items():
        for (qa, qb), cb in q.items():
            key = (pa + qa, pb + qb)
            out[key] = out.get(key, 0j) + ca * cb
    return out


def _poly_pow(p, n):
    out = {(0, 0): 1.0 + 0j}
    for _ in range(n):
        out = _poly_mul(out, p)
    return out


def beam_splitter(theta):
    """Exact beam-splitter unitary on the truncated Fock basis."""
    c, s = math.cos(theta), math.sin(theta)
    a_img = {(1, 0): complex(c), (0, 1): complex(s)}       # a^dag image
    b_img = {(1, 0): complex(-s), (0, 1): complex(c)}      # b^dag image
    u = [[0j] * DIM for _ in range(DIM)]
    for (n_a, n_b), col in INDEX.items():
        poly = _poly_mul(_poly_pow(a_img, n_a), _poly_pow(b_img, n_b))
        norm = math.sqrt(math.factorial(n_a) * math.factorial(n_b))
        for (p, q), coeff in poly.items():
            amp = coeff * math.sqrt(math.factorial(p)
                                    * math.factorial(q)) / norm
            u[INDEX[(p, q)]][col] = amp
    return u


def phase_shifter(phi, mode="b"):
    """Exact phase shifter: |n_a, n_b> gains e^{i phi n_mode}."""
    u = [[0j] * DIM for _ in range(DIM)]
    for (n_a, n_b), i in INDEX.items():
        n = n_b if mode == "b" else n_a
        u[i][i] = complex(math.cos(phi * n), math.sin(phi * n))
    return u


BS50 = beam_splitter(math.pi / 4)
# The recombiner in an interferometer is the mirror image of the
# first splitter - the inverse unitary, BS(-pi/4) - which is what
# makes the Mach-Zehnder fringe below read cos^2(phi/2).
RECOMBINER = beam_splitter(-math.pi / 4)


def apply(u, state):
    return _mat_vec(u, state)


# ================================================================ 3. Hong-Ou-Mandel effect
# Two indistinguishable photons, one in each input port of a 50:50
# splitter, ALWAYS leave together: the |1,1> output amplitude is the
# difference of the two indistinguishable paths (both transmitted,
# both reflected) and cancels exactly. Distinguishable photons take
# the paths independently, so coincidence is T^2 + R^2 = 1/2 at 50:50.
# Partial distinguishability interpolates: only the indistinguishable
# fraction eta^2 of pairs interferes, P_coinc = (1 - eta^2) / 2.

def hom_output():
    """The |1,1> input through a 50:50 splitter: the NOON state."""
    return apply(BS50, basis_state(1, 1))


def hom_coincidence_indistinguishable():
    """Exact coincidence probability from the Fock unitary."""
    return prob(hom_output(), 1, 1)


def hom_coincidence_distinguishable(theta=math.pi / 4):
    """Classical independent-path coincidence: T^2 + R^2.

    Photon a reaches output 1 with probability T and output 2 with
    probability R; photon b (entering the other port) reaches output
    1 with probability R and output 2 with probability T. They land
    in different outputs with probability T*T + R*R - at 50:50 that
    is exactly 1/2, the floor the HOM dip falls away from.
    """
    t2 = math.cos(theta) ** 2
    r2 = math.sin(theta) ** 2
    return t2 * t2 + r2 * r2


def hom_coincidence(eta):
    """Coincidence for mode-overlap amplitude eta in [0, 1].

    Only the indistinguishable fraction eta^2 of photon pairs
    interferes destructively; the rest behave classically.
    eta = 1 -> 0 (full dip), eta = 0 -> 1/2 (no dip).
    """
    return (1.0 - eta ** 2) / 2.0


def hom_eta_from_delay(delay, sigma=1.0):
    """Labelled Gaussian mode overlap vs arrival-time delay.

    sigma is a LABELLED coherence width in arbitrary delay units -
    a teaching shape for the dip, not a measured source property.
    """
    return math.exp(-(delay ** 2) / (2.0 * sigma ** 2))


def hom_dip_curve(sigma=1.0):
    """Coincidence vs delay: the HOM dip, computed point by point."""
    delays = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
    return [(d, hom_coincidence(hom_eta_from_delay(d, sigma)))
            for d in delays]


def hom_dip_visibility(sigma=1.0):
    """Dip visibility (P_far - P_0) / P_far; 1.0 for the ideal dip."""
    p0 = hom_coincidence(hom_eta_from_delay(0.0, sigma))
    p_far = hom_coincidence(hom_eta_from_delay(6.0 * sigma, sigma))
    return (p_far - p0) / p_far


# ================================================================ 4. Mach-Zehnder interferometer
# BS -> phase phi on mode b -> BS. A single photon entering port a
# exits port a with probability cos^2(phi/2): a perfect fringe with
# visibility 1. If the path is MARKED - some degree of freedom in
# principle records which way the photon went - the marked fraction
# cannot interfere and lands 50:50, so visibility falls to 1 - m.
# The phase-precision line is the textbook shot-noise note
# dphi ~ 1 / (V sqrt(N)): a statement about counting statistics,
# not a sensing claim (see the HOLD gates).

def mz_state(phi):
    """Single photon through the full Mach-Zehnder."""
    state = apply(BS50, basis_state(1, 0))
    state = apply(phase_shifter(phi, "b"), state)
    return apply(RECOMBINER, state)


def mz_prob(phi):
    """Probability the photon exits in mode a: cos^2(phi/2)."""
    return prob(mz_state(phi), 1, 0)


def mz_prob_marked(phi, marking):
    """Fringe with a labelled which-path marking fraction m in [0, 1].

    The marked fraction carries no phase information and splits
    evenly; the unmarked fraction interferes perfectly.
    """
    return (1.0 - marking) * mz_prob(phi) + marking * 0.5


def fringe_visibility(prob_fn, samples=721):
    """(max - min) / (max + min) of a fringe sampled over [0, 2 pi)."""
    values = [prob_fn(2.0 * math.pi * i / (samples - 1))
              for i in range(samples)]
    hi, lo = max(values), min(values)
    return (hi - lo) / (hi + lo) if hi + lo > 0 else 0.0


def mz_visibility(marking=0.0):
    return fringe_visibility(lambda phi: mz_prob_marked(phi, marking))


def phase_precision(visibility, photon_count):
    """Shot-noise phase note: dphi ~ 1 / (V sqrt(N)) radians."""
    return 1.0 / (visibility * math.sqrt(photon_count))


# ================================================================ 5. Photon statistics + g2(0)
# Three textbook photon-number distributions, each truncated far
# into its tail (n <= 64) so the moments are honest:
#   coherent (laser-like):  Poisson,        g2(0) = 1
#   single-photon Fock |1>: delta at n = 1, g2(0) = 0 (antibunched)
#   thermal (lamp-like):    Bose geometric, g2(0) = 2 (bunched)
# g2(0) = <n(n-1)> / <n>^2 is COMPUTED from each distribution, never
# written in as the answer - the checks compare it to the theory.

STATS_TERMS = 64


def poisson_dist(mu, terms=STATS_TERMS):
    """Coherent-state photon counts: P(n) = e^-mu mu^n / n!."""
    return [math.exp(-mu) * mu ** n / math.factorial(n)
            for n in range(terms)]


def fock_dist(n0, terms=STATS_TERMS):
    """Fock state |n0>: every count is exactly n0."""
    return [1.0 if n == n0 else 0.0 for n in range(terms)]


def thermal_dist(mu_bar, terms=STATS_TERMS):
    """Thermal (Bose) counts: P(n) = (1/(1+mu)) (mu/(1+mu))^n."""
    p = mu_bar / (1.0 + mu_bar)
    return [(1.0 - p) * p ** n for n in range(terms)]


def dist_mean(dist):
    return sum(n * p for n, p in enumerate(dist))


def dist_g2(dist):
    """Second-order coherence g2(0) = <n(n-1)> / <n>^2."""
    mean = dist_mean(dist)
    if mean == 0:
        return 0.0
    factorial_moment = sum(n * (n - 1) * p for n, p in enumerate(dist))
    return factorial_moment / mean ** 2


def statistics_report(mu=2.0):
    """Computed means and g2(0) for the three light characters."""
    rows = {}
    for name, dist in (("coherent", poisson_dist(mu)),
                       ("single_photon_fock", fock_dist(1)),
                       ("thermal", thermal_dist(mu))):
        rows[name] = {"mean": dist_mean(dist), "g2": dist_g2(dist),
                      "total_probability": sum(dist)}
    rows["two_photon_fock"] = {"mean": dist_mean(fock_dist(2)),
                               "g2": dist_g2(fock_dist(2)),
                               "total_probability": sum(fock_dist(2))}
    return rows


# ================================================================ 6. NOON state: phase super-resolution
# The HOM output (|0,2> - |2,0>) / sqrt(2) IS the N = 2 NOON state:
# both photons together in one arm or the other. A phase phi on
# mode b therefore lands TWICE on the |0,2> component (e^{i 2 phi}),
# and after the recombiner the coincidence probability P(1,1)
# fringes as cos^2(phi) - two full fringes where a single photon
# shows one. That doubled frequency is phase super-resolution,
# computed here from the same unitaries; it is not a metrology
# result (HOLD).

def noon_state():
    """The N = 2 NOON state, produced by the HOM beam splitter."""
    return hom_output()


def noon_prob(phi):
    """Coincidence P(1,1) after phase phi and the recombiner.

    The standard NOON readout is the coincidence channel: it
    fringes as cos^2(phi), twice the single-photon frequency.
    """
    state = apply(phase_shifter(phi, "b"), noon_state())
    return prob(apply(RECOMBINER, state), 1, 1)


def fringe_minima(prob_fn, samples=1441):
    """Count interior fringe minima over phi in [0, 2 pi)."""
    values = [prob_fn(2.0 * math.pi * i / samples) for i in range(samples)]
    count = 0
    for i in range(samples):
        prev_v = values[(i - 1) % samples]
        next_v = values[(i + 1) % samples]
        if values[i] < prev_v and values[i] <= next_v and values[i] < 0.01:
            count += 1
    return count


# ================================================================ 7. kNN light-character classifier
# Features: (g2(0), HOM coincidence rate, fringe visibility). Every
# training row is labelled by the lab's own character model below,
# and every scenario in the report takes its features from the
# lab's own benches - the statistics bench (section 5), the HOM
# bench (section 3), and the Mach-Zehnder bench (section 4) - so
# the classifier interpolates measurements this file actually made.

def model_label(g2, coincidence, visibility):
    """The lab's light-character model distilled to a label.

    g2(0) is the decisive statistic, as it is on a real bench:
    thermal bunching doubles it, a laser leaves it at 1, a Fock
    state kills the n(n-1) moment, and a two-photon Fock state
    halves it. Coincidence separates a true single-photon stream
    (antibunched AND no coincidences) from pair light.
    """
    if g2 >= 1.5:
        return "thermal"
    if g2 >= 0.75:
        return "coherent"
    if g2 >= 0.25:
        return "bunched-pair"
    if coincidence <= 0.10:
        return "single-photon"
    return "bunched-pair"


def _training_grid():
    rows = []
    for g2 in (0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0):
        for coincidence in (0.0, 0.05, 0.25, 0.5):
            for visibility in (0.0, 0.5, 1.0):
                rows.append(((g2, coincidence, visibility),
                             model_label(g2, coincidence, visibility)))
    return rows


TRAINING_GRID = _training_grid()


def _scaled(features):
    g2, coincidence, visibility = features
    return (g2 / 2.0, coincidence, visibility)


def classify_light(g2, coincidence, visibility, k=5):
    """kNN over the model-labelled grid, deterministic tie-breaking."""
    target = _scaled((g2, coincidence, visibility))
    ranked = []
    for features, label in TRAINING_GRID:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    votes = {}
    for _, _, label in ranked[:k]:
        votes[label] = votes.get(label, 0) + 1
    priority = {"single-photon": 0, "bunched-pair": 1,
                "coherent": 2, "thermal": 3}
    return sorted(votes.items(), key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def bench_features():
    """Feature rows measured on this lab's own benches."""
    stats = statistics_report()
    return {
        "heralded_single_photon": (
            stats["single_photon_fock"]["g2"],
            hom_coincidence_indistinguishable(),
            mz_visibility(0.0)),
        "attenuated_laser": (
            stats["coherent"]["g2"],
            hom_coincidence_distinguishable(),
            mz_visibility(0.0)),
        "thermal_lamp": (
            stats["thermal"]["g2"],
            hom_coincidence_distinguishable(),
            mz_visibility(0.0)),
        "bunched_photon_pair": (
            stats["two_photon_fock"]["g2"],
            prob(apply(BS50, basis_state(2, 0)), 1, 1),
            fringe_visibility(noon_prob)),
    }


def classifier_report():
    return {name: classify_light(*features)
            for name, features in bench_features().items()}


# ================================================================ 8. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="quantumphotonics-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all real-photon / sensing / comms gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="quantumphotonics-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Say it in the first line of every report: these are exact amplitudes in a truncated toy basis, not photons - then show the HOM cancellation, the g2 table computed from the distributions, and the marking fraction that priced the lost visibility.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["two photon wave packets arriving at one beam splitter cube",
                  "both photons leaving through the same port, coincidence counter dark",
                  "a Mach-Zehnder diamond with a phase dial sweeping its fringe",
                  "a which-path tag fading the fringe to a flat line",
                  "Poisson, delta, and Bose histograms standing side by side"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    def close(a, b, tol=1e-9):
        return abs(a - b) <= tol

    # 1. Fock space + exact unitaries
    chk("basis_size_10", DIM == 10
        and all(na + nb <= MAX_PHOTONS for na, nb in BASIS))
    chk("bs50_unitary", unitarity_error(BS50) < 1e-9)
    chk("bs_general_unitary", unitarity_error(beam_splitter(0.3)) < 1e-9)
    chk("phase_shifter_unitary", unitarity_error(phase_shifter(0.7)) < 1e-9)
    chk("bs_zero_is_identity",
        close(prob(apply(beam_splitter(0.0), basis_state(1, 0)), 1, 0), 1.0, 1e-12))
    split = apply(BS50, basis_state(1, 0))
    chk("single_photon_split_even",
        close(prob(split, 1, 0), 0.5, 1e-12)
        and close(prob(split, 0, 1), 0.5, 1e-12))
    chk("probability_conserved", close(total_probability(hom_output()), 1.0, 1e-12))

    # 2. Hong-Ou-Mandel effect
    chk("hom_coincidence_zero", hom_coincidence_indistinguishable() < 1e-9)
    out = hom_output()
    chk("hom_output_is_noon",
        close(prob(out, 2, 0), 0.5, 1e-9) and close(prob(out, 0, 2), 0.5, 1e-9)
        and close(out[INDEX[(2, 0)]].real, -1.0 / math.sqrt(2), 1e-9)
        and close(out[INDEX[(0, 2)]].real, 1.0 / math.sqrt(2), 1e-9))
    chk("hom_distinguishable_half",
        close(hom_coincidence_distinguishable(), 0.5, 1e-12))
    chk("hom_partial_overlap",
        hom_coincidence(1.0) == 0.0 and hom_coincidence(0.0) == 0.5
        and close(hom_coincidence(0.5), 0.375, 1e-12))
    curve = hom_dip_curve()
    chk("hom_dip_curve",
        curve[0][1] < 1e-12
        and all(curve[i][1] < curve[i + 1][1] for i in range(len(curve) - 1))
        and close(curve[-1][1], (1.0 - math.exp(-9.0)) / 2.0, 1e-9))
    chk("hom_dip_visibility_one", close(hom_dip_visibility(), 1.0, 1e-9))

    # 3. Mach-Zehnder fringes + which-path marking
    chk("mz_fringe_formula",
        all(close(mz_prob(phi), math.cos(phi / 2.0) ** 2, 1e-9)
            for phi in (0.0, 0.7, math.pi / 2, math.pi, 4.0)))
    chk("mz_full_switch_at_pi",
        mz_prob(math.pi) < 1e-9
        and close(prob(mz_state(math.pi), 0, 1), 1.0, 1e-9))
    chk("mz_visibility_ideal", close(mz_visibility(0.0), 1.0, 1e-3))
    chk("mz_visibility_marked",
        close(mz_visibility(0.4), 0.6, 1e-3)
        and close(mz_visibility(1.0), 0.0, 1e-3))
    chk("phase_precision_note",
        close(phase_precision(1.0, 10000), 0.01, 1e-12)
        and close(phase_precision(0.6, 10000), 1.0 / 60.0, 1e-9))

    # 4. Photon statistics: g2(0) computed from the distributions
    stats = statistics_report()
    chk("poisson_normalised",
        close(stats["coherent"]["total_probability"], 1.0, 1e-9)
        and close(stats["coherent"]["mean"], 2.0, 1e-9))
    chk("poisson_g2_one", close(stats["coherent"]["g2"], 1.0, 1e-6))
    chk("fock_g2_zero", stats["single_photon_fock"]["g2"] == 0.0)
    chk("fock2_g2_half", close(stats["two_photon_fock"]["g2"], 0.5, 1e-12))
    chk("thermal_g2_two",
        close(stats["thermal"]["g2"], 2.0, 1e-6)
        and close(stats["thermal"]["mean"], 2.0, 1e-6))

    # 5. NOON state: doubled fringe frequency
    chk("noon_fringe_formula",
        all(close(noon_prob(phi), math.cos(phi) ** 2, 1e-9)
            for phi in (0.3, math.pi / 2, 2.0, math.pi)))
    chk("noon_super_resolution_contrast",
        noon_prob(math.pi / 2) < 1e-9
        and close(mz_prob(math.pi / 2), 0.5, 1e-9)
        and close(noon_prob(math.pi), 1.0, 1e-9)
        and mz_prob(math.pi) < 1e-9)
    chk("noon_minima_doubled",
        fringe_minima(noon_prob) == 2 and fringe_minima(mz_prob) == 1)
    chk("noon_visibility_one", close(fringe_visibility(noon_prob), 1.0, 1e-3))

    # 6. classifier - labels come from the lab's own character model
    rep = classifier_report()
    chk("classifier_single_photon", rep["heralded_single_photon"] == "single-photon")
    chk("classifier_coherent", rep["attenuated_laser"] == "coherent")
    chk("classifier_thermal", rep["thermal_lamp"] == "thermal")
    chk("classifier_bunched_pair", rep["bunched_photon_pair"] == "bunched-pair")
    chk("classifier_matches_model",
        all(classify_light(*features) == model_label(*features)
            for features in bench_features().values()))
    chk("pair_coincidence_from_unitary",
        close(prob(apply(BS50, basis_state(2, 0)), 1, 1), 0.5, 1e-9))

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_source_hold", gate("real_photon_source_claim") == "HOLD")
    chk("gate_comms_hold", gate("quantum_communication_claim") == "HOLD")
    chk("gate_sensing_hold", gate("quantum_sensing_claim") == "HOLD")
    chk("gate_entanglement_hold", gate("entanglement_certification_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("QuantumPhotonics-Lab - single-photon optics lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - exact amplitudes, toy photons")
    print("    This lab computes EXACT amplitudes in a truncated two-mode")
    print("    Fock space (<= 3 photons). Beam splitters and phase shifters")
    print("    conserve photon number, so the truncation loses nothing.")
    print("    There are no real photons here: no source, no detector, no")
    print("    measurement - and no sensing or comms result of any kind.")
    print(f"\n[2] Fock bench - {DIM} basis states, unitarity proven in-file")
    print(f"    basis states {DIM} | BS(50:50) unitarity error "
          f"{unitarity_error(BS50):.2e} | BS(0.3 rad) error "
          f"{unitarity_error(beam_splitter(0.3)):.2e}")
    split = apply(BS50, basis_state(1, 0))
    print(f"    one photon at 50:50 -> P(1,0) {prob(split, 1, 0):.4f} | "
          f"P(0,1) {prob(split, 0, 1):.4f}")
    print("\n[3] Hong-Ou-Mandel - two photons walk into a beam splitter")
    print(f"    indistinguishable: coincidence "
          f"{hom_coincidence_indistinguishable():.2e} (they bunch: "
          f"P(2,0) {prob(hom_output(), 2, 0):.4f}, "
          f"P(0,2) {prob(hom_output(), 0, 2):.4f})")
    print(f"    distinguishable:   coincidence "
          f"{hom_coincidence_distinguishable():.4f} (classical T^2 + R^2)")
    print("    dip vs delay (labelled Gaussian overlap, sigma = 1):")
    for delay, p in hom_dip_curve():
        print(f"      delay {delay:3.1f} -> coincidence {p:.4f}")
    print(f"    dip visibility {hom_dip_visibility():.4f}")
    print("\n[4] Mach-Zehnder - one photon, two paths, one fringe")
    for phi in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        print(f"    phi {phi:5.3f} -> P(exit a) {mz_prob(phi):.4f} "
              f"(cos^2(phi/2) = {math.cos(phi / 2) ** 2:.4f})")
    print(f"    visibility: ideal {mz_visibility(0.0):.4f} | "
          f"40% which-path marked {mz_visibility(0.4):.4f} | "
          f"fully marked {mz_visibility(1.0):.4f}")
    print(f"    shot-noise note: dphi ~ {phase_precision(1.0, 10000):.4f} rad "
          f"at V = 1, N = 10000 ({phase_precision(0.6, 10000):.4f} rad "
          f"at V = 0.6) - a counting-statistics note, not a sensor.")
    print("\n[5] Photon statistics - g2(0) computed from each distribution")
    stats = statistics_report()
    for name in ("coherent", "single_photon_fock", "thermal",
                 "two_photon_fock"):
        row = stats[name]
        print(f"    {name:18s} mean {row['mean']:.4f} | "
              f"g2(0) {row['g2']:.4f}")
    print("    -> coherent 1, Fock |1> 0 (antibunched), thermal 2 (bunched),")
    print("       Fock |2> 1/2: the second-order coherence separates them.")
    print("\n[6] NOON state - the HOM output fringes twice as fast")
    for phi in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        print(f"    phi {phi:5.3f} -> coincidence NOON {noon_prob(phi):.4f} | "
              f"single photon {mz_prob(phi):.4f}")
    print(f"    fringe minima in [0, 2pi): NOON {fringe_minima(noon_prob)} | "
          f"single photon {fringe_minima(mz_prob)} - doubled frequency,")
    print("    phase super-resolution as arithmetic, not as a metrology claim.")
    print("\n[7] Light-character classifier (TinyML kNN, bench-fed features)")
    for name, label in classifier_report().items():
        g2, coinc, vis = bench_features()[name]
        print(f"    {name:24s} g2 {g2:.3f} coinc {coinc:.3f} "
              f"vis {vis:.3f} -> {label}")
    print("\n[8] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[9] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "hom":
        print(json.dumps({
            "coincidence_indistinguishable": hom_coincidence_indistinguishable(),
            "coincidence_distinguishable": hom_coincidence_distinguishable(),
            "dip_curve": hom_dip_curve(),
            "dip_visibility": hom_dip_visibility(),
            "noon_amplitudes": {
                "P(2,0)": prob(hom_output(), 2, 0),
                "P(1,1)": prob(hom_output(), 1, 1),
                "P(0,2)": prob(hom_output(), 0, 2)},
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "mz":
        print(json.dumps({
            "fringe": {f"{phi:.3f}": mz_prob(phi)
                       for phi in (0.0, math.pi / 2, math.pi,
                                   3 * math.pi / 2)},
            "visibility_ideal": mz_visibility(0.0),
            "visibility_marked_0.4": mz_visibility(0.4),
            "visibility_marked_1.0": mz_visibility(1.0),
            "phase_precision_V1_N10000": phase_precision(1.0, 10000),
            "phase_precision_V0.6_N10000": phase_precision(0.6, 10000),
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "stats":
        print(json.dumps(statistics_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "noon":
        print(json.dumps({
            "fringe": {f"{phi:.3f}": noon_prob(phi)
                       for phi in (0.0, math.pi / 2, math.pi,
                                   3 * math.pi / 2)},
            "minima_0_2pi": fringe_minima(noon_prob),
            "single_photon_minima_0_2pi": fringe_minima(mz_prob),
            "visibility": fringe_visibility(noon_prob),
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "quantum_sensing_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
