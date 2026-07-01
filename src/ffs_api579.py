"""
ffs_api579.py - API 579-1/ASME FFS-1 Part 5 local metal loss + remaining life.

[SOURCE: API 579-1/ASME FFS-1 Part 5 (RSFa=0.90); API 510 remaining life]  T1
"""
from __future__ import annotations

import math

from . import constants as C


def folias_factor(lta_length_mm: float, radius_mm: float, t_mm: float) -> float:
    """Folias / bulging factor Mt for a longitudinal local thin area.
        lambda = 1.285 * L / sqrt(R * t) ;  Mt = sqrt(1 + 0.48 * lambda^2)
    Mt >= 1, growing with flaw length -> a longer flaw is weaker.
    [SOURCE: API 579-1/ASME FFS-1 Part 5, Folias factor]  T1
    """
    if radius_mm <= 0 or t_mm <= 0:
        raise ValueError("radius and thickness must be positive")
    lam = 1.285 * max(lta_length_mm, 0.0) / math.sqrt(radius_mm * t_mm)
    return math.sqrt(1.0 + 0.48 * lam ** 2)


def rsf_part5(t_actual: float, t_nominal: float,
              lta_length_mm: float, radius_mm: float) -> float:
    """API 579-1 Part 5 Level-1 Remaining Strength Factor for a local thin area,
    including the Folias bulging factor Mt (which the simplified linear RSF omits):

        Rt_loss = (t_nominal - t_actual) / t_nominal          (fractional wall loss)
        Mt      = folias_factor(L, R, t_nominal)
        RSF     = (1 - Rt_loss) / (1 - Rt_loss / Mt)

    A longer flaw (larger Mt) gives a lower RSF at the same depth.
    [SOURCE: API 579-1/ASME FFS-1 Part 5 Level 1 RSF]  T1
    """
    if t_nominal <= 0:
        return 0.0
    rt_loss = min(max((t_nominal - t_actual) / t_nominal, 0.0), 1.0)
    mt = folias_factor(lta_length_mm, radius_mm, t_nominal)
    denom = 1.0 - rt_loss / mt
    if denom <= 0:
        return 0.0
    return max(0.0, min(1.0, (1.0 - rt_loss) / denom))


def t_min_pressure(p_mpa: float, radius_mm: float, allow_stress_mpa: float,
                   weld_eff: float = 1.0) -> float:
    """Minimum required thickness (circumferential stress, thin-wall):
        t_min = P*R / (S*E - 0.6*P)
    [SOURCE: ASME B31.3 / API 510 pressure design]  T1
    """
    denom = allow_stress_mpa * weld_eff - 0.6 * p_mpa
    if denom <= 0:
        raise ValueError("invalid pressure/stress combination")
    return p_mpa * radius_mm / denom


def remaining_strength_factor(t_actual: float, t_min: float,
                              t_nominal: float) -> float:
    """SCREENING RSF proxy (linear thickness ratio, NO Folias factor):
        RSF = (t_actual - t_min) / (t_nominal - t_min), clamped [0,1]
    This is a depth-only screening estimate; use rsf_part5() for the true
    API 579-1 Part 5 Level-1 RSF that includes the Folias bulging factor Mt.
    [SOURCE: API 579-1 Part 5 RSF concept, simplified/screening]  T2
    """
    denom = t_nominal - t_min
    if denom <= 0:
        return 0.0
    return max(0.0, min(1.0, (t_actual - t_min) / denom))


def acceptable(rsf: float) -> bool:
    """Accept if RSF >= RSFa (0.90). [SOURCE: API 579-1 Part 5]  T1"""
    return rsf >= C.API579_RSF_ALLOWABLE


def reduced_mawp(mawp: float, rsf: float) -> float:
    """If RSF < RSFa, reduce MAWP by RSF/RSFa. [SOURCE: API 579-1 Part 5]  T1"""
    if rsf >= C.API579_RSF_ALLOWABLE:
        return mawp
    return mawp * rsf / C.API579_RSF_ALLOWABLE


def remaining_life(t_actual: float, t_min: float, rate_mm_yr: float) -> float:
    """Remaining life = (t_actual - t_min) / corrosion_rate [years].
    [SOURCE: API 510 remaining life]  T1
    """
    if rate_mm_yr <= 0:
        return float("inf")
    return max(0.0, (t_actual - t_min) / rate_mm_yr)
