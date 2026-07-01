"""ASTM G119 synergy decomposition tests."""
import pytest
from src import synergy_g119 as syn
from src import constants as C


def test_g119_worked_example_arithmetic():
    ex = C.G119_EXAMPLE
    s = ex["T"] - ex["W0"] - ex["C0"]
    assert s == pytest.approx(135.9, rel=0.01)


def test_g119_corrosion_augmentation():
    ex = C.G119_EXAMPLE
    aug = ex["Cw"] / ex["C0"]
    assert aug == pytest.approx(1.79, rel=0.01)


@pytest.mark.parametrize("shear", [0, 5, 10, 20, 50, 100, 150])
def test_scale_removal_monotonic(shear):
    base = syn.scale_removal_fraction(0, 0)
    assert syn.scale_removal_fraction(shear, 0) >= base - 1e-12


@pytest.mark.parametrize("shear", [0, 10, 50, 150])
def test_scale_removal_bounded(shear):
    r = syn.scale_removal_fraction(shear, 1.0)
    assert 0 <= r <= 1


def test_scale_removal_zero_at_zero():
    assert syn.scale_removal_fraction(0, 0) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("e0,c0p,c0b,s", [
    (0.01, 1.0, 3.0, 10), (0.5, 2.0, 5.0, 50), (5.0, 4.0, 6.0, 200),
    (0.1, 0.5, 2.0, 5), (1.0, 3.0, 8.0, 100)])
def test_decompose_total_equals_sum(e0, c0p, c0b, s):
    r = syn.decompose(e0, c0p, c0b, s)
    assert r.total == pytest.approx(r.e0 + r.c0 + r.synergy)


@pytest.mark.parametrize("e0,c0p,c0b,s", [
    (0.01, 1.0, 3.0, 10), (0.5, 2.0, 5.0, 50), (5.0, 4.0, 6.0, 200)])
def test_synergy_equals_components(e0, c0p, c0b, s):
    r = syn.decompose(e0, c0p, c0b, s)
    assert r.synergy == pytest.approx(r.d_cw + r.d_wc)


def test_decompose_bare_floor():
    # if bare < protected, code clamps bare = protected
    r = syn.decompose(0.1, 5.0, 2.0, 50)
    assert r.d_cw >= 0


@pytest.mark.parametrize("s", [10, 50, 150])
def test_higher_shear_more_synergy(s):
    low = syn.decompose(1.0, 2.0, 6.0, 5)
    high = syn.decompose(1.0, 2.0, 6.0, s)
    assert high.synergy >= low.synergy - 1e-9


def test_corrosion_augmentation_ge_one():
    r = syn.decompose(1.0, 2.0, 6.0, 100)
    assert r.corrosion_augmentation >= 1.0
