"""
benchmarks.py - QC Gate 1 physics verification (analytical hand-calculations).

Each benchmark independently hand-computes an expected value from the governing
equation and source constants, then compares against the code output.
Tolerances per ICS2 Triple QC Protocol: 1% for rates, 5% for integrated.

Run:  python validation/benchmarks.py
"""
from __future__ import annotations

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from src import constants as C            # noqa: E402
from src import corrosion_norsok as cor   # noqa: E402
from src import erosion_dnv as ero        # noqa: E402
from src import hydrodynamics as hyd      # noqa: E402
from src import synergy_g119 as syn       # noqa: E402

RESULTS = []


def check(name, expected, actual, tol_rel):
    ok = abs(actual - expected) <= tol_rel * abs(expected) + 1e-12
    RESULTS.append((name, expected, actual, tol_rel, ok))
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name}: expected={expected:.6g} actual={actual:.6g} "
          f"(tol {tol_rel*100:.0f}%)")
    return ok


def bench_norsok_node_20c():
    """Hand-calc NORSOK CR at 20 C node.
    CR = Kt * fCO2^0.62 * (S/19)^(0.146+0.0324 log10 fCO2) * f(pH)
    At 20 C, pCO2=1 bar, P=20 bar, shear=19 Pa, pH=4.0
    fugacity a = 10^(20*(0.0031 - 1.4/293.15))
    """
    t_c, pco2, p, shear, ph = 20, 1.0, 20.0, 19.0, 4.0
    t_k = 293.15
    a = 10 ** (p * (0.0031 - 1.4 / t_k))
    fco2 = a * pco2
    kt = 4.762
    # f(pH=4.0): 3.5<pH<4.6 -> 2.0676 - 0.2309*4.0
    fph = 2.0676 - 0.2309 * 4.0
    shear_exp = 0.146 + 0.0324 * math.log10(fco2)
    expected = kt * fco2 ** 0.62 * (shear / 19.0) ** shear_exp * fph
    actual = cor.corrosion_rate(t_c, pco2, p, shear, ph)
    return check("NORSOK CR @20C node", expected, actual, 0.01)


def bench_norsok_5c_no_shear():
    """At 5 C, Eq.3 has NO shear term, fugacity exponent 0.36."""
    t_c, pco2, p, shear, ph = 5, 1.0, 30.0, 100.0, 4.0
    t_k = 278.15
    a = 10 ** (p * (0.0031 - 1.4 / t_k))
    fco2 = a * pco2
    kt = 0.42
    fph = 2.0676 - 0.2309 * 4.0
    expected = kt * fco2 ** 0.36 * fph  # no shear term
    actual = cor.corrosion_rate(t_c, pco2, p, shear, ph)
    return check("NORSOK CR @5C (no shear term)", expected, actual, 0.01)


def bench_norsok_interpolation():
    """CR at 30 C = linear interp of CR(20) and CR(40)."""
    args = (1.0, 50.0, 20.0, 5.0)
    cr20 = cor.corrosion_rate(20, *args)
    cr40 = cor.corrosion_rate(40, *args)
    expected = 0.5 * (cr20 + cr40)
    actual = cor.corrosion_rate(30, *args)
    return check("NORSOK CR linear interp @30C", expected, actual, 0.01)


def bench_dnv_straight():
    """DNV Eq.8.9 straight pipe: E = 2.5e-5 * m_dot * U^2.6 * D^-2."""
    m_dot, u, d = 1e-4, 10.0, 0.1
    expected = 2.5e-5 * m_dot * u ** 2.6 * d ** -2
    actual = ero.erosion_straight(m_dot, u, d)
    return check("DNV straight-pipe erosion Eq.8.9", expected, actual, 0.01)


def bench_dnv_angle():
    """DNV characteristic bend angle: alpha = atan(1/(2*sqrt(R/D)))."""
    r_over_d = 1.5
    expected = math.degrees(math.atan(1.0 / (2.0 * math.sqrt(r_over_d))))
    actual = ero.characteristic_bend_angle(r_over_d)
    return check("DNV bend characteristic angle", expected, actual, 0.001)


def bench_falpha_peak():
    """DNV Rev.4.2 F(alpha) is a normalised ductile angle function: it rises
    steeply, plateaus near 1.0 across the ductile range (25-45 deg), and decays
    to ~0.57 at 90 deg. Verify (a) plateau in 25-45 deg, (b) ductile range
    far exceeds normal impact (90 deg). [SOURCE: DNV-RP-O501 Table 7-1]  T1
    """
    vals = [(a, ero.f_alpha(a)) for a in range(1, 91)]
    peak_angle = max(vals, key=lambda t: t[1])[0]
    f90 = ero.f_alpha(90)
    f30 = ero.f_alpha(30)
    ok = (25 <= peak_angle <= 45) and (f30 > 1.4 * f90)
    RESULTS.append(("DNV F(alpha) ductile plateau 25-45deg", peak_angle, peak_angle, 0, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] DNV F(alpha) plateau at {peak_angle} deg "
          f"(25-45); F30={f30:.2f} > 1.4*F90={1.4*f90:.2f}")
    return ok


