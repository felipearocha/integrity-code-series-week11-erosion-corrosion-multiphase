"""NORSOK M-506:2017 corrosion model tests."""
import math
import pytest
from src import corrosion_norsok as cor
from src import constants as C


@pytest.mark.parametrize("t_node", C.NORSOK_KT_TEMPS)
def test_cr_positive_at_each_node(t_node):
    cr = cor.corrosion_rate(t_node, 1.0, 50.0, 20.0, 5.0)
    assert cr > 0


@pytest.mark.parametrize("t_node", C.NORSOK_KT_TEMPS)
def test_kt_value_present(t_node):
    assert t_node in C.NORSOK_KT and C.NORSOK_KT[t_node] >= 0


def test_kt_has_nine_entries_2017():
    # 2017 edition includes 5 C and 15 C (regression vs outdated Rev.1)
    assert len(C.NORSOK_KT) == 9
    assert 5 in C.NORSOK_KT and 15 in C.NORSOK_KT


def test_kt_5c_value():
    assert C.NORSOK_KT[5] == pytest.approx(0.42)


def test_kt_15c_value():
    assert C.NORSOK_KT[15] == pytest.approx(1.59)


def test_kt_peaks_at_60():
    assert C.NORSOK_KT[60] == max(C.NORSOK_KT.values())


@pytest.mark.parametrize("t_node,expected", list(C.NORSOK_KT.items()))
def test_kt_regression_values(t_node, expected):
    assert C.NORSOK_KT[t_node] == pytest.approx(expected)


def test_cr_node_20c_handcalc():
    t_k = 293.15
    a = 10 ** (20.0 * (0.0031 - 1.4 / t_k))
    fco2 = a * 1.0
    fph = 2.0676 - 0.2309 * 4.0
    se = 0.146 + 0.0324 * math.log10(fco2)
    expected = 4.762 * fco2 ** 0.62 * (19.0 / 19.0) ** se * fph
    assert cor.corrosion_rate(20, 1.0, 20.0, 19.0, 4.0) == pytest.approx(expected, rel=0.01)


def test_cr_5c_drops_shear_term():
    # at 5 C, shear must not matter (Eq.3)
    a = cor.corrosion_rate(5, 1.0, 30.0, 5.0, 4.5)
    b = cor.corrosion_rate(5, 1.0, 30.0, 150.0, 4.5)
    assert a == pytest.approx(b, rel=1e-9)


def test_cr_15c_uses_low_exponent():
    # 15 C uses fugacity exponent 0.36, distinct from 20 C 0.62
    assert C.NORSOK_FCO2_EXP_LOWT == 0.36


@pytest.mark.parametrize("shear", [5, 10, 20, 50, 100])
def test_cr_increases_with_shear_at_60c(shear):
    base = cor.corrosion_rate(60, 1.0, 50.0, 1.0, 5.0)
    assert cor.corrosion_rate(60, 1.0, 50.0, shear, 5.0) >= base


@pytest.mark.parametrize("ph", [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5])
def test_cr_decreases_with_ph_at_60c(ph):
    # higher pH -> generally lower corrosion (more protective)
    low = cor.corrosion_rate(60, 1.0, 50.0, 20.0, 3.5)
    assert cor.corrosion_rate(60, 1.0, 50.0, 20.0, ph) <= low + 1e-9


@pytest.mark.parametrize("t", [10, 25, 30, 50, 70, 100, 130])
def test_cr_interpolation_within_bracket(t):
    temps = C.NORSOK_KT_TEMPS
    lower = max(x for x in temps if x <= t)
    upper = min(x for x in temps if x >= t)
    cr = cor.corrosion_rate(t, 1.0, 50.0, 20.0, 5.0)
    cl = cor.corrosion_rate(lower, 1.0, 50.0, 20.0, 5.0)
    cu = cor.corrosion_rate(upper, 1.0, 50.0, 20.0, 5.0)
    assert min(cl, cu) - 1e-6 <= cr <= max(cl, cu) + 1e-6


def test_fugacity_below_250bar():
    t_k = 333.15
    expected = 10 ** (100 * (0.0031 - 1.4 / t_k))
    assert cor.fugacity_coefficient(100, t_k) == pytest.approx(expected)


def test_fugacity_capped_at_250bar():
    t_k = 333.15
    assert cor.fugacity_coefficient(400, t_k) == cor.fugacity_coefficient(250, t_k)


@pytest.mark.parametrize("t_node", C.NORSOK_KT_TEMPS)
@pytest.mark.parametrize("ph", [3.6, 4.0, 4.6, 5.0, 5.5, 6.0, 6.4])
def test_fph_positive(t_node, ph):
    assert cor.f_ph(t_node, ph) > 0


def test_applicability_h2s_limit():
    ok, _ = cor.is_applicable(1.0, 0.1)
    assert not ok


def test_applicability_ratio_limit():
    ok, _ = cor.is_applicable(1.0, 0.06)  # ratio < 20
    assert not ok


def test_applicability_pass():
    ok, _ = cor.is_applicable(2.0, 0.0)
    assert ok


@pytest.mark.parametrize("t", [5, 20, 40, 60, 80, 90, 120, 150])
def test_cr_zero_pco2_floor(t):
    cr = cor.corrosion_rate(t, C.NORSOK_FCO2_MIN, 50.0, 20.0, 5.0)
    assert cr >= 0
