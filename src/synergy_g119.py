"""
synergy_g119.py - ASTM G119 erosion-corrosion synergy decomposition.

    T  = W0 + C0 + S            (Eq.1)
    S  = dCw + dWc             (Eq.2)   synergy = erosion-enhanced-corrosion
                                         + corrosion-enhanced-erosion
[SOURCE: ASTM G119-04 Clauses 7.1-7.3, Eqs.1-4]  T1

Mechanism: high wall shear + sand impingement strip the protective FeCO3 scale,
re-exposing bare steel; the bare-steel corrosion rate then applies until the
scale re-forms. This package models the synergy through a scale-removal factor
driven by wall shear and particle loading.
"""
from __future__ import annotations

import math
from dataclasses import dataclass



@dataclass
class SynergyResult:
    e0: float       # pure erosion [mm/yr]
    c0: float       # pure (scaled/protected) corrosion [mm/yr]
    d_cw: float     # erosion-enhanced corrosion [mm/yr]
    d_wc: float     # corrosion-enhanced erosion [mm/yr]
    synergy: float  # S = d_cw + d_wc
    total: float    # T = e0 + c0 + S
    scale_removal: float          # fraction of FeCO3 scale removed [0..1]
    corrosion_augmentation: float # (c0 + d_cw)/c0
    total_synergism: float        # T/(T-S)


def scale_removal_fraction(shear_pa: float, e0_mm_yr: float,
                           shear_threshold_pa: float = 15.0) -> float:
    """Fraction of protective FeCO3 scale removed by flow + particles [0..1].

    Combines a shear-driven term (scale stripping above ~10-20 Pa, slug flow)
    with a particle-erosion term. Saturates at 1.
    [SOURCE: mechanism per NORSOK M-506 Clause 8.4 (mesa attack);
             ASTM G119 synergy framework]  T2
    """
    # NOTE: the 15 Pa scale-removal threshold and the 0.5 mm/yr erosion scale are
    # HEURISTIC parameters. NORSOK M-506 has no quantitative descaling law (mesa
    # attack is a morphology, not a stripping formula); ASTM G119 supplies the
    # additive T=W0+C0+S framework but no predictive split. Treat as T3.
    shear_term = 1.0 - math.exp(-max(shear_pa, 0.0) / shear_threshold_pa)
    erosion_term = 1.0 - math.exp(-max(e0_mm_yr, 0.0) / 0.5)
    removal = 1.0 - (1.0 - shear_term) * (1.0 - erosion_term)
    return min(max(removal, 0.0), 1.0)


def decompose(e0: float, c0_protected: float, c0_bare: float,
              shear_pa: float) -> SynergyResult:
    """Decompose total erosion-corrosion wastage per ASTM G119.

    Args:
        e0: pure mechanical erosion rate (DNV) [mm/yr]
        c0_protected: corrosion rate WITH intact FeCO3 scale [mm/yr]
        c0_bare: corrosion rate on BARE steel (no scale) [mm/yr]
        shear_pa: wall shear stress [Pa]
    [SOURCE: ASTM G119-04 Eqs.1-4]  T1
    """
    if c0_bare < c0_protected:
        c0_bare = c0_protected
    removal = scale_removal_fraction(shear_pa, e0)
    # erosion-enhanced corrosion: extra corrosion from exposing bare steel
    d_cw = removal * (c0_bare - c0_protected)
    # corrosion-enhanced erosion: fresh-exposed (corroded) surface erodes faster.
    # The 0.25 coefficient is a HEURISTIC (T3) assumption, not an ASTM G119 value;
    # G119 gives the additive framework but no predictive coefficient for d_wc.
    d_wc = e0 * 0.25 * removal
    synergy = d_cw + d_wc
    total = e0 + c0_protected + synergy
    cw = c0_protected + d_cw
    corr_aug = cw / c0_protected if c0_protected > 0 else float("inf")
    total_syn = total / (total - synergy) if (total - synergy) > 0 else float("inf")
    return SynergyResult(
        e0=e0, c0=c0_protected, d_cw=d_cw, d_wc=d_wc, synergy=synergy,
        total=total, scale_removal=removal,
        corrosion_augmentation=corr_aug, total_synergism=total_syn,
    )
