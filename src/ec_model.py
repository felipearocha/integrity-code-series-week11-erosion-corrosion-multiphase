"""
ec_model.py - Coupled erosion-corrosion model coordinator.

Chains the full physics for one operating point:
  multiphase flow -> mixture props -> wall shear S + MTC ->
  [erosion: DNV-RP-O501 bend] + [corrosion: NORSOK M-506:2017 with S] ->
  scale-removal-driven ASTM G119 synergy -> total wall-loss rate ->
  API 579 remaining life.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import constants as C
from . import multiphase_flow as mpf
from . import hydrodynamics as hyd
from . import erosion_dnv as ero
from . import corrosion_norsok as cor
from . import synergy_g119 as syn
from . import ffs_api579 as ffs


@dataclass
class Operating:
    """Operating point inputs."""
    q_l_m3s: float
    q_g_m3s: float
    diameter_m: float
    temp_c: float
    p_total_bar: float
    p_co2_bar: float
    ph: float
    watercut: float = 0.5
    sand_ppmw: float = C.P002_SAND_LIQUID_PPMW
    r_over_d: float = 1.5
    rho_g: float = 50.0
    component: str = "elbow"
    t_nominal_mm: float = 12.7
    p_h2s_bar: float = 0.0


@dataclass
class ECResult:
    regime: str
    u_m: float
    shear_pa: float
    sherwood: float
    mtc: float
    erosion_mm_yr: float
    corrosion_protected_mm_yr: float
    corrosion_bare_mm_yr: float
    synergy_mm_yr: float
    total_mm_yr: float
    scale_removal: float
    corrosion_augmentation: float
    applicable: bool
    note: str


def evaluate(op: Operating) -> ECResult:
    """Evaluate the coupled erosion-corrosion model for one operating point."""
    applicable, note = cor.is_applicable(op.p_co2_bar, op.p_h2s_bar)

    fs = mpf.resolve_flow(op.q_l_m3s, op.q_g_m3s, op.diameter_m,
                          watercut=op.watercut, rho_g=op.rho_g)

    shear = hyd.norsok_wall_shear(fs.rho_m, fs.u_m, op.diameter_m, fs.mu_m)
    sc = hyd.schmidt_number(fs.mu_m, fs.rho_m)
    sh = hyd.sherwood_berger_hau(fs.reynolds, sc)
    enh = hyd.geometry_enhancement(
        "elbow" if op.component in ("elbow", "bend") else "straight")
    sh *= enh
    mtc = hyd.mass_transfer_coefficient(sh, op.diameter_m)

    # erosion (DNV). ASSUMPTION: particle impact velocity U_p = mixture velocity
    # u_m (no slip model; valid mainly for liquid-dominated flow — particles lag
    # in gas-dominated regimes). Sand loading is on the liquid stream (ppmw).
    m_dot_p = ero.sand_mass_flow(op.sand_ppmw, op.q_l_m3s,
                                 rho_l=mpf.liquid_density(C.RHO_WATER, C.RHO_OIL,
                                                          op.watercut))
    e0 = ero.erosion_rate(m_dot_p, fs.u_m, op.diameter_m,
                          component=op.component, r_over_d=op.r_over_d)

    # corrosion (NORSOK) with intact scale = uses actual shear; bare = high shear
    c0_protected = cor.corrosion_rate(op.temp_c, op.p_co2_bar, op.p_total_bar,
                                      shear, op.ph)
    # bare-steel (scale-free) rate PROXY: NORSOK evaluated at an elevated shear so
    # its shear term stands in for lost FeCO3 scale. This is a T3 modelling proxy,
    # not a NORSOK bare-steel model.
    c0_bare = cor.corrosion_rate(op.temp_c, op.p_co2_bar, op.p_total_bar,
                                 max(shear * 3.0, 50.0), op.ph)

    sr = syn.decompose(e0, c0_protected, c0_bare, shear)

    return ECResult(
        regime=fs.regime, u_m=fs.u_m, shear_pa=shear, sherwood=sh, mtc=mtc,
        erosion_mm_yr=e0, corrosion_protected_mm_yr=c0_protected,
        corrosion_bare_mm_yr=c0_bare, synergy_mm_yr=sr.synergy,
        total_mm_yr=sr.total, scale_removal=sr.scale_removal,
        corrosion_augmentation=sr.corrosion_augmentation,
        applicable=applicable, note=note,
    )


def remaining_life_years(op: Operating, result: ECResult,
                         allow_stress_mpa: float = 138.0) -> float:
    """Remaining life from the total wall-loss rate (API 579 / API 510)."""
    p_mpa = op.p_total_bar * 0.1
    radius_mm = op.diameter_m * 1000.0 / 2.0
    t_min = ffs.t_min_pressure(p_mpa, radius_mm, allow_stress_mpa)
    return ffs.remaining_life(op.t_nominal_mm, t_min, result.total_mm_yr)
