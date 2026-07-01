"""
corrosion_norsok.py - NORSOK M-506:2017 (Rev.3) CO2 corrosion rate model.
Library controlled copy.

[SOURCE: NORSOK M-506:2017 Clause 5.2 (Eqs.1-3), Tables 1-2, Clause 8.1]  T1
"""
from __future__ import annotations

import math

from . import constants as C


def fugacity_coefficient(p_bar: float, t_k: float) -> float:
    """CO2 fugacity coefficient a (Eqs.7-8):
        a = 10^(P*(0.0031 - 1.4/T))      for P < 250 bar
        a = 10^(250*(0.0031 - 1.4/T))    for P >= 250 bar
    [SOURCE: NORSOK M-506:2017 Clause 8.1, Eqs.7-8]  T1
    """
    p_eff = min(p_bar, 250.0)
    return 10.0 ** (p_eff * (0.0031 - 1.4 / t_k))


def co2_fugacity(p_co2_bar: float, p_total_bar: float, t_k: float) -> float:
    """fCO2 = a * pCO2.  [SOURCE: NORSOK M-506:2017 Eq.4]  T1"""
    return fugacity_coefficient(p_total_bar, t_k) * p_co2_bar


def f_ph(t_c_node: int, ph: float) -> float:
    """pH factor f(pH)_t at a tabulated temperature node (Table 2, 2017).
    Evaluates the piecewise polynomial/exp segment for the given pH.
    [SOURCE: NORSOK M-506:2017 Table 2]  T1
    """
    if t_c_node not in C.NORSOK_FPH:
        raise ValueError(f"{t_c_node} is not a tabulated NORSOK temperature")
    segments = C.NORSOK_FPH[t_c_node]
    ph_c = min(max(ph, C.NORSOK_PH_MIN), C.NORSOK_PH_MAX)
    for lo, hi, kind, coeffs in segments:
        if lo <= ph_c <= hi:
            if kind == "poly":
                return sum(co * ph_c ** i for i, co in enumerate(coeffs))
            if kind == "exp":
                return coeffs[0] * math.exp(coeffs[1] * ph_c)
    # fall back to nearest segment edge
    lo, hi, kind, coeffs = segments[0] if ph_c < segments[0][0] else segments[-1]
    if kind == "poly":
        return sum(co * ph_c ** i for i, co in enumerate(coeffs))
    return coeffs[0] * math.exp(coeffs[1] * ph_c)


def _cr_at_node(t_node: int, f_co2: float, shear_pa: float, ph: float) -> float:
    """Corrosion rate at a tabulated temperature node (Eqs.1-3). [mm/year]"""
    kt = C.NORSOK_KT[t_node]
    fph = f_ph(t_node, ph)
    if t_node == 5:
        # Eq.3: no shear term, fugacity exponent 0.36
        return kt * f_co2 ** C.NORSOK_FCO2_EXP_LOWT * fph
    if t_node == 15:
        exp_fco2 = C.NORSOK_FCO2_EXP_LOWT
    else:
        exp_fco2 = C.NORSOK_FCO2_EXP_STD
    shear_exp = C.NORSOK_S_EXP_A + C.NORSOK_S_EXP_B * math.log10(max(f_co2, 1e-9))
    shear_term = (max(shear_pa, 1e-9) / C.NORSOK_S_REF) ** shear_exp
    return kt * f_co2 ** exp_fco2 * shear_term * fph


def corrosion_rate(t_c: float, p_co2_bar: float, p_total_bar: float,
                   shear_pa: float, ph: float) -> float:
    """NORSOK M-506:2017 CO2 corrosion rate [mm/year] at arbitrary temperature
    via linear interpolation between the bracketing tabulated nodes (per the
    standard's stated method).
    [SOURCE: NORSOK M-506:2017 Clause 5.2]  T1
    """
    t_k = C.c_to_k(t_c)
    f_co2 = co2_fugacity(p_co2_bar, p_total_bar, t_k)
    # Guard the NORSOK fugacity applicability window [0.1, 10] bar so an
    # out-of-range fCO2 is not silently extrapolated through the power law
    # (mirrors the temperature and pH clamping already applied).
    f_co2 = min(max(f_co2, C.NORSOK_FCO2_MIN), C.NORSOK_FCO2_MAX)
    temps = C.NORSOK_KT_TEMPS

    t_clamped = min(max(t_c, temps[0]), temps[-1])
    # exact node
    for tn in temps:
        if abs(t_clamped - tn) < 1e-9:
            return _cr_at_node(tn, f_co2, shear_pa, ph)
    # bracket
    lower = max(tn for tn in temps if tn < t_clamped)
    upper = min(tn for tn in temps if tn > t_clamped)
    cr_lo = _cr_at_node(lower, f_co2, shear_pa, ph)
    cr_hi = _cr_at_node(upper, f_co2, shear_pa, ph)
    frac = (t_clamped - lower) / (upper - lower)
    return cr_lo + frac * (cr_hi - cr_lo)


def is_applicable(p_co2_bar: float, p_h2s_bar: float = 0.0) -> tuple[bool, str]:
    """Rev.3 applicability check: invalid if pH2S>0.05 bar or pCO2/pH2S<20.
    [SOURCE: NORSOK M-506:2017 Introduction Rev.3 notes]  T1
    """
    if p_h2s_bar > C.NORSOK_PH2S_MAX:
        return False, f"pH2S {p_h2s_bar:.3f} bar > {C.NORSOK_PH2S_MAX} bar limit"
    if p_h2s_bar > 0 and (p_co2_bar / p_h2s_bar) < C.NORSOK_PCO2_PH2S_RATIO_MIN:
        return False, "pCO2/pH2S < 20 (model not applicable)"
    return True, "applicable"
