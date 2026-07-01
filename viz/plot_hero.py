"""
plot_hero.py - HERO visual: erosion-corrosion wall-loss field on a 90 deg elbow.

Spatial wall-loss map over the elbow surface (bend angle vs circumference) after
a service interval. The angular shear profile is a PRESCRIBED analytical shape
fitted to the peak locations reported by El-Gammal 2010 / Kim 2021 (extrados peak
~37 deg; a stronger intrados inlet peak), NOT a resolved CFD field. Wall loss is
clamped to the pipe wall (12.7 mm). The field is CO2-corrosion-dominated with an
erosion/synergy contribution; the split is shown in the title.
"""
from __future__ import annotations

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
from src import ec_model as ecm           # noqa: E402
from src import elbow_field as ef         # noqa: E402

P = C.PALETTE


def _style(ax):
    for spine in ax.spines.values():
        spine.set_linewidth(0.7)
        spine.set_color(C.PALETTE["charcoal"])
    ax.tick_params(direction="out", width=0.7, which="both")
    ax.minorticks_on()


def build():
    # Representative sour multiphase elbow at a MODERATE operating point (a few
    # m/s, mild pH) so the 3-yr field shows a spatial gradient rather than
    # saturating the wall everywhere.
    import math
    D = 0.1524
    area = math.pi * D ** 2 / 4
    u_m = 4.0
    op = ecm.Operating(q_l_m3s=0.25 * u_m * area, q_g_m3s=0.75 * u_m * area,
                       diameter_m=D, temp_c=60, p_total_bar=60, p_co2_bar=1.0,
                       ph=5.9, watercut=0.6, sand_ppmw=10.0, r_over_d=1.5,
                       component="elbow")
    res = ecm.evaluate(op)
    service_years = 3.0
    angles, circ, loss = ef.wall_loss_field(
        res.shear_pa, res.erosion_mm_yr, res.corrosion_protected_mm_yr,
        res.corrosion_bare_mm_yr, service_years)
    loss = np.array(loss)
    pk, pa_ang, pc_circ = ef.peak_loss(angles, circ, loss.tolist())

    fig = plt.figure(figsize=(13, 6.2), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.28)

    # Panel (a): 2D wall-loss heatmap
    ax0 = fig.add_subplot(gs[0, 0])
    extent = [circ[0], circ[-1], angles[0], angles[-1]]
    im = ax0.imshow(loss, aspect="auto", origin="lower", extent=extent,
                    cmap="inferno")
    cbar = fig.colorbar(im, ax=ax0, pad=0.02)
    cbar.set_label("Wall loss after 3 yr [mm]", fontsize=10)
    ax0.set_xlabel("Circumferential position [deg]  (0=extrados, 180=intrados)",
                   fontsize=10)
    ax0.set_ylabel("Position around bend [deg]", fontsize=10)
    ax0.axhline(C.ELBOW_EXTRADOS_PEAK_DEG, color="white", lw=0.8, ls="--",
                alpha=0.6)
    ax0.annotate(f"extrados feature ~{C.ELBOW_EXTRADOS_PEAK_DEG:.0f} deg (secondary)",
                 xy=(8, C.ELBOW_EXTRADOS_PEAK_DEG), color="white", fontsize=8,
                 va="bottom")
    ax0.plot(pc_circ, pa_ang, marker="x", color="cyan", ms=10, mew=2)
    ax0.annotate(f"global peak {pk:.1f} mm @ {pa_ang:.0f} deg (intrados inlet)",
                 xy=(pc_circ, pa_ang), color="cyan", fontsize=8, va="top")
    ax0.set_title("(a) Erosion-corrosion wall-loss field on 90 deg elbow",
                  fontsize=11, loc="left", fontweight="bold")
    _style(ax0)

    # Panel (b): angular profiles extrados vs intrados (the physics signature)
    ax1 = fig.add_subplot(gs[0, 1])
    extr = loss[:, 0]          # circ=0 -> extrados
    mid = loss[:, loss.shape[1] // 2]   # circ=180 -> intrados
    ax1.plot(angles, extr, color=P["dark_red"], lw=2.0, label="extrados (outer)")
    ax1.plot(angles, mid, color=P["navy"], lw=2.0, label="intrados (inner)")
    ax1.axvline(C.ELBOW_EXTRADOS_PEAK_DEG, color=P["charcoal"], lw=0.8, ls=":")
    ax1.set_xlabel("Position around bend [deg]", fontsize=10)
    ax1.set_ylabel("Wall loss after 3 yr [mm]", fontsize=10)
    ax1.set_title("(b) Extrados vs intrados loss profile", fontsize=11,
                  loc="left", fontweight="bold")
    ax1.legend(frameon=False, fontsize=9, loc="upper right")
    _style(ax1)

    _tot = res.erosion_mm_yr + res.corrosion_protected_mm_yr + res.synergy_mm_yr
    _es = 100.0 * res.erosion_mm_yr / _tot if _tot > 0 else 0.0
    _ss = 100.0 * res.synergy_mm_yr / _tot if _tot > 0 else 0.0
    fig.suptitle(
        f"ICS Week 11  |  Erosion-Corrosion on multiphase elbow  |  "
        f"{res.regime} flow, u_m={res.u_m:.1f} m/s, S={res.shear_pa:.0f} Pa  |  "
        f"split: erosion {_es:.1f}% / synergy {_ss:.1f}% / corrosion {100-_es-_ss:.1f}%",
        fontsize=10.5, y=0.99, color=P["charcoal"])
    fig.text(0.99, 0.01, "INTEGRITY CODE SERIES  |  NORSOK M-506:2017 + DNV-RP-O501 + ASTM G119",
             ha="right", va="bottom", fontsize=7, color=P["steel"])

    out = os.path.join(_ASSETS, "hero_erosion_corrosion_week11.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}  (peak {pk:.2f} mm @ {pa_ang:.0f} deg, {pc_circ:.0f} circ)")
    return out


if __name__ == "__main__":
    build()
