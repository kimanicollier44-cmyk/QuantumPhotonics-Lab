"""Tests for QuantumPhotonics-Lab: Fock optics, HOM, MZ, stats, gates."""
import math

import pytest

import main as m


# ---- Fock space + unitaries
def test_basis_size():
    assert m.DIM == 10
    assert all(na + nb <= 3 for na, nb in m.BASIS)


def test_bs50_unitary():
    assert m.unitarity_error(m.BS50) < 1e-9


def test_bs_general_unitary():
    assert m.unitarity_error(m.beam_splitter(0.3)) < 1e-9
    assert m.unitarity_error(m.beam_splitter(1.1)) < 1e-9


def test_phase_shifter_unitary():
    assert m.unitarity_error(m.phase_shifter(0.7)) < 1e-9


def test_bs_zero_is_identity():
    out = m.apply(m.beam_splitter(0.0), m.basis_state(1, 0))
    assert m.prob(out, 1, 0) == pytest.approx(1.0, abs=1e-12)


def test_single_photon_split_even():
    out = m.apply(m.BS50, m.basis_state(1, 0))
    assert m.prob(out, 1, 0) == pytest.approx(0.5, abs=1e-12)
    assert m.prob(out, 0, 1) == pytest.approx(0.5, abs=1e-12)


def test_probability_conserved():
    assert m.total_probability(m.hom_output()) == pytest.approx(1.0, abs=1e-12)


# ---- Hong-Ou-Mandel
def test_hom_coincidence_zero():
    assert m.hom_coincidence_indistinguishable() < 1e-9


def test_hom_output_is_noon():
    out = m.hom_output()
    assert m.prob(out, 2, 0) == pytest.approx(0.5, abs=1e-9)
    assert m.prob(out, 0, 2) == pytest.approx(0.5, abs=1e-9)
    assert out[m.INDEX[(2, 0)]].real == pytest.approx(-1 / math.sqrt(2), abs=1e-9)
    assert out[m.INDEX[(0, 2)]].real == pytest.approx(1 / math.sqrt(2), abs=1e-9)


def test_hom_distinguishable_half():
    assert m.hom_coincidence_distinguishable() == pytest.approx(0.5, abs=1e-12)


def test_hom_partial_overlap():
    assert m.hom_coincidence(1.0) == 0.0
    assert m.hom_coincidence(0.0) == 0.5
    assert m.hom_coincidence(0.5) == pytest.approx(0.375, abs=1e-12)


def test_hom_dip_curve_rises_to_classical():
    curve = m.hom_dip_curve()
    assert curve[0][1] < 1e-12
    assert all(curve[i][1] < curve[i + 1][1] for i in range(len(curve) - 1))
    assert curve[-1][1] == pytest.approx((1 - math.exp(-9.0)) / 2, abs=1e-9)


def test_hom_dip_visibility():
    assert m.hom_dip_visibility() == pytest.approx(1.0, abs=1e-9)


# ---- Mach-Zehnder
@pytest.mark.parametrize("phi", [0.0, 0.7, math.pi / 2, math.pi, 4.0])
def test_mz_fringe_formula(phi):
    assert m.mz_prob(phi) == pytest.approx(math.cos(phi / 2) ** 2, abs=1e-9)


def test_mz_full_switch_at_pi():
    assert m.mz_prob(math.pi) < 1e-9
    assert m.prob(m.mz_state(math.pi), 0, 1) == pytest.approx(1.0, abs=1e-9)


def test_mz_visibility_ideal():
    assert m.mz_visibility(0.0) == pytest.approx(1.0, abs=1e-3)


def test_mz_visibility_marked():
    assert m.mz_visibility(0.4) == pytest.approx(0.6, abs=1e-3)
    assert m.mz_visibility(1.0) == pytest.approx(0.0, abs=1e-3)


def test_phase_precision_note():
    assert m.phase_precision(1.0, 10000) == pytest.approx(0.01, abs=1e-12)
    assert m.phase_precision(0.6, 10000) == pytest.approx(1 / 60, abs=1e-9)


# ---- photon statistics
def test_poisson_normalised_and_mean():
    stats = m.statistics_report()
    assert stats["coherent"]["total_probability"] == pytest.approx(1.0, abs=1e-9)
    assert stats["coherent"]["mean"] == pytest.approx(2.0, abs=1e-9)


def test_g2_values():
    stats = m.statistics_report()
    assert stats["coherent"]["g2"] == pytest.approx(1.0, abs=1e-6)
    assert stats["single_photon_fock"]["g2"] == 0.0
    assert stats["thermal"]["g2"] == pytest.approx(2.0, abs=1e-6)
    assert stats["two_photon_fock"]["g2"] == pytest.approx(0.5, abs=1e-12)


def test_thermal_mean():
    assert m.statistics_report()["thermal"]["mean"] == pytest.approx(2.0, abs=1e-6)


# ---- NOON state
@pytest.mark.parametrize("phi", [0.3, math.pi / 2, 2.0, math.pi])
def test_noon_fringe_formula(phi):
    assert m.noon_prob(phi) == pytest.approx(math.cos(phi) ** 2, abs=1e-9)


def test_noon_super_resolution_contrast():
    assert m.noon_prob(math.pi / 2) < 1e-9
    assert m.mz_prob(math.pi / 2) == pytest.approx(0.5, abs=1e-9)
    assert m.noon_prob(math.pi) == pytest.approx(1.0, abs=1e-9)
    assert m.mz_prob(math.pi) < 1e-9


def test_noon_minima_doubled():
    assert m.fringe_minima(m.noon_prob) == 2
    assert m.fringe_minima(m.mz_prob) == 1


def test_noon_visibility():
    assert m.fringe_visibility(m.noon_prob) == pytest.approx(1.0, abs=1e-3)


def test_pair_coincidence_from_unitary():
    out = m.apply(m.BS50, m.basis_state(2, 0))
    assert m.prob(out, 1, 1) == pytest.approx(0.5, abs=1e-9)


# ---- classifier
def test_classifier_report():
    rep = m.classifier_report()
    assert rep["heralded_single_photon"] == "single-photon"
    assert rep["attenuated_laser"] == "coherent"
    assert rep["thermal_lamp"] == "thermal"
    assert rep["bunched_photon_pair"] == "bunched-pair"


def test_classifier_matches_model_on_benches():
    for features in m.bench_features().values():
        assert m.classify_light(*features) == m.model_label(*features)


# ---- gates + seats
def test_hold_gates_14():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_gates_hold():
    assert m.gate("real_photon_source_claim") == "HOLD"
    assert m.gate("quantum_communication_claim") == "HOLD"
    assert m.gate("quantum_sensing_claim") == "HOLD"
    assert m.gate("entanglement_certification_claim") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_council_seats():
    brains = m.brains_report()
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["decider"]["can_override_hold"] is False
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False
    assert brains["flow"]["live"] == 0


def test_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]
    assert len(checks) == 42
