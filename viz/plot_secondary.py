"""
plot_secondary.py - Secondary visuals (all from real model output):
  1. Beggs-Brill flow-regime map with the operating point overlaid
  2. ASTM G119 synergy decomposition (E0 / C0 / dCw / dWc)
  3. Wall shear stress vs NORSOK corrosion rate (with scale-stripping zone)
  4. Sensitivity tornado (surrogate feature importance)
  5. Monte Carlo total wall-loss-rate distribution
  6. NORSOK Kt temperature curve + KAERI experimental FAC overlay
"""
from __future__ import annotations

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_ROOT)
_ASSETS = os.path.join(_PROJECT_ROOT, "assets")

from src import constants as C            # noqa: E402
from src import multiphase_flow as mpf    # noqa: E402
from src import corrosion_norsok as cor   # noqa: E402
from src import ec_model as ecm           # noqa: E402
from src import synergy_g119 as syn       # noqa: E402
from src import monte_carlo as mc         # noqa: E402

P = C.PALETTE


def _style(ax):
    for sp in ax.spines.values():
        sp.set_linewidth(0.7); sp.set_color(P["charcoal"])
    ax.tick_params(direction="out", width=0.7, which="both")
    ax.minorticks_on()
    ax.grid(True, lw=0.35, color="0.85")


