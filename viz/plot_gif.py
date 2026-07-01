"""
plot_gif.py - Animated wall-loss evolution on the 90 deg elbow over service life,
contrasting two scenarios (clean vs sand-laden).

Metal loss is clamped to the pipe wall (12.7 mm): once a scenario reaches the
wall the pipe has PERFORATED and the curve plateaus with a perforation marker.
The title reports the erosion/corrosion split so the reader sees the field is
CO2-corrosion-dominated with an erosion/synergy contribution.
"""
from __future__ import annotations

import os
import sys
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_ROOT)
_ASSETS = os.path.join(_PROJECT_ROOT, "assets")

from src import constants as C            # noqa: E402
from src import ec_model as ecm           # noqa: E402
from src import elbow_field as ef         # noqa: E402

P = C.PALETTE


def _scenario(sand_ppmw, u_m, ph):
    D = 0.1016
    area = math.pi * D ** 2 / 4
    op = ecm.Operating(q_l_m3s=0.2 * u_m * area, q_g_m3s=0.8 * u_m * area,
                       diameter_m=D, temp_c=60, p_total_bar=60, p_co2_bar=1.0,
                       ph=ph, watercut=0.5, sand_ppmw=sand_ppmw, component="elbow")
    return ecm.evaluate(op)


def build(n_frames=60, t_wall_mm=None):
    if t_wall_mm is None:
        t_wall_mm = C.WALL_THICKNESS_MM
    # Moderate, realistic operating points (a few m/s, mild pH) so the field
    # EVOLVES over the service window instead of perforating in months.
    clean = _scenario(0.5, 2.5, ph=6.0)     # ~mild
    sandy = _scenario(80.0, 4.0, ph=5.5)    # more aggressive
    years = np.linspace(0.05, 6.0, n_frames)

    # per-year RATE field (unclamped at 1 yr for these moderate rates); the
    # loss at year t is min(rate*t, wall), applied per frame below.
    a, c, rate_clean = ef.wall_loss_field(
        clean.shear_pa, clean.erosion_mm_yr, clean.corrosion_protected_mm_yr,
        clean.corrosion_bare_mm_yr, 1.0)
    _, _, rate_sandy = ef.wall_loss_field(
        sandy.shear_pa, sandy.erosion_mm_yr, sandy.corrosion_protected_mm_yr,
        sandy.corrosion_bare_mm_yr, 1.0)
    lc = np.array(rate_clean)     # mm/yr per point
    ls = np.array(rate_sandy)

    def eros_share(r):
        tot = r.erosion_mm_yr + r.corrosion_protected_mm_yr + r.synergy_mm_yr
        return 100.0 * r.erosion_mm_yr / tot if tot > 0 else 0.0

    perf_clean = ef.time_to_perforation(lc.max(), t_wall_mm)
    perf_sandy = ef.time_to_perforation(ls.max(), t_wall_mm)

    fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(14, 4.6), dpi=150,
                                        gridspec_kw={"width_ratios": [1, 1, 0.9]})
    extent = [c[0], c[-1], a[0], a[-1]]
    im0 = ax0.imshow(np.minimum(lc * years[0], t_wall_mm), aspect="auto",
                     origin="lower", extent=extent, cmap="inferno", vmin=0, vmax=t_wall_mm)
    im1 = ax1.imshow(np.minimum(ls * years[0], t_wall_mm), aspect="auto",
                     origin="lower", extent=extent, cmap="inferno", vmin=0, vmax=t_wall_mm)
    for ax, title in [(ax0, f"Clean (0.5 ppmw, 2.5 m/s, pH 6.0)  eros {eros_share(clean):.1f}%"),
                      (ax1, f"Sand-laden (80 ppmw, 4 m/s, pH 5.5)  eros {eros_share(sandy):.1f}%")]:
        ax.set_xlabel("Circumferential [deg]", fontsize=9)
        ax.set_ylabel("Around bend [deg]", fontsize=9)
        ax.set_title(title, fontsize=9, fontweight="bold")
    cbar = fig.colorbar(im1, ax=ax1, pad=0.02)
    cbar.set_label("Wall loss [mm] (capped at wall)", fontsize=9)

    # peak-loss vs time, clamped at the wall
    peak_clean = np.minimum(lc.max() * years, t_wall_mm)
    peak_sandy = np.minimum(ls.max() * years, t_wall_mm)
    ax2.set_xlim(0, years[-1]); ax2.set_ylim(0, t_wall_mm * 1.08)
    ax2.axhline(t_wall_mm, color=P["charcoal"], lw=1, ls="--")
    ax2.text(0.2, t_wall_mm * 1.01, "nominal wall 12.7 mm (perforation)", fontsize=8,
             color=P["charcoal"])
    line_c, = ax2.plot([], [], color=P["teal"], lw=2, label="clean")
    line_s, = ax2.plot([], [], color=P["dark_red"], lw=2, label="sand-laden")
    for perf, col in [(perf_clean, P["teal"]), (perf_sandy, P["dark_red"])]:
        if math.isfinite(perf) and perf <= years[-1]:
            ax2.plot(perf, t_wall_mm, marker="v", color=col, ms=9)
    ax2.set_xlabel("Service time [yr]", fontsize=9)
    ax2.set_ylabel("Peak wall loss [mm]", fontsize=9)
    ax2.set_title("Peak wall loss vs time", fontsize=10, fontweight="bold")
    ax2.legend(frameon=False, fontsize=9)
    for ax in (ax0, ax1, ax2):
        for sp in ax.spines.values():
            sp.set_linewidth(0.7)

    txt = fig.suptitle("", fontsize=11, color=P["charcoal"])
    pbar = fig.add_axes([0.12, 0.005, 0.76, 0.012])
    pbar.axis("off")
    prog = pbar.barh(0, 0, height=1, color=P["steel"])

    def update(k):
        yr = years[k]
        im0.set_data(np.minimum(lc * yr, t_wall_mm))
        im1.set_data(np.minimum(ls * yr, t_wall_mm))
        line_c.set_data(years[:k + 1], peak_clean[:k + 1])
        line_s.set_data(years[:k + 1], peak_sandy[:k + 1])
        txt.set_text(f"ICS Week 11  |  Erosion-corrosion wall loss on elbow "
                     f"(CO2-corrosion-dominated)  |  t = {yr:.1f} yr")
        prog[0].set_width(yr / years[-1])
        return im0, im1, line_c, line_s

    anim = animation.FuncAnimation(fig, update, frames=n_frames, blit=False)
    out = os.path.join(_ASSETS, "elbow_wall_loss_evolution.gif")
    fig.text(0.99, 0.965, "INTEGRITY CODE SERIES", ha="right", fontsize=7,
             color=P["steel"])
    anim.save(out, writer=animation.PillowWriter(fps=6))
    plt.close(fig)
    pc = f"{perf_clean:.1f} yr" if math.isfinite(perf_clean) else ">6 yr"
    ps = f"{perf_sandy:.1f} yr" if math.isfinite(perf_sandy) else ">6 yr"
    print(f"wrote {out}  (clean perforation {pc}, sand-laden perforation {ps}; "
          f"loss clamped at {t_wall_mm} mm wall)")
    return out


if __name__ == "__main__":
    build()
