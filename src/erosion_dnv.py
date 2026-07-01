"""
erosion_dnv.py - DNV-RP-O501 Rev.4.2 (2007) ductile particle-erosion model.
Designated by NORSOK P-002 Clause 8.6.4 as the empirical particle-erosion model.

[SOURCE: DNV-RP-O501 Rev.4.2 (2007) Sec.7-8]  T1
[SOURCE: NORSOK P-002 Clause 8.6.4 designating DNV-RP-O501]  T1
"""
from __future__ import annotations

import math

from . import constants as C


def f_alpha(alpha_deg: float) -> float:
    """Ductile angle function F(alpha), Rev.4.2 8-term polynomial (Table 7-1):
        F(a) = sum_{i=1..8} (-1)^(i+1) A_i (a_rad)^i
    Clamped to >=0 (the polynomial is only valid 0..90 deg for steel).
    [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Table 7-1, Eqs.7.2/7.3]  T1
    """
    a = math.radians(alpha_deg)
    total = 0.0
    for i, coeff in enumerate(C.DNV_FALPHA_COEFFS, start=1):
        total += ((-1) ** (i + 1)) * coeff * a ** i
    return max(total, 0.0)


def sand_mass_flow(sand_ppmw: float, q_l_m3s: float,
                   rho_l: float = C.RHO_WATER) -> float:
    """Sand mass flow [kg/s] from a ppm-by-weight loading on the liquid stream.
    m_dot_p = (sand_ppmw * 1e-6) * (rho_l * q_l)
    [SOURCE: NORSOK P-002 sand-load basis]  T2
    """
    liquid_mass_flow = rho_l * q_l_m3s     # kg/s
    return sand_ppmw * 1e-6 * liquid_mass_flow


def erosion_straight(m_dot_p: float, u_p: float, diameter_m: float) -> float:
    """Straight smooth steel pipe erosion (Eq.8.9):
        E_dot_L = 2.5e-5 * m_dot_p * U_p^2.6 * D^-2   [mm/year]
    [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Eq.8.9]  T1
    """
    if diameter_m <= 0:
        raise ValueError("diameter must be positive")
    return C.DNV_STRAIGHT_COEFF * m_dot_p * u_p ** C.DNV_N_STEEL * diameter_m ** -2


def characteristic_bend_angle(r_over_d: float) -> float:
    """Characteristic particle impact angle for a bend (Eq.8.15):
        alpha = arctan( 1 / (2*sqrt(R/D)) )   [deg]
    [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Eq.8.15]  T1
    """
    if r_over_d <= 0:
        raise ValueError("R/D must be positive")
    return math.degrees(math.atan(1.0 / (2.0 * math.sqrt(r_over_d))))


def erosion_bend(m_dot_p: float, u_p: float, diameter_m: float,
                 r_over_d: float = 1.5) -> float:
    """Pipe-bend (elbow) erosion rate (Rev.4.2 Sec.8.4, Eq.8.21 form):

        E_dot_L = [K * m_dot_p * U_p^n * F(alpha) / (rho_t * A_t)] * C1 * C_unit
        A_t = pi*D^2 / (4*sin(alpha))

    The angle dependence is carried by F(alpha) and by the 1/sin(alpha) inside
    A_t. There is NO additional standalone sin(alpha) in the numerator; adding
    one double-counts the impact angle and underpredicts bend erosion by a
    factor sin(alpha).

    Returns mm/year.
    [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Eqs.8.15-8.21]  T1
    """
    if diameter_m <= 0:
        raise ValueError("diameter must be positive")
    alpha = characteristic_bend_angle(r_over_d)
    a_rad = math.radians(alpha)
    sin_a = math.sin(a_rad)
    a_t = math.pi * diameter_m ** 2 / (4.0 * sin_a)
    fa = f_alpha(alpha)
    numerator = C.DNV_K_STEEL * m_dot_p * u_p ** C.DNV_N_STEEL * fa
    e_ms = numerator / (C.RHO_STEEL * a_t)
    return e_ms * C.DNV_C1_BEND * C.DNV_C_UNIT


def erosion_rate(m_dot_p: float, u_p: float, diameter_m: float,
                 component: str = "bend", r_over_d: float = 1.5) -> float:
    """Dispatch erosion rate by component type. Returns mm/year."""
    if component in ("bend", "elbow"):
        return erosion_bend(m_dot_p, u_p, diameter_m, r_over_d)
    if component == "straight":
        return erosion_straight(m_dot_p, u_p, diameter_m)
    raise ValueError(f"unknown component {component!r}")
