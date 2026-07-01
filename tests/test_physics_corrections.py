"""
Physics-correction tests (Week 11 remediation audit).

These encode the CORRECT physics that the audit found wrong or unbounded:
  - DNV bend erosion must NOT carry an extra sin(alpha) (the angle dependence is
    F(alpha) plus the 1/sin(alpha) already inside A_t).
  - The elbow wall-loss field must be clamped to the pipe wall thickness (metal
    loss cannot exceed the wall).
  - Beggs-Brill transition holdup must use the A-weighted interpolation, not a
    flat 0.5 blend.
  - NORSOK Eq.22 friction uses the cube root (1/3), not 0.33.
  - corrosion_rate must not silently extrapolate fCO2 outside NORSOK's window.
  - A proper API 579 Part-5 Level-1 RSF uses the Folias bulging factor Mt.

Written test-first: with the pre-remediation code these FAIL.
"""
import math

from src import constants as C
from src import erosion_dnv as ero
from src import multiphase_flow as mpf
from src import hydrodynamics as hyd
from src import elbow_field as ef
from src import corrosion_norsok as cor
from src import ffs_api579 as ffs


def test_bend_erosion_has_no_extra_sin_alpha():
    # DNV-RP-O501 bend: E = K*m*U^n*F(alpha)/(rho_t*A_t)*C1*C_unit, A_t = pi*D^2/(4 sin a).
    # The only angle factors are F(alpha) and the 1/sin(alpha) inside A_t.
    m_dot, u_p, d, rod = 1.0e-4, 15.0, 0.1, 1.5
    alpha = math.radians(ero.characteristic_bend_angle(rod))
    a_t = math.pi * d ** 2 / (4.0 * math.sin(alpha))
    fa = ero.f_alpha(math.degrees(alpha))
    expected = (C.DNV_K_STEEL * m_dot * u_p ** C.DNV_N_STEEL * fa) / (C.RHO_STEEL * a_t) \
        * C.DNV_C1_BEND * C.DNV_C_UNIT
    got = ero.erosion_bend(m_dot, u_p, d, rod)
    assert abs(got - expected) / expected < 0.01, (
        f"bend erosion carries a spurious sin(alpha): got {got:.5g}, expected {expected:.5g}")


def test_wall_loss_field_is_clamped_to_wall_thickness():
    # Aggressive rates over a long interval must not report metal loss beyond the wall.
    angles, circ, loss = ef.wall_loss_field(
        s_mean=100.0, e0_bend=5.0, c0_protected=8.0, c0_bare=12.0, service_years=20.0)
    peak, a_deg, c_deg = ef.peak_loss(angles, circ, loss)
    assert peak <= C.WALL_THICKNESS_MM + 1e-9, (
        f"wall loss {peak:.2f} mm exceeds the {C.WALL_THICKNESS_MM} mm wall")


def test_beggs_brill_transition_holdup_is_A_weighted():
    # transition E_L = A*E_seg + (1-A)*E_int, A=(L3-Fr)/(L3-L2); NOT a flat 0.5 blend.
    lam, fr = 0.36, 0.02
    regime = mpf.beggs_brill_regime(lam, fr)
    assert regime == "transition"
    l2 = 0.0009252 * lam ** (-2.4684)
    l3 = 0.10 * lam ** (-1.4516)
    a_w = (l3 - fr) / (l3 - l2)
    seg = mpf.beggs_brill_holdup(lam, fr, "segregated")
    inter = mpf.beggs_brill_holdup(lam, fr, "intermittent")
    expected = a_w * seg + (1.0 - a_w) * inter
    got = mpf.beggs_brill_holdup(lam, fr, "transition")
    assert abs(got - expected) < 1e-6, f"transition holdup not A-weighted: {got:.4f} vs {expected:.4f}"


def test_norsok_friction_uses_cube_root():
    # Eq.22 bracket is raised to 1/3, not 0.33.
    s = hyd.norsok_wall_shear(1000.0, 3.0, 0.1, 1.0e-3)
    term = 20000.0 * C.PIPE_ROUGHNESS / 0.1 + 1.0e6 * 1.0e-3 / (1000.0 * 3.0 * 0.1)
    f = C.NORSOK_FRICTION_C * (1.0 + term ** (1.0 / 3.0))
    expected = 0.5 * 1000.0 * f * 3.0 ** 2
    assert abs(s - expected) / expected < 1e-6, f"friction not cube-root: {s:.4f} vs {expected:.4f}"


def test_corrosion_rate_guards_fco2_envelope():
    # fCO2 well outside NORSOK's [0.1, 10] window must not be silently extrapolated
    # to an absurd rate; expect either a clamp (bounded) or a raised flag.
    cr = cor.corrosion_rate(60.0, 500.0, 500.0, 19.0, 4.0)
    assert cr < 60.0, f"fCO2 far outside envelope silently extrapolated to {cr:.1f} mm/yr"


def test_api579_rsf_uses_folias_bulging_factor():
    # A long shallow LTA (large 2c) must have a LOWER RSF than a short one at the
    # same depth, because the Folias factor Mt grows with flaw length.
    rsf_short = ffs.rsf_part5(t_actual=8.0, t_nominal=12.7,
                              lta_length_mm=20.0, radius_mm=150.0)
    rsf_long = ffs.rsf_part5(t_actual=8.0, t_nominal=12.7,
                             lta_length_mm=400.0, radius_mm=150.0)
    assert 0.0 <= rsf_long < rsf_short <= 1.0, (
        f"Part-5 RSF must fall with flaw length via Mt: short={rsf_short:.3f} long={rsf_long:.3f}")
