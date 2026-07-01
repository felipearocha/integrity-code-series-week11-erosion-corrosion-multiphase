"""
constants.py - Physical constants, material data, and standard-derived coefficients.

Integrity Code Series - Week 11
Erosion-Corrosion (synergistic) in multiphase oil & gas production piping at bends.

EVERY constant carries an explicit [SOURCE: ...] tag per the ICS2 no-hallucination policy.
Anti-hallucination tiers:
    T1 = directly from a controlled standard/paper copy
    T2 = calculated/derived from standard data
    T3 = practitioner heuristic (labelled)
"""
from __future__ import annotations

# ----------------------------------------------------------------------------
# Universal constants
# ----------------------------------------------------------------------------
G = 9.80665            # gravitational acceleration [m/s^2]
R_GAS = 8.314462618    # universal gas constant [J/(mol K)]
T_ABS = 273.15         # 0 C in K

# ----------------------------------------------------------------------------
# Carbon steel material data (target component)
# ----------------------------------------------------------------------------
RHO_STEEL = 7800.0     # steel density [kg/m^3]
# [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Table 7-2, rho_t for steel grades]  T1

WALL_THICKNESS_MM = 12.7   # nominal wall of the target elbow [mm] (Sch-80 ~6" NPS)
# Metal loss is physically bounded by this: a wall-loss field can never exceed it
# (the pipe perforates first). [SOURCE: ASME B36.10M nominal wall - practitioner]  T3

# ----------------------------------------------------------------------------
# 1) DNV-RP-O501 Rev.4.2 (2007) ductile erosion model -- PRIMARY EROSION ENGINE
#    Designated by NORSOK P-002 Clause 8.6.4 (library copy) as the empirical
#    particle-erosion model for standard pipework components.
# ----------------------------------------------------------------------------
DNV_K_STEEL = 2.0e-9   # material constant K [(m/s)^-n]
DNV_N_STEEL = 2.6      # velocity exponent n [-]
# [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Table 7-2]  T1

# Angle function F(alpha) polynomial coefficients A1..A8 (Rev.4.2 Table 7-1)
# F(alpha) = sum_{i=1..8} (-1)^(i+1) * A_i * (alpha_rad)^i
DNV_FALPHA_COEFFS = (9.370, 42.295, 110.864, 175.804, 170.137, 98.398, 31.211, 4.170)
# [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Table 7-1, Eqs.7.2/7.3]  T1

DNV_C1_BEND = 2.5      # bend model/geometry factor (Rev.4.2; was 5 in Rev.4.1)
# [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Sec.8.4, Eq.8.21]  T1

DNV_C_UNIT = 3.15e10   # unit conversion m/s -> mm/year used in bend model
# [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Eq.8.21]  T1

DNV_STRAIGHT_COEFF = 2.5e-5  # straight smooth steel pipe closed form Eq.8.9
# E_dot_L = 2.5e-5 * m_dot_p * U_p^2.6 * D^-2  [mm/year], SI inputs
# [SOURCE: DNV-RP-O501 Rev.4.2 (2007) Eq.8.9]  T1

# ----------------------------------------------------------------------------
# 2) NORSOK M-506:2017 (Rev.3) CO2 corrosion model -- PRIMARY CORROSION ENGINE
# ----------------------------------------------------------------------------
NORSOK_KT = {
    5: 0.42, 15: 1.59, 20: 4.762, 40: 8.927, 60: 10.695,
    80: 9.949, 90: 6.250, 120: 7.770, 150: 5.203,
}
# [SOURCE: NORSOK M-506:2017 Table 1 - library controlled copy]  T1
NORSOK_KT_TEMPS = tuple(sorted(NORSOK_KT.keys()))

NORSOK_FCO2_EXP_STD = 0.62
NORSOK_FCO2_EXP_LOWT = 0.36
NORSOK_S_REF = 19.0
NORSOK_S_EXP_A = 0.146
NORSOK_S_EXP_B = 0.0324
# [SOURCE: NORSOK M-506:2017 Clause 5.2, Eqs.1-3]  T1

NORSOK_FPH = {
    5:   [(3.5, 4.6, "poly", (2.0676, -0.2309)),
          (4.6, 6.5, "poly", (4.342, -1.051, 0.0708))],
    15:  [(3.5, 4.6, "poly", (2.0676, -0.2309)),
          (4.6, 6.5, "poly", (4.986, -1.191, 0.0708))],
    20:  [(3.5, 4.6, "poly", (2.0676, -0.2309)),
          (4.6, 6.5, "poly", (5.1885, -1.2353, 0.0708))],
    40:  [(3.5, 4.6, "poly", (2.0676, -0.2309)),
          (4.6, 6.5, "poly", (5.1885, -1.2353, 0.0708))],
    60:  [(3.5, 4.6, "poly", (1.836, -0.1818)),
          (4.6, 6.5, "poly", (15.444, -6.1291, 0.8204, -0.0371))],
    80:  [(3.5, 4.6, "poly", (2.6727, -0.3636)),
          (4.6, 6.5, "exp", (331.68, -1.2618))],
    90:  [(3.5, 4.57, "poly", (3.1355, -0.4673)),
          (4.57, 5.62, "exp", (21254.0, -2.1811)),
          (5.62, 6.5, "poly", (0.4014, -0.0538))],
    120: [(3.5, 4.3, "poly", (1.5375, -0.125)),
          (4.3, 5.0, "poly", (5.9757, -1.157)),
          (5.0, 6.5, "poly", (0.546125, -0.071225))],
    150: [(3.5, 3.8, "poly", (1.0,)),
          (3.8, 5.0, "poly", (17.634, -7.0945, 0.715)),
          (5.0, 6.5, "poly", (0.037,))],
}
# [SOURCE: NORSOK M-506:2017 Table 2 - library controlled copy]  T1