def bench_blasius():
    """Blasius Fanning f = 0.0791 Re^-0.25 at Re=1e4."""
    re = 1e4
    expected = 0.0791 * re ** -0.25
    actual = hyd.blasius_friction(re)
    return check("Blasius friction @Re=1e4", expected, actual, 0.001)


def bench_berger_hau():
    """Berger-Hau Sh = 0.0165 Re^0.86 Sc^0.33 at Re=4e4, Sc=2244."""
    re, sc = 4e4, 2244.0
    expected = 0.0165 * re ** 0.86 * sc ** 0.33
    actual = hyd.sherwood_berger_hau(re, sc)
    return check("Berger-Hau Sherwood", expected, actual, 0.001)


def bench_g119_example():
    """ASTM G119 worked example: T=387,W0=249,C0=2.10,Cw=3.75 -> S=135.9.
    Verify the synergy arithmetic S = T - W0 - C0 and augmentation = Cw/C0.
    """
    ex = C.G119_EXAMPLE
    s = ex["T"] - ex["W0"] - ex["C0"]
    aug = ex["Cw"] / ex["C0"]
    check("G119 synergy S (=135.9)", 135.9, s, 0.01)
    return check("G119 corrosion augmentation (=1.79)", 1.79, aug, 0.01)


def bench_monotonic_temperature():
    """NORSOK CR must peak near 60 C (Kt peak) and fall by 150 C."""
    args = (1.0, 50.0, 20.0, 5.0)
    cr60 = cor.corrosion_rate(60, *args)
    cr150 = cor.corrosion_rate(150, *args)
    cr5 = cor.corrosion_rate(5, *args)
    ok = cr60 > cr5 and cr60 > cr150
    RESULTS.append(("NORSOK CR peaks ~60C", cr60, cr60, 0, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] NORSOK CR peak: CR5={cr5:.2f} "
          f"CR60={cr60:.2f} CR150={cr150:.2f}")
    return ok


def bench_dnv_bend_magnitude():
    """Hand-calc DNV bend erosion magnitude (Eq.8.21) - the headline erosion path.
    E = K*m*U^n*F(alpha)/(rho_t*A_t)*C1*C_unit, A_t = pi*D^2/(4 sin a).
    NO extra sin in the numerator. m=1e-4 kg/s, U=15 m/s, D=0.1 m, R/D=1.5.
    """
    m_dot, u_p, d, rod = 1.0e-4, 15.0, 0.1, 1.5
    alpha = math.radians(ero.characteristic_bend_angle(rod))
    a_t = math.pi * d ** 2 / (4.0 * math.sin(alpha))
    fa = ero.f_alpha(math.degrees(alpha))
    expected = (C.DNV_K_STEEL * m_dot * u_p ** C.DNV_N_STEEL * fa) / (C.RHO_STEEL * a_t) \
        * C.DNV_C1_BEND * C.DNV_C_UNIT
    actual = ero.erosion_bend(m_dot, u_p, d, rod)
    return check("DNV bend erosion magnitude Eq.8.21", expected, actual, 0.01)


def bench_g119_decompose():
    """Exercise the actual G119 synergy MODEL (syn.decompose), not just dict
    arithmetic: the additive identity T=W0+C0+S must hold and, with the scale
    stripped (high shear), the synergy must be positive and augmentation > 1.
    """
    r = syn.decompose(e0=0.5, c0_protected=2.0, c0_bare=6.0, shear_pa=60.0)
    check("G119 decompose additive identity T=e0+c0+S",
          r.e0 + r.c0 + r.synergy, r.total, 0.001)
    ok = r.synergy > 0 and r.corrosion_augmentation > 1.0 and 0.0 <= r.scale_removal <= 1.0
    RESULTS.append(("G119 model synergy>0 at high shear", r.synergy, r.synergy, 0, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] G119 model synergy>0 at high shear: "
          f"S={r.synergy:.3f} aug={r.corrosion_augmentation:.2f} removal={r.scale_removal:.2f}")
    return ok


def main():
    print("=" * 64)
    print("QC GATE 1 - PHYSICS VERIFICATION (analytical hand-calcs)")
    print("=" * 64)
    benches = [
        bench_norsok_node_20c, bench_norsok_5c_no_shear,
        bench_norsok_interpolation, bench_dnv_straight, bench_dnv_angle,
        bench_dnv_bend_magnitude, bench_falpha_peak, bench_blasius,
        bench_berger_hau, bench_g119_example, bench_g119_decompose,
        bench_monotonic_temperature,
    ]
    for b in benches:
        b()
    n_pass = sum(1 for r in RESULTS if r[4])
    n_tot = len(RESULTS)
    print("-" * 64)
    print(f"GATE 1: {n_pass}/{n_tot} checks passed")
    print("=" * 64)
    return 0 if n_pass == n_tot else 1


if __name__ == "__main__":
    sys.exit(main())
