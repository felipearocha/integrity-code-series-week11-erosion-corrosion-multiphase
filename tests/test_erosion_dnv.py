"""DNV-RP-O501 erosion model tests."""
import math
import pytest
from src import erosion_dnv as ero
from src import constants as C


def test_straight_handcalc():
    expected = 2.5e-5 * 1e-4 * 10.0 ** 2.6 * 0.1 ** -2
    assert ero.erosion_straight(1e-4, 10.0, 0.1) == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("u", [2, 4, 6, 8, 10, 15, 20])
def test_erosion_increases_with_velocity(u):
    base = ero.erosion_straight(1e-4, 1.0, 0.1)
    assert ero.erosion_straight(1e-4, u, 0.1) >= base


@pytest.mark.parametrize("m", [1e-5, 1e-4, 1e-3, 1e-2])
def test_erosion_linear_in_sand(m):
    e1 = ero.erosion_straight(1e-5, 10, 0.1)
    ratio = ero.erosion_straight(m, 10, 0.1) / e1
    assert ratio == pytest.approx(m / 1e-5, rel=1e-6)


@pytest.mark.parametrize("d", [0.05, 0.1, 0.15, 0.2, 0.25])
def test_erosion_decreases_with_diameter(d):
    big = ero.erosion_straight(1e-4, 10, 0.05)
    assert ero.erosion_straight(1e-4, 10, d) <= big + 1e-12


@pytest.mark.parametrize("rd", [1.0, 1.5, 2.0, 3.0, 5.0])
def test_bend_angle_decreases_with_rd(rd):
    a_small = ero.characteristic_bend_angle(1.0)
    assert ero.characteristic_bend_angle(rd) <= a_small + 1e-9


def test_bend_angle_handcalc():
    expected = math.degrees(math.atan(1.0 / (2.0 * math.sqrt(1.5))))
    assert ero.characteristic_bend_angle(1.5) == pytest.approx(expected)


@pytest.mark.parametrize("a", range(0, 91, 5))
def test_falpha_nonnegative(a):
    assert ero.f_alpha(a) >= 0


@pytest.mark.parametrize("a", range(0, 91, 5))
def test_falpha_bounded(a):
    assert ero.f_alpha(a) <= 1.2


def test_falpha_zero_at_zero():
    assert ero.f_alpha(0) == pytest.approx(0.0, abs=1e-9)


def test_falpha_plateau_in_ductile_range():
    vals = [(a, ero.f_alpha(a)) for a in range(1, 91)]
    peak = max(vals, key=lambda t: t[1])[0]
    assert 25 <= peak <= 45


def test_falpha_ductile_exceeds_normal():
    assert ero.f_alpha(30) > 1.4 * ero.f_alpha(90)


@pytest.mark.parametrize("rd", [1.0, 1.5, 2.0, 3.0, 5.0])
def test_bend_erosion_positive(rd):
    assert ero.erosion_bend(1e-3, 10.0, 0.1, rd) > 0


@pytest.mark.parametrize("u", [5, 10, 15, 20])
def test_bend_erosion_increases_with_velocity(u):
    base = ero.erosion_bend(1e-3, 1.0, 0.1, 1.5)
    assert ero.erosion_bend(1e-3, u, 0.1, 1.5) >= base


def test_sand_mass_flow_scales():
    a = ero.sand_mass_flow(10, 0.01)
    b = ero.sand_mass_flow(20, 0.01)
    assert b == pytest.approx(2 * a, rel=1e-9)


def test_sand_mass_flow_zero():
    assert ero.sand_mass_flow(0, 0.01) == 0


def test_erosion_dispatch_bend():
    assert ero.erosion_rate(1e-3, 10, 0.1, "bend") > 0


def test_erosion_dispatch_straight():
    assert ero.erosion_rate(1e-3, 10, 0.1, "straight") > 0


def test_erosion_dispatch_unknown():
    with pytest.raises(ValueError):
        ero.erosion_rate(1e-3, 10, 0.1, "tee")


def test_material_constants_dnv():
    assert C.DNV_K_STEEL == 2.0e-9
    assert C.DNV_N_STEEL == 2.6
    assert C.DNV_C1_BEND == 2.5
