"""Surrogate GBR tests."""
import math
import pytest
from src import monte_carlo as mc
from src import surrogate_gbr as gbr


@pytest.fixture(scope="module")
def trained():
    ds = mc.run(n=3000, seed=11)
    X = ds.X()
    y = [math.log10(max(v, 1e-3)) for v in ds.y()]
    return gbr.train(X, y, n_estimators=120)


def test_split_sizes():
    X = [[i, i * 2] for i in range(100)]
    y = list(range(100))
    Xtr, Xte, ytr, yte = gbr.train_test_split(X, y, 0.2, seed=1)
    assert len(Xte) == 20 and len(Xtr) == 80


def test_split_no_overlap():
    X = [[i] for i in range(50)]
    y = list(range(50))
    Xtr, Xte, ytr, yte = gbr.train_test_split(X, y, 0.3, seed=2)
    assert set(ytr).isdisjoint(set(yte))


def test_metrics_keys(trained):
    _, metrics, _ = trained
    assert {"r2", "mae", "rmse", "backend"} <= set(metrics.keys())


def test_r2_reasonable(trained):
    _, metrics, _ = trained
    assert metrics["r2"] > 0.3  # surrogate explains a fair share of variance


def test_predictions_finite(trained):
    _, _, (Xte, yte, yp) = trained
    assert all(math.isfinite(p) for p in yp)


def test_mae_nonnegative(trained):
    _, metrics, _ = trained
    assert metrics["mae"] >= 0


def test_python_backend_runs():
    X = [[i, i % 3] for i in range(200)]
    y = [i * 0.5 for i in range(200)]
    m = gbr._PyGBR(n_estimators=20, max_depth=1, learning_rate=0.1)
    m.fit(X, y)
    assert math.isfinite(m.predict_one([10, 1]))
