"""
elbow_field.py - Spatial wall-loss field around a 90 deg elbow over service time.

Combines the DNV erosion bend rate, the NORSOK corrosion rate (shear-dependent),
the G119 synergy, and the experimentally observed angular shear distribution to
produce a 2D wall-loss map on the elbow surface (angle around bend x circumference).

[SOURCE: El-Gammal et al. 2010; Kim et al. 2021 elbow peak location - library]  T1
"""
from __future__ import annotations

import math

from . import constants as C
from . import hydrodynamics as hyd
from . import synergy_g119 as syn


def wall_loss_field(s_mean: float, e0_bend: float, c0_protected: float,
                    c0_bare: float, service_years: float,
                    n_angle: int = 73, n_circ: int = 48):
    """Compute wall-loss [mm] over the elbow surface after `service_years`.

    Grid:
        rows  = angular position around bend (0..90 deg), n_angle points
        cols  = circumferential position (0..360 deg), n_circ points
                (0 = extrados/outer, 180 = intrados/inner)
    Returns (angles_deg, circ_deg, loss_mm 2D list).
    """
    angles, shear_ext, shear_int = hyd.elbow_angular_shear_profile(s_mean, n_angle)
    circ = [360.0 * j / (n_circ - 1) for j in range(n_circ)]

    loss = []
    for i, a in enumerate(angles):
        row = []
        for cphi in circ:
            # blend extrados/intrados shear by circumferential position
            phi = math.radians(cphi)
            w_ext = 0.5 * (1.0 + math.cos(phi))   # 1 at 0 deg (extrados)
            w_int = 0.5 * (1.0 - math.cos(phi))   # 1 at 180 deg (intrados)
            s_local = w_ext * shear_ext[i] + w_int * shear_int[i]
            # local corrosion scales with local/mean shear via NORSOK shear term
            shear_scale = (s_local / s_mean) ** 0.3 if s_mean > 0 else 1.0
            c0_loc = c0_protected * shear_scale
            cbare_loc = c0_bare * shear_scale
            # local erosion scales with local velocity; shear~v^2 so
            # velocity ratio = sqrt(shear ratio); erosion ~ v^2.6
            vel_ratio = (s_local / s_mean) ** 0.5 if s_mean > 0 else 1.0
            e0_loc = e0_bend * vel_ratio ** 2.6
            res = syn.decompose(e0_loc, c0_loc, cbare_loc, s_local)
            # Metal loss is physically bounded by the wall: once cumulative loss
            # reaches the wall thickness the pipe has perforated and cannot thin
            # further. Clamp so the field never reports loss beyond the wall.
            row.append(min(res.total * service_years, C.WALL_THICKNESS_MM))
        loss.append(row)
    return angles, circ, loss


def time_to_perforation(rate_mm_yr: float,
                        wall_mm: float = None):
    """Years until cumulative loss reaches the wall (perforation). inf if rate<=0."""
    wall = C.WALL_THICKNESS_MM if wall_mm is None else wall_mm
    if rate_mm_yr <= 0:
        return float("inf")
    return wall / rate_mm_yr


def peak_loss(angles, circ, loss):
    """Return (max_loss_mm, angle_deg, circ_deg) of the worst point."""
    best = (-1.0, 0.0, 0.0)
    for i, a in enumerate(angles):
        for j, cphi in enumerate(circ):
            if loss[i][j] > best[0]:
                best = (loss[i][j], a, cphi)
    return best