def flow_regime_map():
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=300)
    cl = np.logspace(-3, 0, 200)
    fr = np.logspace(-2, 3, 200)
    grid = np.zeros((len(fr), len(cl)))
    codes = {"segregated": 0, "transition": 1, "intermittent": 2, "distributed": 3}
    for i, f in enumerate(fr):
        for j, c in enumerate(cl):
            grid[i, j] = codes[mpf.beggs_brill_regime(c, f)]
    im = ax.pcolormesh(cl, fr, grid, cmap="YlGnBu", shading="auto", alpha=0.85)
    ax.set_xscale("log"); ax.set_yscale("log")
    # operating point
    D = 0.1524; area = math.pi * D**2 / 4; u_m = 8.0
    op = ecm.Operating(q_l_m3s=0.25*u_m*area, q_g_m3s=0.75*u_m*area, diameter_m=D,
                       temp_c=60, p_total_bar=60, p_co2_bar=1.0, ph=5.5)
    fs = mpf.resolve_flow(op.q_l_m3s, op.q_g_m3s, D, watercut=0.6)
    ax.plot(fs.lambda_l, fs.froude, "o", color=P["dark_red"], ms=13, mec="white",
            mew=1.5, zorder=5, label=f"operating point ({fs.regime})")
    ax.set_xlabel("No-slip liquid holdup C_L [-]", fontsize=10)
    ax.set_ylabel("Mixture Froude number Fr_m [-]", fontsize=10)
    ax.set_title("Beggs-Brill (1973) flow-regime map with operating point",
                 fontsize=11, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2, 3])
    cbar.ax.set_yticklabels(["segregated", "transition", "intermittent", "distributed"])
    _style(ax)
    out = os.path.join(_ASSETS, "flow_regime_map.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out


def synergy_decomposition():
    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=300)
    # severity ladder (4 in elbow): corrosion-dominated -> erosion-dominated
    scenarios = [("normal\n6 m/s, 10 ppmw", 6.0, 10.0),
                 ("high sand\n15 m/s, 50 ppmw", 15.0, 50.0),
                 ("loss of sand control\n20 m/s, 200 ppmw (P-002)", 20.0, 200.0)]
    D = 0.1016; area = math.pi*D**2/4
    labels, e0s, c0s, dcw, dwc = [], [], [], [], []
    for name, u_m, sand in scenarios:
        op = ecm.Operating(q_l_m3s=0.2*u_m*area, q_g_m3s=0.8*u_m*area, diameter_m=D,
                           temp_c=60, p_total_bar=60, p_co2_bar=1.0, ph=5.5,
                           watercut=0.5, sand_ppmw=sand)
        r = ecm.evaluate(op)
        sr = syn.decompose(r.erosion_mm_yr, r.corrosion_protected_mm_yr,
                           r.corrosion_bare_mm_yr, r.shear_pa)
        labels.append(name); e0s.append(sr.e0); c0s.append(sr.c0)
        dcw.append(sr.d_cw); dwc.append(sr.d_wc)
    x = np.arange(len(labels))
    ax.bar(x, c0s, label="C0 pure corrosion (scaled)", color=P["steel"])
    ax.bar(x, e0s, bottom=c0s, label="E0 pure erosion", color=P["navy"])
    b2 = [c+e for c, e in zip(c0s, e0s)]
    ax.bar(x, dcw, bottom=b2, label="dCw erosion-enhanced corrosion", color=P["teal"])
    b3 = [b+d for b, d in zip(b2, dcw)]
    ax.bar(x, dwc, bottom=b3, label="dWc corrosion-enhanced erosion", color=P["dark_red"])
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Wall-loss rate [mm/yr]", fontsize=10)
    ax.set_title("ASTM G119 erosion-corrosion synergy decomposition",
                 fontsize=11, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    _style(ax)
    out = os.path.join(_ASSETS, "synergy_decomposition.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out


def shear_vs_corrosion():
    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=300)
    shears = np.linspace(1, 150, 120)
    for T, col in [(40, P["steel"]), (60, P["navy"]), (90, P["teal"])]:
        cr = [cor.corrosion_rate(T, 1.0, 60, s, 5.5) for s in shears]
        ax.plot(shears, cr, color=col, lw=2.0, label=f"{T} C")
    ax.axvspan(10, 20, color=P["dark_red"], alpha=0.12)
    ax.text(15, ax.get_ylim()[1]*0.9, "FeCO3\nscale stripping\n(~10-20 Pa)",
            ha="center", fontsize=8, color=P["dark_red"])
    ax.set_xlabel("Wall shear stress S [Pa]  (NORSOK Eq.21)", fontsize=10)
    ax.set_ylabel("NORSOK CO2 corrosion rate [mm/yr]", fontsize=10)
    ax.set_title("Wall shear stress vs NORSOK M-506:2017 corrosion rate",
                 fontsize=11, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, title="temperature")
    _style(ax)
    out = os.path.join(_ASSETS, "shear_vs_corrosion.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out


def sensitivity_tornado():
    import json
    fi_path = os.path.join(_ASSETS, "feature_importance.json")
    if not os.path.exists(fi_path):
        return None
    fi = json.load(open(fi_path))
    items = sorted(fi.items(), key=lambda t: t[1])
    names = [k for k, _ in items]; vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=300)
    colors = [P["navy"] if v == max(vals) else P["steel"] for v in vals]
    ax.barh(names, vals, color=colors)
    ax.set_xlabel("Surrogate feature importance [-]", fontsize=10)
    ax.set_title("Sensitivity tornado (GBR surrogate over >12k MC runs)",
                 fontsize=11, loc="left", fontweight="bold")
    _style(ax)
    out = os.path.join(_ASSETS, "sensitivity_tornado.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out


def mc_distribution():
    ds = mc.run(n=12000, seed=11)
    vals = [v for v in ds.y() if v > 0]
    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=300)
    ax.hist(vals, bins=np.logspace(np.log10(min(vals)), np.log10(max(vals)), 50),
            color=P["steel"], edgecolor=P["navy"], lw=0.4)
    ax.set_xscale("log")
    st = mc.summary_stats(vals)
    for q, lab, col in [(st["p50"], "p50", P["navy"]),
                        (st["p95"], "p95", P["dark_red"])]:
        ax.axvline(q, color=col, lw=1.5, ls="--", label=f"{lab}={q:.1f} mm/yr")
    ax.axvline(0.3, color=P["teal"], lw=1.5, label="0.3 mm/yr allowable (P-002 basis)")
    ax.set_xlabel("Total erosion-corrosion wall-loss rate [mm/yr]", fontsize=10)
    ax.set_ylabel("Count", fontsize=10)
    ax.set_title("Monte Carlo wall-loss distribution (12,000 runs)",
                 fontsize=11, loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    _style(ax)
    out = os.path.join(_ASSETS, "mc_distribution.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out


def kaeri_validation():
    """NORSOK Kt curve + KAERI 2021 experimental FAC-rate vs flow overlay."""
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    # left: Kt curve
    temps = list(C.NORSOK_KT_TEMPS)
    kts = [C.NORSOK_KT[t] for t in temps]
    ax0.plot(temps, kts, "o-", color=P["navy"], lw=2, ms=7)
    ax0.axvline(60, color=P["dark_red"], lw=1, ls=":")
    ax0.text(62, max(kts)*0.95, "Kt peak 60 C\n(FeCO3 protection)", fontsize=8,
             color=P["dark_red"])
    ax0.set_xlabel("Temperature [C]", fontsize=10)
    ax0.set_ylabel("NORSOK M-506:2017 constant Kt", fontsize=10)
    ax0.set_title("(a) NORSOK Kt vs temperature (Table 1, 2017)", fontsize=11,
                  loc="left", fontweight="bold")
    _style(ax0)
    # right: KAERI experimental FAC rate vs flow (Table 2, library copy)
    flow = [2, 4, 7, 10, 12]
    pipe = [0.54, 0.8, 0.99, None, None]
    cyl = [0.83, 1.38, None, 9.1, None]
    fp = [(f, v) for f, v in zip(flow, pipe) if v is not None]
    fc = [(f, v) for f, v in zip(flow, cyl) if v is not None]
    ax1.plot([f for f, _ in fp], [v for _, v in fp], "s-", color=P["steel"],
             lw=2, ms=8, label="pipe specimen (KAERI 2021)")
    ax1.plot([f for f, _ in fc], [v for _, v in fc], "^-", color=P["dark_red"],
             lw=2, ms=8, label="cylindrical specimen (KAERI 2021)")
    ax1.set_xlabel("Flow rate [m/s]", fontsize=10)
    ax1.set_ylabel("FAC rate [mm/yr]  @150 C", fontsize=10)
    ax1.set_title("(b) KAERI 2021 experimental FAC benchmark", fontsize=11,
                  loc="left", fontweight="bold")
    ax1.legend(frameon=False, fontsize=8)
    _style(ax1)
    fig.text(0.99, 0.01, "Data: Kim et al. Nucl Eng Tech 53 (2021) 3003-3011 Table 2 (library copy)",
             ha="right", va="bottom", fontsize=7, color=P["steel"])
    out = os.path.join(_ASSETS, "kaeri_validation.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out


def build_all():
    outs = [flow_regime_map(), synergy_decomposition(), shear_vs_corrosion(),
            sensitivity_tornado(), mc_distribution(), kaeri_validation()]
    for o in outs:
        if o:
            print("wrote", os.path.basename(o))
    return outs


if __name__ == "__main__":
    build_all()
