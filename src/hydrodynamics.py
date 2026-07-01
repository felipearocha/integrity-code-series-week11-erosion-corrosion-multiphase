"""
hydrodynamics.py - Wall shear stress and mass-transfer coefficient, including
elbow/bend enhancement.

[SOURCE: NORSOK M-506:2017 Clause 8.4, Eqs.21-22 wall shear]  T1
[SOURCE: Berger & Hau (1977) Sh = 0.0165 Re^0.86 Sc^0.33]  T1
[SOURCE: Blasius (1913) Fanning f = 0.0791 Re^-0.25]  T1
[SOURCE: El-Gammal et al. 2010; Kim et al. 2021 elbow peak location]  T1
"""
from __future__ import annotations

import math

from . import constants as C


def norsok_wall_shear(rho_m: float, u_m: float, diameter_m: float,
                      mu_m: float, roughness_m: float = C.PIPE_ROUGHNESS) -> float:
    """Mean wall shear stress (NORSOK M-506:2017 Eq.21-22):
        S = 0.5 * rho_m * f * u_m^2
        f = 0.001375 * [1 + (20000*k/D + 1e6*mu_m/(rho_m*u_m*D))^(1/3)]
    Returns S in Pa.
    [SOURCE: NORSOK M-506:2017 Clause 8.4, Eqs.21-22]  T1
    """
    if u_m <= 0 or diameter_m <= 0 or rho_m <= 0:
        raise ValueError("rho_m, u_m, diameter must be positive")
    term = 20000.0 * roughness_m / diameter_m + 1.0e6 * mu_m / (rho_m * u_m * diameter_m)
    f = C.NORSOK_FRICTION_C * (1.0 + term ** (1.0 / 3.0))   # Eq.22 cube root
    return 0.5 * rho_m * f * u_m ** 2


def blasius_friction(reynolds: float) -> float:
    """Fanning friction factor (Blasius), valid ~4e3 < Re < 1e5.
    [SOURCE: Blasius 1913]  T1"""
    if reynolds <= 0:
        raise ValueError("Reynolds must be positive")
    return C.BLASIUS_C * reynolds ** C.BLASIUS_EXP


def schmidt_number(mu: float, rho: float, d_ab: float = C.D_AB_FE) -> float:
    """Sc = nu / D_AB = mu / (rho * D_AB)."""
    return mu / (rho * d_ab)


def sherwood_berger_hau(reynolds: float, schmidt: float) -> float:
    """Straight-pipe Sherwood number (Berger-Hau 1977):
        Sh = 0.0165 * Re^0.86 * Sc^0.33
    [SOURCE: Berger & Hau 1977]  T1"""
    return C.BERGER_HAU_C * reynolds ** C.BERGER_HAU_RE_EXP * schmidt ** C.BERGER_HAU_SC_EXP


def mass_transfer_coefficient(sherwood: float, diameter_m: float,
                              d_ab: float = C.D_AB_FE) -> float:
    """Mass-transfer coefficient k_m = Sh * D_AB / diameter. [m/s]"""
    return sherwood * d_ab / diameter_m


def geometry_enhancement(component: str) -> float:
    """Component MTC enhancement vs straight pipe, matching the severity
    ordering measured by Kim et al. 2021 (KAERI):
        straight < after-elbow < single elbow < elbow-after-orifice
    [SOURCE: derived T2 from Kim et al. 2021 - library copy]  T2
    """
    table = {
        "straight": C.ENH_STRAIGHT,
        "after_elbow": C.ENH_AFTER_ELBOW,
        "elbow": C.ENH_ELBOW,
        "elbow_after_orifice": C.ENH_ELBOW_AFTER_ORIFICE,
    }
    if component not in table:
        raise ValueError(f"unknown component {component!r}")
    return table[component]


def elbow_angular_shear_profile(s_mean: float, n_points: int = 73):
    """Angular distribution of wall shear around a 90 deg elbow (0..90 deg).

    This is a PRESCRIBED analytical shape (two hand-fitted Gaussian bumps), not a
    resolved CFD/flow solution. Its peak LOCATIONS are set to match the pattern
    reported by El-Gammal 2010 / Kim 2021 (extrados peak ~37 deg; an early
    intrados inlet peak), but the amplitudes and widths are tuned parameters. It
    is therefore an input shape fitted to the experiment, not evidence that the
    physics reproduces the experiment.
    Returns (angles_deg, shear_extrados, shear_intrados).
    [SOURCE: peak locations El-Gammal 2010 / Kim 2021; profile shape = tuned fit]  T3
    """
    angles = [90.0 * i / (n_points - 1) for i in range(n_points)]
    extrados = []
    intrados = []
    peak = C.ELBOW_EXTRADOS_PEAK_DEG
    for a in angles:
        # extrados: Gaussian-like bump centred at 37 deg, then sustained to exit
        bump = math.exp(-((a - peak) / 22.0) ** 2)
        sustained = 0.45 * (a / 90.0)
        ext = s_mean * (1.0 + 1.1 * bump + sustained)
        # intrados: strong early peak near the inlet (a small), decaying
        early = math.exp(-((a - 8.0) / 12.0) ** 2)
        intr = s_mean * (1.0 + C.ELBOW_INTRADOS_FACTOR * 1.1 * early + 0.2 * sustained)
        extrados.append(ext)
        intrados.append(intr)
    return angles, extrados, intrados
