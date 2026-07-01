"""
multiphase_flow.py - Gas-liquid multiphase flow: mixture properties, superficial
velocities, and Beggs-Brill (1973) flow-pattern classification + holdup.

[SOURCE: Beggs & Brill (1973) "A Study of Two-Phase Flow in Inclined Pipes",
         JPT pp.607-617, SPE-4007-PA]  T1
[SOURCE: NORSOK M-506:2017 Clause 8.4 mixture property definitions]  T1
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import constants as C


@dataclass
class FlowState:
    """Resolved multiphase flow state for a pipe section."""
    u_sl: float          # superficial liquid velocity [m/s]
    u_sg: float          # superficial gas velocity [m/s]
    u_m: float           # mixture velocity [m/s]
    lambda_l: float      # no-slip liquid holdup [-]
    rho_m: float         # mixture density [kg/m^3]
    mu_m: float          # mixture viscosity [Pa.s]
    holdup_l: float      # Beggs-Brill horizontal liquid holdup E_L(0) [-]
    regime: str          # "segregated" | "intermittent" | "distributed" | "transition"
    froude: float        # mixture Froude number [-]
    reynolds: float      # mixture Reynolds number [-]


def superficial_velocity(q_m3s: float, diameter_m: float) -> float:
    """Superficial velocity = volumetric flow / pipe cross-section. [m/s]"""
    if diameter_m <= 0:
        raise ValueError("diameter must be positive")
    area = math.pi * diameter_m ** 2 / 4.0
    return q_m3s / area


def mixture_density(rho_l: float, rho_g: float, lambda_l: float) -> float:
    """No-slip mixture density: rho_m = rho_l*lambda_l + rho_g*(1-lambda_l).
    [SOURCE: NORSOK M-506:2017 Clause 8.4]  T1"""
    return rho_l * lambda_l + rho_g * (1.0 - lambda_l)


def mixture_viscosity(mu_l: float, mu_g: float, lambda_l: float) -> float:
    """No-slip mixture viscosity. [SOURCE: NORSOK M-506:2017 Clause 8.4]  T1"""
    return mu_l * lambda_l + mu_g * (1.0 - lambda_l)


def liquid_density(rho_w: float, rho_o: float, watercut: float) -> float:
    """Liquid (oil+water) density from watercut fraction [0..1]."""
    return watercut * rho_w + (1.0 - watercut) * rho_o


def froude_number(u_m: float, diameter_m: float) -> float:
    """Mixture Froude number Fr = u_m^2 / (g*D). [SOURCE: Beggs-Brill 1973]  T1"""
    return u_m ** 2 / (C.G * diameter_m)


def reynolds_number(rho: float, u: float, diameter_m: float, mu: float) -> float:
    """Reynolds number Re = rho*u*D/mu."""
    if mu <= 0:
        raise ValueError("viscosity must be positive")
    return rho * u * diameter_m / mu


def beggs_brill_regime(lambda_l: float, froude: float) -> str:
    """Beggs-Brill (1973) horizontal flow-pattern classification.
    Boundaries:
        L1 = 316 * C_L^0.302
        L2 = 0.0009252 * C_L^-2.4684
        L3 = 0.10 * C_L^-1.4516
        L4 = 0.5 * C_L^-6.738
    [SOURCE: Beggs & Brill 1973 SPE-4007-PA]  T1
    """
    cl = min(max(lambda_l, 1e-9), 1.0)
    l1 = 316.0 * cl ** 0.302
    l2 = 0.0009252 * cl ** (-2.4684)
    l3 = 0.10 * cl ** (-1.4516)
    l4 = 0.5 * cl ** (-6.738)

    if (cl < 0.01 and froude < l1) or (cl >= 0.01 and froude < l2):
        return "segregated"
    if cl >= 0.01 and l2 <= froude < l3:
        return "transition"
    if (0.01 <= cl < 0.4 and l3 <= froude <= l1) or (cl >= 0.4 and l3 < froude <= l4):
        return "intermittent"
    return "distributed"


def beggs_brill_holdup(lambda_l: float, froude: float, regime: str) -> float:
    """Beggs-Brill horizontal liquid holdup E_L(0) = a*C_L^b / Fr^c,
    constrained E_L(0) >= C_L.
    [SOURCE: Beggs & Brill 1973 SPE-4007-PA]  T1
    """
    coeffs = {
        "segregated": (0.98, 0.4846, 0.0868),
        "intermittent": (0.845, 0.5351, 0.0173),
        "distributed": (1.065, 0.5824, 0.0609),
    }
    if regime == "transition":
        # Beggs-Brill A-weighted blend: E_L = A*E_seg + (1-A)*E_int,
        # A = (L3 - Fr)/(L3 - L2). (The previous flat 0.5 average ignored Fr.)
        cl = min(max(lambda_l, 1e-9), 1.0)
        l2 = 0.0009252 * cl ** (-2.4684)
        l3 = 0.10 * cl ** (-1.4516)
        a_w = 0.5 if l3 == l2 else (l3 - froude) / (l3 - l2)
        a_w = min(max(a_w, 0.0), 1.0)
        seg = beggs_brill_holdup(lambda_l, froude, "segregated")
        inter = beggs_brill_holdup(lambda_l, froude, "intermittent")
        return a_w * seg + (1.0 - a_w) * inter
    a, b, cc = coeffs[regime]
    cl = min(max(lambda_l, 1e-9), 1.0)
    fr = max(froude, 1e-9)
    el0 = a * cl ** b / fr ** cc
    return min(max(el0, cl), 1.0)


def resolve_flow(q_l_m3s: float, q_g_m3s: float, diameter_m: float,
                 watercut: float = 0.5,
                 rho_w: float = C.RHO_WATER, rho_o: float = C.RHO_OIL,
                 rho_g: float = 50.0,
                 mu_w: float = C.MU_WATER, mu_o: float = C.MU_OIL,
                 mu_g: float = C.MU_GAS) -> FlowState:
    """Resolve a full multiphase flow state from volumetric flows + geometry."""
    u_sl = superficial_velocity(q_l_m3s, diameter_m)
    u_sg = superficial_velocity(q_g_m3s, diameter_m)
    u_m = u_sl + u_sg
    if (q_l_m3s + q_g_m3s) <= 0:
        raise ValueError("total flow must be positive")
    lambda_l = q_l_m3s / (q_l_m3s + q_g_m3s)

    rho_l = liquid_density(rho_w, rho_o, watercut)
    mu_l = mu_w * watercut + mu_o * (1.0 - watercut)
    rho_m = mixture_density(rho_l, rho_g, lambda_l)
    mu_m = mixture_viscosity(mu_l, mu_g, lambda_l)

    fr = froude_number(u_m, diameter_m)
    re = reynolds_number(rho_m, u_m, diameter_m, mu_m)
    regime = beggs_brill_regime(lambda_l, fr)
    holdup = beggs_brill_holdup(lambda_l, fr, regime)

    return FlowState(u_sl=u_sl, u_sg=u_sg, u_m=u_m, lambda_l=lambda_l,
                     rho_m=rho_m, mu_m=mu_m, holdup_l=holdup, regime=regime,
                     froude=fr, reynolds=re)
