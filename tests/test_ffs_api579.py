"""API 579-1 Part 5 FFS tests."""
import pytest
from src import ffs_api579 as ffs
from src import constants as C


def test_rsf_allowable_value():
    assert C.API579_RSF_ALLOWABLE == 0.90


@pytest.mark.parametrize("p,r,s", [(5, 75, 138), (10, 50, 138), (2, 100, 120)])
def test_tmin_positive(p, r, s):
    assert ffs.t_min_pressure(p, r, s) > 0


def test_tmin_bad_combo():
    with pytest.raises(ValueError):
        ffs.t_min_pressure(300, 75, 138)


@pytest.mark.parametrize("ta", [12.7, 11, 10, 8, 6])
def test_rsf_decreases_with_loss(ta):
    full = ffs.remaining_strength_factor(12.7, 3.0, 12.7)
    assert ffs.remaining_strength_factor(ta, 3.0, 12.7) <= full + 1e-9


def test_rsf_bounds():
    assert 0 <= ffs.remaining_strength_factor(8, 3, 12.7) <= 1


def test_rsf_at_tmin_zero():
    assert ffs.remaining_strength_factor(3.0, 3.0, 12.7) == pytest.approx(0.0)


@pytest.mark.parametrize("rsf,expect", [(0.95, True), (0.90, True), (0.85, False), (0.5, False)])
def test_acceptable(rsf, expect):
    assert ffs.acceptable(rsf) is expect


def test_reduced_mawp_no_reduction():
    assert ffs.reduced_mawp(100, 0.95) == 100


def test_reduced_mawp_reduction():
    assert ffs.reduced_mawp(100, 0.45) == pytest.approx(100 * 0.45 / 0.90)


@pytest.mark.parametrize("rate", [0.1, 0.5, 1.0, 2.0, 5.0])
def test_remaining_life_decreases_with_rate(rate):
    base = ffs.remaining_life(12.7, 3.0, 0.1)
    assert ffs.remaining_life(12.7, 3.0, rate) <= base + 1e-9


def test_remaining_life_zero_rate_infinite():
    assert ffs.remaining_life(12.7, 3.0, 0) == float("inf")


def test_remaining_life_handcalc():
    assert ffs.remaining_life(12.7, 3.0, 1.0) == pytest.approx(9.7)
