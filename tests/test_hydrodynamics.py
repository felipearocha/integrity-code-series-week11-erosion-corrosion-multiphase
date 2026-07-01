"""Hydrodynamics: shear, friction, mass transfer, elbow profile."""
import math
import pytest
from src import hydrodynamics as hyd
from src import constants as C


@pytest.mark.parametrize("u", [1, 3, 5, 8, 12])
def test_shear_increases_with_velocity(u):
    base = hyd.norsok_wall_shear(800, 1.0, 0.1, 1e-3)
    assert hyd.norsok_wall_shear(800, u, 0.1, 1e-3) >= base


def test_shear_bad_inputs():
    with pytest.raises(ValueError):
        hyd.norsok_wall_shear(800, 0, 0.1, 1e-3)


@pytest.mark.parametrize("re", [4e3, 1e4, 5e4, 1e5])
def test_blasius_positive(re):
    assert hyd.blasius_friction(re) > 0


def test_blasius_handcalc():
    assert hyd.blasius_friction(1e4) == pytest.approx(0.0791 * 1e4 ** -0.25)


def test_blasius_bad():
    with pytest.raises(ValueError):
        hyd.blasius_friction(0)


@pytest.mark.parametrize("re", [1e4, 2e4, 4e4, 7e4, 1e5])
def test_sherwood_increases_with_re(re):
    base = hyd.sherwood_berger_hau(1e4, 2000)
    assert hyd.sherwood_berger_hau(re, 2000) >= base


def test_sherwood_handcalc():
    expected = 0.0165 * 4e4 ** 0.86 * 2244 ** 0.33
    assert hyd.sherwood_berger_hau(4e4, 2244) == pytest.approx(expected)


@pytest.mark.parametrize("mu,rho", [(1e-3, 1000), (5e-4, 900), (2e-3, 1024)])
def test_schmidt_positive(mu, rho):
    assert hyd.schmidt_number(mu, rho) > 0


def test_mtc_positive():
    assert hyd.mass_transfer_coefficient(1000, 0.1) > 0


@pytest.mark.parametrize("comp,exp", [
    ("straight", C.ENH_STRAIGHT), ("after_elbow", C.ENH_AFTER_ELBOW),
    ("elbow", C.ENH_ELBOW), ("elbow_after_orifice", C.ENH_ELBOW_AFTER_ORIFICE)])
def test_geometry_enhancement(comp, exp):
    assert hyd.geometry_enhancement(comp) == exp


def test_enhancement_ordering():
    # severity ordering per Kim 2021
    assert (C.ENH_STRAIGHT < C.ENH_AFTER_ELBOW < C.ENH_ELBOW
            < C.ENH_ELBOW_AFTER_ORIFICE)


def test_geometry_enhancement_unknown():
    with pytest.raises(ValueError):
        hyd.geometry_enhancement("weld")


def test_elbow_profile_lengths():
    angles, ext, intr = hyd.elbow_angular_shear_profile(10.0, 73)
    assert len(angles) == len(ext) == len(intr) == 73


def test_elbow_extrados_peaks_near_37():
    angles, ext, intr = hyd.elbow_angular_shear_profile(10.0, 91)
    peak_angle = angles[ext.index(max(ext))]
    assert 30 <= peak_angle <= 45


def test_elbow_intrados_peaks_early():
    angles, ext, intr = hyd.elbow_angular_shear_profile(10.0, 91)
    peak_angle = angles[intr.index(max(intr))]
    assert peak_angle <= 20


@pytest.mark.parametrize("s", [5, 10, 20, 50])
def test_elbow_profile_scales_with_mean(s):
    angles, ext, intr = hyd.elbow_angular_shear_profile(s, 37)
    assert max(ext) > s and max(intr) > s