NORSOK_T_MIN, NORSOK_T_MAX = 5.0, 150.0
NORSOK_PH_MIN, NORSOK_PH_MAX = 3.5, 6.5
NORSOK_FCO2_MIN, NORSOK_FCO2_MAX = 0.1, 10.0
NORSOK_P_MIN, NORSOK_P_MAX = 1.0, 1000.0
NORSOK_VL_MAX = 20.0
NORSOK_VG_MAX = 40.0
NORSOK_RE_TURB = 2300.0
NORSOK_PH2S_MAX = 0.05
NORSOK_PCO2_PH2S_RATIO_MIN = 20.0
# [SOURCE: NORSOK M-506:2017 Tables 3-6 + Rev.3 notes]  T1

NORSOK_FRICTION_C = 0.001375
# [SOURCE: NORSOK M-506:2017 Clause 8.4, Eq.22]  T1

# ----------------------------------------------------------------------------
# 3) NORSOK P-002 erosion design basis (library controlled copy)
# ----------------------------------------------------------------------------
P002_SAND_LIQUID_PPMW = 10.0
P002_SAND_GAS_PPMW = 0.5
P002_PARTICLE_SIZE_UM = 250.0
P002_LOSS_SAND_KG = 1000.0
P002_LOSS_SAND_HOURS = 4.0
P002_VEL_LIMIT_CS = 10.0
P002_VEL_LIMIT_CRA = 25.0
# [SOURCE: NORSOK P-002 Clauses 8.5.2, 8.6.4 - library controlled copy]  T1

# ----------------------------------------------------------------------------
# 4) Elbow hydrodynamics / mass transfer
# ----------------------------------------------------------------------------
BERGER_HAU_C = 0.0165
BERGER_HAU_RE_EXP = 0.86
BERGER_HAU_SC_EXP = 0.33
# [SOURCE: Berger & Hau (1977) Int J Heat Mass Transfer 20:1185-1194]  T1

BLASIUS_C = 0.0791
BLASIUS_EXP = -0.25
# [SOURCE: Blasius (1913); Bird-Stewart-Lightfoot Transport Phenomena]  T1

ELBOW_EXTRADOS_PEAK_DEG = 37.0   # extrados shear-peak location [deg] (from the papers)
ELBOW_INTRADOS_FACTOR = 1.37     # tuned intrados/extrados peak amplitude ratio
# The ~37 deg extrados peak location is reported by the papers; the amplitude
# ratio and the Gaussian shape parameters are hand-fitted, NOT read directly
# from a controlled copy. [SOURCE: peak location El-Gammal et al. 2010 / Kim
# et al. 2021; amplitude ratio + profile shape = tuned fit]  T2/T3

ENH_STRAIGHT = 1.00
ENH_AFTER_ELBOW = 1.4
ENH_ELBOW = 2.0
ENH_ELBOW_AFTER_ORIFICE = 3.0
# [SOURCE: derived T2 to match severity ordering in Kim et al. 2021 - library]  T2

# ----------------------------------------------------------------------------
# 5) ASTM G119 synergy framework
# ----------------------------------------------------------------------------
G119_EXAMPLE = {"T": 387.0, "W0": 249.0, "C0": 2.10, "Cw": 3.75}
# [SOURCE: ASTM G119-04 Clause 7.3 worked example]  T1

# ----------------------------------------------------------------------------
# 6) API 579-1 Part 5 fitness-for-service
# ----------------------------------------------------------------------------
API579_RSF_ALLOWABLE = 0.90
# [SOURCE: API 579-1/ASME FFS-1 Part 5, RSFa default]  T1

# ----------------------------------------------------------------------------
# Fluid property defaults (NORSOK M-506:2017 Table 5 defaults)
# ----------------------------------------------------------------------------
RHO_WATER = 1024.0
RHO_OIL = 850.0
MU_WATER = 0.0005
MU_OIL = 0.0011
MU_GAS = 3.0e-5
D_AB_FE = 7.0e-10
PIPE_ROUGHNESS = 50e-6
# [SOURCE: NORSOK M-506:2017 Table 5 default values]  T1

PALETTE = {
    "navy": "#1b3a5c",
    "steel": "#4c80b0",
    "dark_red": "#8c2318",
    "teal": "#2e7d7b",
    "charcoal": "#333333",
}


def c_to_k(t_c):
    """Celsius to Kelvin."""
    return t_c + T_ABS
