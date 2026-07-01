"""
monte_carlo.py - Monte Carlo uncertainty propagation over the coupled
erosion-corrosion model. Generates the >=10,000-row dataset used for surrogate
training and uncertainty quantification.

Sampling ranges track the NORSOK M-506:2017 applicability envelope and the
NORSOK P-002 sand-load design basis. NOTE: p_co2_bar is sampled over [0.1, 10]
which is NORSOK's window on CO2 FUGACITY, not partial pressure; since the
fugacity coefficient a<=1 across the sampled T/P envelope the realised fCO2 sits
at or below pCO2. corrosion_rate() clamps fCO2 into [0.1, 10] so no sample is
silently extrapolated outside the standard.
[SOURCE: NORSOK M-506:2017 Tables 3-6; NORSOK P-002 Clause 8.6.4]  T1
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from . import constants as C
from . import ec_model as ecm

# MC sampling ranges (uniform unless noted) - all within standard envelopes.
# Sample the mixture velocity directly inside the NORSOK envelope, then split
# into liquid/gas superficial velocities respecting u_sl<=20, u_sg<=40 m/s.
MC_RANGES = {
    "u_m": (1.0, 25.0),            # mixture velocity [m/s] within NORSOK envelope
    "liquid_fraction": (0.05, 0.80),  # fraction of u_m carried by liquid
    "diameter_m": (0.0508, 0.254), # 2" to 10"
    "temp_c": (C.NORSOK_T_MIN, C.NORSOK_T_MAX),
    "p_total_bar": (10.0, 150.0),
    "p_co2_bar": (C.NORSOK_FCO2_MIN, C.NORSOK_FCO2_MAX),
    "ph": (C.NORSOK_PH_MIN, C.NORSOK_PH_MAX),
    "watercut": (0.1, 0.95),
    "sand_ppmw": (0.5, 30.0),      # P-002 default 10; sensitivity to 30
    "r_over_d": (1.0, 5.0),
}
# [SOURCE: ranges within NORSOK M-506:2017 (vL<=20, vG<=40 m/s) + P-002]  T1

FEATURES = ["q_l_m3s", "q_g_m3s", "diameter_m", "temp_c", "p_total_bar",
            "p_co2_bar", "ph", "watercut", "sand_ppmw", "r_over_d",
            "u_m", "shear_pa", "sherwood"]
TARGET = "total_mm_yr"


@dataclass
class MCDataset:
    rows: list          # list of dict
    feature_names: list
    target_name: str

    def X(self):
        return [[r[f] for f in self.feature_names] for r in self.rows]

    def y(self):
        return [r[self.target_name] for r in self.rows]


def _sample(rng: random.Random) -> ecm.Operating:
    import math
    d = rng.uniform(*MC_RANGES["diameter_m"])
    area = math.pi * d ** 2 / 4.0
    u_m = rng.uniform(*MC_RANGES["u_m"])
    lf = rng.uniform(*MC_RANGES["liquid_fraction"])
    u_sl = min(u_m * lf, C.NORSOK_VL_MAX)
    u_sg = min(u_m - u_sl, C.NORSOK_VG_MAX)
    q_l = u_sl * area
    q_g = u_sg * area
    return ecm.Operating(
        q_l_m3s=q_l, q_g_m3s=q_g,
        diameter_m=d,
        temp_c=rng.uniform(*MC_RANGES["temp_c"]),
        p_total_bar=rng.uniform(*MC_RANGES["p_total_bar"]),
        p_co2_bar=rng.uniform(*MC_RANGES["p_co2_bar"]),
        ph=rng.uniform(*MC_RANGES["ph"]),
        watercut=rng.uniform(*MC_RANGES["watercut"]),
        sand_ppmw=rng.uniform(*MC_RANGES["sand_ppmw"]),
        r_over_d=rng.uniform(*MC_RANGES["r_over_d"]),
    )


def run(n: int = 10000, seed: int = 11) -> MCDataset:
    """Run n Monte Carlo evaluations; return the assembled dataset."""
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        op = _sample(rng)
        try:
            res = ecm.evaluate(op)
        except (ValueError, ZeroDivisionError):
            continue
        rows.append({
            "q_l_m3s": op.q_l_m3s, "q_g_m3s": op.q_g_m3s,
            "diameter_m": op.diameter_m, "temp_c": op.temp_c,
            "p_total_bar": op.p_total_bar, "p_co2_bar": op.p_co2_bar,
            "ph": op.ph, "watercut": op.watercut, "sand_ppmw": op.sand_ppmw,
            "r_over_d": op.r_over_d,
            "u_m": res.u_m, "shear_pa": res.shear_pa, "sherwood": res.sherwood,
            "erosion_mm_yr": res.erosion_mm_yr,
            "corrosion_protected_mm_yr": res.corrosion_protected_mm_yr,
            "synergy_mm_yr": res.synergy_mm_yr,
            "total_mm_yr": res.total_mm_yr,
            "regime": res.regime,
        })
    return MCDataset(rows=rows, feature_names=FEATURES, target_name=TARGET)


def summary_stats(values):
    """Return dict of mean, std, p5, p50, p95 for a list of values."""
    s = sorted(values)
    n = len(s)
    if n == 0:
        return {"n": 0}
    mean = sum(s) / n
    var = sum((v - mean) ** 2 for v in s) / n
    def pct(p):
        k = max(0, min(n - 1, int(round(p / 100.0 * (n - 1)))))
        return s[k]
    return {"n": n, "mean": mean, "std": var ** 0.5,
            "p5": pct(5), "p50": pct(50), "p95": pct(95),
            "min": s[0], "max": s[-1]}
