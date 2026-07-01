"""Monte Carlo + dataset tests."""
import pytest
from src import monte_carlo as mc


@pytest.fixture(scope="module")
def ds():
    return mc.run(n=2000, seed=11)


def test_dataset_size(ds):
    assert len(ds.rows) >= 1900  # most samples valid


def test_dataset_features(ds):
    assert ds.feature_names and ds.target_name == "total_mm_yr"


def test_X_shape(ds):
    X = ds.X()
    assert len(X) == len(ds.rows)
    assert len(X[0]) == len(ds.feature_names)


def test_y_positive(ds):
    assert all(v > 0 for v in ds.y())


def test_targets_physical_range(ds):
    # within NORSOK envelope, total should not be astronomically large
    assert max(ds.y()) < 500


@pytest.mark.parametrize("key", list(mc.MC_RANGES.keys()))
def test_ranges_valid(key):
    lo, hi = mc.MC_RANGES[key]
    assert lo < hi


def test_summary_stats(ds):
    st = mc.summary_stats(ds.y())
    assert st["p5"] <= st["p50"] <= st["p95"]
    assert st["min"] <= st["mean"] <= st["max"]


def test_summary_empty():
    assert mc.summary_stats([])["n"] == 0


def test_reproducible():
    a = mc.run(n=500, seed=7)
    b = mc.run(n=500, seed=7)
    assert a.y()[:10] == b.y()[:10]


def test_different_seed_differs():
    a = mc.run(n=500, seed=1)
    b = mc.run(n=500, seed=2)
    assert a.y()[:10] != b.y()[:10]


@pytest.mark.parametrize("regime", ["segregated", "intermittent", "distributed", "transition"])
def test_regime_values(ds, regime):
    regimes = {r["regime"] for r in ds.rows}
    assert regimes.issubset(
        {"segregated", "intermittent", "distributed", "transition"})
