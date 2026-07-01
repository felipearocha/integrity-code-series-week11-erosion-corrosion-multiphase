"""Visualization output existence + integrity (QC Gate 2)."""
import os
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ASSETS = os.path.join(_ROOT, "assets")

EXPECTED_PNGS = [
    "hero_erosion_corrosion_week11.png",
    "flow_regime_map.png",
    "synergy_decomposition.png",
    "shear_vs_corrosion.png",
    "sensitivity_tornado.png",
    "mc_distribution.png",
    "kaeri_validation.png",
]


@pytest.mark.parametrize("fname", EXPECTED_PNGS)
def test_png_exists(fname):
    assert os.path.exists(os.path.join(_ASSETS, fname))


@pytest.mark.parametrize("fname", EXPECTED_PNGS)
def test_png_nonzero(fname):
    assert os.path.getsize(os.path.join(_ASSETS, fname)) > 5000


@pytest.mark.parametrize("fname", EXPECTED_PNGS)
def test_png_header(fname):
    with open(os.path.join(_ASSETS, fname), "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"


def test_gif_exists():
    assert os.path.exists(os.path.join(_ASSETS, "elbow_wall_loss_evolution.gif"))


def test_gif_nonzero():
    assert os.path.getsize(
        os.path.join(_ASSETS, "elbow_wall_loss_evolution.gif")) > 50000


def test_gif_min_frames():
    from PIL import Image
    im = Image.open(os.path.join(_ASSETS, "elbow_wall_loss_evolution.gif"))
    assert im.n_frames >= 50


def test_dataset_exists():
    assert os.path.exists(os.path.join(_ASSETS, "mc_dataset.csv"))


def test_dataset_min_rows():
    with open(os.path.join(_ASSETS, "mc_dataset.csv")) as f:
        n = sum(1 for _ in f) - 1  # minus header
    assert n >= 10000
