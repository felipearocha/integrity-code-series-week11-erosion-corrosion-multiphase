"""
surrogate_gbr.py - Gradient-boosted-regression surrogate of the coupled
erosion-corrosion model, for fast inference and sensitivity analysis.

Falls back to a pure-Python gradient-boosting implementation if scikit-learn
is unavailable, so the package runs without heavyweight ML dependencies.
"""
from __future__ import annotations



def train_test_split(X, y, test_frac=0.2, seed=11):
    import random
    rng = random.Random(seed)
    idx = list(range(len(X)))
    rng.shuffle(idx)
    n_test = int(len(X) * test_frac)
    test_idx = set(idx[:n_test])
    Xtr, ytr, Xte, yte = [], [], [], []
    for i in range(len(X)):
        if i in test_idx:
            Xte.append(X[i]); yte.append(y[i])
        else:
            Xtr.append(X[i]); ytr.append(y[i])
    return Xtr, Xte, ytr, yte


def _metrics(y_true, y_pred):
    n = len(y_true)
    mean = sum(y_true) / n
    ss_tot = sum((v - mean) ** 2 for v in y_true)
    ss_res = sum((t - p) ** 2 for t, p in zip(y_true, y_pred))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    mae = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / n
    rmse = (ss_res / n) ** 0.5
    return {"r2": r2, "mae": mae, "rmse": rmse}


def train(X, y, test_frac=0.2, seed=11, n_estimators=200, max_depth=3,
          learning_rate=0.05):
    """Train a GBR surrogate. Returns (model, metrics, (Xte, yte, ypred))."""
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_frac, seed)
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        model = GradientBoostingRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            learning_rate=learning_rate, random_state=seed)
        model.fit(Xtr, ytr)
        ypred = list(model.predict(Xte))
        backend = "sklearn"
    except Exception:
        model = _PyGBR(n_estimators=min(n_estimators, 60), max_depth=max_depth,
                       learning_rate=learning_rate)
        model.fit(Xtr, ytr)
        ypred = [model.predict_one(x) for x in Xte]
        backend = "python"
    metrics = _metrics(yte, ypred)
    metrics["backend"] = backend
    return model, metrics, (Xte, yte, ypred)


# ---- minimal pure-Python gradient boosting (regression-stump ensemble) ----
class _Stump:
    __slots__ = ("feat", "thr", "left", "right")

    def __init__(self, feat, thr, left, right):
        self.feat = feat; self.thr = thr; self.left = left; self.right = right

    def predict_one(self, x):
        return self.left if x[self.feat] <= self.thr else self.right


class _PyGBR:
    def __init__(self, n_estimators=50, max_depth=1, learning_rate=0.1):
        self.n = n_estimators
        self.lr = learning_rate
        self.base = 0.0
        self.trees = []

    def fit(self, X, y):
        self.base = sum(y) / len(y)
        pred = [self.base] * len(y)
        n_feat = len(X[0])
        import random
        rng = random.Random(7)
        for _ in range(self.n):
            resid = [y[i] - pred[i] for i in range(len(y))]
            best = None
            feats = rng.sample(range(n_feat), max(1, n_feat // 2))
            for f in feats:
                vals = sorted(set(x[f] for x in X))
                if len(vals) < 2:
                    continue
                for q in (0.25, 0.5, 0.75):
                    thr = vals[int(q * (len(vals) - 1))]
                    lv = [resid[i] for i in range(len(X)) if X[i][f] <= thr]
                    rv = [resid[i] for i in range(len(X)) if X[i][f] > thr]
                    if not lv or not rv:
                        continue
                    lm = sum(lv) / len(lv); rm = sum(rv) / len(rv)
                    err = sum((v - lm) ** 2 for v in lv) + sum((v - rm) ** 2 for v in rv)
                    if best is None or err < best[0]:
                        best = (err, f, thr, lm, rm)
            if best is None:
                break
            _, f, thr, lm, rm = best
            self.trees.append(_Stump(f, thr, lm, rm))
            for i in range(len(X)):
                pred[i] += self.lr * self.trees[-1].predict_one(X[i])
        return self

    def predict_one(self, x):
        return self.base + self.lr * sum(t.predict_one(x) for t in self.trees)
