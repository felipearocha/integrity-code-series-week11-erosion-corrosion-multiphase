"""Integration tests of the coupled erosion-corrosion model."""
import math
import pytest
from src import ec_model as ecm


def _op(**kw):
    d = dict(q_l_m3s=0.01, q_g_m3s=0.1, diameter_m=0.1016, temp_c=60,
             p_total_bar=60, p_co2_bar=1.0, ph=5.5, watercut=0.5,
             sand_ppmw=10.0, r_over_d=1.5, component="elbow")
    d.update(kw)
    return ecm.Operating(**d)


def test_evaluate_returns_result():
    r = ecm.evaluate(_op())
    assert r.total_mm_yr > 0


@pytest.mark.parametrize("t", [20, 40, 60, 80, 90, 120])
def test_evaluate_across_temperature(t):
    r = ecm.evaluate(_op(temp_c=t))
    assert r.total_mm_yr > 0
    assert r.corrosion_protected_mm_yr >= 0


@pytest.mark.parametrize("sand", [0.5, 5, 10, 30, 100])
def test_more_sand_more_erosion(sand):
    base = ecm.evaluate(_op(sand_ppmw=0.5)).erosion_mm_yr
    assert ecm.evaluate(_op(sand_ppmw=sand)).erosion_mm_yr >= base - 1e-12


@pytest.mark.parametrize("ph", [3.6, 4.0, 4.5, 5.0, 5.5, 6.0])
def test_lower_ph_more_corrosion(ph):
    high = ecm.evaluate(_op(ph=6.0)).corrosion_protected_mm_yr
    assert ecm.evaluate(_op(ph=ph)).corrosion_protected_mm_yr >= high - 1e-9


def test_total_ge_components():
    r = ecm.evaluate(_op())
    assert r.total_mm_yr >= r.erosion_mm_yr + r.corrosion_protected_mm_yr - 1e-9


@pytest.mark.parametrize("ql,qg", [(0.005, 0.05), (0.01, 0.1), (0.02, 0.2),
                                    (0.008, 0.15), (0.015, 0.08)])
def test_evaluate_various_flows(ql, qg):
    r = ecm.evaluate(_op(q_l_m3s=ql, q_g_m3s=qg))
    assert r.shear_pa > 0 and r.sherwood > 0 and r.mtc > 0


def test_h2s_marks_inapplicable():
    r = ecm.evaluate(_op(p_h2s_bar=0.2))
    assert not r.applicable


def test_remaining_life_positive():
    op = _op()
    r = ecm.evaluate(op)
    rl = ecm.remaining_life_years(op, r)
    assert rl >= 0


@pytest.mark.parametrize("d", [0.0508, 0.1016, 0.1524, 0.2032, 0.254])
def test_evaluate_diameters(d):
    r = ecm.evaluate(_op(diameter_m=d))
    assert r.total_mm_yr > 0


@pytest.mark.parametrize("rd", [1.0, 1.5, 2.0, 3.0, 5.0])
def test_evaluate_bend_radii(rd):
    r = ecm.evaluate(_op(r_over_d=rd))
    assert r.erosion_mm_yr >= 0


def test_corrosion_augmentation_reasonable():
    r = ecm.evaluate(_op(sand_ppmw=100, q_g_m3s=0.3))
    assert r.corrosion_augmentation >= 1.0
