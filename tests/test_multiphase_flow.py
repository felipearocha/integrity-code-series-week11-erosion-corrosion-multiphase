"""Multiphase flow + Beggs-Brill tests."""
import math
import pytest
from src import multiphase_flow as mpf
from src import constants as C


@pytest.mark.parametrize("q,d", [(0.01, 0.1), (0.02, 0.15), (0.005, 0.05)])
def test_superficial_velocity(q, d):
    area = math.pi * d ** 2 / 4
    assert mpf.superficial_velocity(q, d) == pytest.approx(q / area)


def test_superficial_velocity_bad_diameter():
    with pytest.raises(ValueError):
        mpf.superficial_velocity(0.01, 0)


@pytest.mark.parametrize("ll", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_mixture_density_bounds(ll):
    rho = mpf.mixture_density(1000, 50, ll)
    assert 50 <= rho <= 1000


def test_mixture_density_endpoints():
    assert mpf.mixture_density(1000, 50, 1.0) == 1000
    assert mpf.mixture_density(1000, 50, 0.0) == 50


@pytest.mark.parametrize("wc", [0.0, 0.3, 0.5, 0.7, 1.0])
def test_liquid_density(wc):
    rho = mpf.liquid_density(1024, 850, wc)
    assert 850 <= rho <= 1024


@pytest.mark.parametrize("u,d", [(1, 0.1), (5, 0.1), (10, 0.15)])
def test_froude_positive(u, d):
    assert mpf.froude_number(u, d) > 0


def test_reynolds_bad_viscosity():
    with pytest.raises(ValueError):
        mpf.reynolds_number(1000, 5, 0.1, 0)


@pytest.mark.parametrize("cl,fr", [(0.001, 0.001), (0.1, 1), (0.5, 10),
                                    (0.9, 100), (0.3, 50), (0.05, 0.5)])
def test_regime_returns_valid(cl, fr):
    assert mpf.beggs_brill_regime(cl, fr) in (
        "segregated", "intermittent", "distributed", "transition")


@pytest.mark.parametrize("regime", ["segregated", "intermittent", "distributed"])
def test_holdup_at_least_no_slip(regime):
    h = mpf.beggs_brill_holdup(0.3, 10.0, regime)
    assert h >= 0.3 - 1e-9


@pytest.mark.parametrize("regime", ["segregated", "intermittent", "distributed", "transition"])
def test_holdup_bounded(regime):
    h = mpf.beggs_brill_holdup(0.4, 5.0, regime)
    assert 0 <= h <= 1


@pytest.mark.parametrize("ql,qg", [(0.01, 0.2), (0.02, 0.1), (0.005, 0.4)])
def test_resolve_flow_consistency(ql, qg):
    fs = mpf.resolve_flow(ql, qg, 0.1, watercut=0.5)
    assert fs.u_m == pytest.approx(fs.u_sl + fs.u_sg)
    assert 0 < fs.lambda_l < 1
    assert fs.regime in ("segregated", "intermittent", "distributed", "transition")


def test_resolve_flow_zero_total():
    with pytest.raises(ValueError):
        mpf.resolve_flow(0, 0, 0.1)


def test_high_gas_gives_distributed():
    fs = mpf.resolve_flow(0.001, 0.5, 0.1, watercut=0.5)
    assert fs.regime in ("distributed", "intermittent", "transition")


@pytest.mark.parametrize("d", [0.05, 0.1, 0.15, 0.2, 0.25])
def test_resolve_flow_diameters(d):
    fs = mpf.resolve_flow(0.01, 0.1, d, watercut=0.5)
    assert fs.rho_m > 0 and fs.mu_m > 0
