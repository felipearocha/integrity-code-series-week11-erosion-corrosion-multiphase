# Integrity Code Series — Week 11

## Coupled Erosion-Corrosion in Multiphase Oil & Gas Production Piping at Bends

[![CI](https://github.com/felipearocha/integrity-code-series-week11-erosion-corrosion-multiphase/actions/workflows/ci.yml/badge.svg)](https://github.com/felipearocha/integrity-code-series-week11-erosion-corrosion-multiphase/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests: 466 passing](https://img.shields.io/badge/tests-466%20passing-brightgreen.svg)](tests)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21114866.svg)](https://doi.org/10.5281/zenodo.21114866)

---

**Service:** sand-laden CO2 (sweet) multiphase production piping, carbon steel, 90 deg elbows
**Standards:** NORSOK M-506:2017 (Rev.3), DNV-RP-O501 Rev.4.2, NORSOK P-002, ASTM G119, API 571 Sec.3.27, API 579-1 Part 5
**Validation:** Kim et al. (KAERI) Nucl Eng Tech 53 (2021) 3003-3011; Madani Sani et al. Wear 426-427 (2019)

## Problem Statement

A 90 degree elbow carrying a sand-laden gas-liquid stream degrades by two coupled
mechanisms that neither acts alone: mechanical **erosion** from impacting sand, and
**CO2 corrosion** of carbon steel. The coupling is physical - high wall shear and
particle impact strip the protective iron-carbonate (FeCO3) scale, re-exposing bare
steel whose corrosion reverts to high rates. This erosion-corrosion **synergy**
(ASTM G119) localises wall loss at the elbow, where the flow field concentrates
both shear and impact.

API RP 14E reduces this to a single density-based velocity limit and gives no
erosion rate and no solids guidance (Madani Sani et al. 2019). This package instead
resolves the hydrodynamics and runs the codified erosion and corrosion models
together.

**The question:** where on the elbow, and how fast, does the wall thin - and which
operating parameters govern it?

## Coupling Chain

```
multiphase flow (Beggs-Brill regime + holdup)
        |
        v
mixture density / velocity / viscosity
        |
        +--> wall shear stress S  (NORSOK M-506:2017 Eq.21-22)
        +--> mass-transfer coeff  (Berger-Hau Sh = 0.0165 Re^0.86 Sc^0.33)
        |
        v
erosion (DNV-RP-O501 bend model) + corrosion (NORSOK M-506:2017 with S-term)
        |
        v
ASTM G119 synergy: T = E0 + C0 + dCw + dWc   (scale-removal driven)
        |
        v
wall-loss field on elbow (extrados ~37 deg peak + intrados inlet peak)
        |
        v
API 579-1 Part 5 RSF + remaining life
        |
        +--> Monte Carlo (>=10k) -> GBR surrogate -> sensitivity
        +--> SHA-256 audit chain + sensor validation
```

## Governing Equations

Every constant is tagged to its source standard or paper. The equations render
below directly on GitHub; a full styled reference is in
[`docs/equations.html`](docs/equations.html) —
[**view it rendered**](https://htmlpreview.github.io/?https://github.com/felipearocha/integrity-code-series-week11-erosion-corrosion-multiphase/blob/main/docs/equations.html).

### Sand erosion — DNV-RP-O501 Rev.4.2 (designated by NORSOK P-002 Clause 8.6.4)

Characteristic bend impact angle and bend erosion rate (Eqs. 8.15–8.21):

$$\alpha = \arctan\left(\frac{1}{2\sqrt{R/D}}\right) \qquad \dot{E}_L = \left[\frac{K\,\dot{m}_p\,U_p^{n}\,F(\alpha)}{\rho_t\,A_t}\right] C_1\,C_\mathrm{unit} \qquad A_t = \frac{\pi D^2}{4\sin\alpha}$$

The angle dependence is carried by $F(\alpha)$ and by the $1/\sin\alpha$ inside $A_t$ — there is **no extra** $\sin\alpha$ in the numerator (adding one underpredicts bend erosion by a factor $\sin\alpha$). Carbon steel $K=2.0\times10^{-9}$, $n=2.6$, $C_1=2.5$ (Table 7-2); $F(\alpha)$ is the 8-term polynomial (Table 7-1).

### CO₂ corrosion — NORSOK M-506:2017 (Rev.3)

$$\mathrm{CR}_t = K_t\, f_{\mathrm{CO_2}}^{0.62} \left(\frac{S}{19}\right)^{0.146 + 0.0324\log_{10} f_{\mathrm{CO_2}}} f(\mathrm{pH})_t \qquad f_{\mathrm{CO_2}} = a\,p_{\mathrm{CO_2}} \qquad a = 10^{\,P(0.0031 - 1.4/T)}$$

9-node $K_t$ table (5–150 °C; separate low-temperature forms at 5 °C and 15 °C); wall shear $S$ from Eqs. 21–22; $f(\mathrm{pH})_t$ from Table 2; $f_{\mathrm{CO_2}}$ clamped to the $[0.1,\,10]$ bar window.

### Multiphase flow — Beggs-Brill (1973)

$$\lambda_L = \frac{q_L}{q_L+q_g} \qquad E_L(0) = \frac{a\,\lambda_L^{b}}{\mathrm{Fr}^{c}} \qquad E_L^{\text{trans}} = A\,E_L^{\text{seg}} + (1-A)\,E_L^{\text{int}},\quad A = \frac{L_3-\mathrm{Fr}}{L_3-L_2}$$

### Wall shear and mass transfer (NORSOK Eqs. 21–22 · Berger-Hau)

$$\tau_w = \tfrac{1}{2}\rho_m f\,u_m^2 \qquad f = 0.001375\left[1 + \left(\frac{2\times10^4\,\varepsilon}{D} + \frac{10^6\,\mu_m}{\rho_m u_m D}\right)^{1/3}\right] \qquad \mathrm{Sh} = 0.0165\,\mathrm{Re}^{0.86}\,\mathrm{Sc}^{0.33}$$

### Erosion-corrosion synergy — ASTM G119

$$T = W_0 + C_0 + S \qquad S = \Delta C_w + \Delta W_c$$

The scale-removal split is driven by wall shear and erosion; its coefficients are heuristic (see [Model-fidelity notes](#model-fidelity-notes-honest-scope)).

### Fitness-for-service — API 579-1 Part 5 (RSF with Folias factor)

$$\mathrm{RSF} = \frac{1 - R_t}{1 - R_t/M_t} \qquad M_t = \sqrt{1 + 0.48\,\lambda^2} \qquad \lambda = \frac{1.285\,L}{\sqrt{R\,t}} \qquad \mathrm{RSF}_a = 0.90$$

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py                 # benchmarks + dataset + all visuals
python validation/benchmarks.py   # QC Gate 1 (14 hand-calcs)
python -m pytest tests/ -q        # 466 tests
```

## Repository Structure

```
src/
  constants.py          standard-derived constants, each [SOURCE]-tagged
  multiphase_flow.py    Beggs-Brill regime + holdup, mixture properties
  hydrodynamics.py      NORSOK wall shear, Berger-Hau MTC, elbow profile
  erosion_dnv.py        DNV-RP-O501 straight + bend erosion
  corrosion_norsok.py   NORSOK M-506:2017 CO2 corrosion rate
  synergy_g119.py       ASTM G119 erosion-corrosion synergy
  elbow_field.py        2D wall-loss field over the elbow
  ffs_api579.py         API 579-1 Part 5 RSF + remaining life
  ec_model.py           coupled-model coordinator
  monte_carlo.py        >=10k MC dataset
  surrogate_gbr.py      GBR surrogate (sklearn, pure-python fallback)
  cybersecurity.py      audit chain + sensor validation + fingerprint
validation/benchmarks.py   QC Gate 1 analytical hand-calcs
viz/                    plot_hero.py, plot_secondary.py, plot_gif.py
tests/                  466 tests across 12 modules
assets/                 hero, 6 secondary PNGs, GIF, dataset, surrogate metrics
docs/equations.html     rendered (MathJax) governing-equations reference
```

## Key Result

The elbow wall-loss field uses a PRESCRIBED angular shear profile whose peak
locations are fitted to the pattern reported by El-Gammal et al. 2010 / Kim et
al. 2021 (an extrados feature ~37 deg plus a stronger intrados inlet peak, which
carries the global maximum) - this is an input shape fitted to the experiment,
not a resolved CFD field. Metal loss is clamped to the pipe wall (12.7 mm) and
the visuals report time-to-perforation.

Under the sampled operating envelope the wall loss is **CO2-corrosion-dominated**:
sand erosion contributes ~2% of the median total and the erosion-corrosion
synergy ~15%. The Monte Carlo surrogate accordingly ranks pH, temperature and
CO2 as the dominant drivers with wall shear secondary; the erosion/sand drivers
are near zero. "Erosion-corrosion" is the standard damage-mechanism name
(API 571 3.27 / ASTM G119), not a 50/50 numerical split.

## Model-fidelity notes (honest scope)

- The G119 synergy split (scale-removal threshold, bare-steel proxy, d_wc
  coefficient) uses **heuristic (T3)** constants; ASTM G119 supplies the additive
  framework, not the predictive coefficients.
- Beggs-Brill liquid holdup and the Berger-Hau mass-transfer coefficient are
  computed as **diagnostics**; the flow effect on corrosion is carried by the
  NORSOK wall-shear term (as NORSOK M-506 intends), not by holdup or MTC.
- `ffs_api579.rsf_part5()` implements the true Part-5 Level-1 RSF with the Folias
  bulging factor Mt; `remaining_strength_factor()` is a depth-only screening proxy.

## Escalation Table

| Week | Topic | Key escalation |
|------|-------|---------------|
| 9 | CUI | 3 coupled PDEs, Strang splitting |
| 10 | NNpHSCC | Chen-Sutherby-Xing crack growth, crack colony, COV=61.2% epistemic |
| **11** | **Erosion-corrosion** | **Coupled DNV erosion + NORSOK CO2 + Beggs-Brill flow + G119 synergy + API 579 Part 5 FFS** |

## Cybersecurity (STRIDE)

SHA-256 hash-chain audit for all runs; sensor-envelope validation; coefficient
fingerprint; surrogate out-of-distribution fallback. See `src/cybersecurity.py`.

## Anti-Hallucination Note

Every equation and constant carries an explicit `[SOURCE: ...]` tag with tier
(T1 standard/paper, T2 derived, T3 practitioner). The NORSOK M-506 model was
transcribed from the controlled 2017 (Rev.3) copy - not the older Rev.1 widely
posted online, which lacks the 5 C / 15 C nodes and the pH2S applicability limit.

The tiers are applied honestly. Where a coupling term is a modelling assumption
rather than a standard value it is tagged **T3** and called out in the
"Model-fidelity notes" section above - specifically the ASTM G119 synergy split
coefficients, the bare-steel-corrosion proxy, and the prescribed elbow shear
profile (whose peak locations are fitted to El-Gammal/Kim, not resolved by CFD).
The T1 constants that ARE read directly from a controlled copy - the NORSOK Kt
9-node table, the DNV `F(alpha)` polynomial, and the Beggs-Brill holdup
coefficients - are each verified against their source by a QC Gate hand-calc.

## Disclaimer

Research tool only. Not for design, fitness-for-service, or safety-critical
decisions without site-specific calibration and independent PE review.

## License

MIT - Felipe Rocha. See [LICENSE](LICENSE).

## How to Cite

If this software contributes to your work, please cite the archived release:

> Rocha, F. (2026). *Integrity Code Series — Week 11 — Coupled Erosion-Corrosion in Multiphase Piping at Bends* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.21114866

**BibTeX:**

```bibtex
@software{rocha_2026_erosion_corrosion,
  author    = {Rocha, Felipe},
  title     = {{Integrity Code Series --- Week 11 --- Coupled
               Erosion-Corrosion in Multiphase Piping at Bends}},
  year      = 2026,
  publisher = {Zenodo},
  version   = {v1.0.0},
  doi       = {10.5281/zenodo.21114866},
  url       = {https://doi.org/10.5281/zenodo.21114866}
}
```

| DOI | Points to |
|-----|-----------|
| [`10.5281/zenodo.21114866`](https://doi.org/10.5281/zenodo.21114866) (concept) | Always resolves to the latest version — use for citation. |
| [`10.5281/zenodo.21114867`](https://doi.org/10.5281/zenodo.21114867) (version) | Pinned to v1.0.0 — use when reproducibility matters. |

A machine-readable [`CITATION.cff`](CITATION.cff) drives GitHub's "Cite this repository" widget.

## Integrity Code Series

Part of an ongoing series of physics-first integrity simulators by Felipe Rocha:

| # | Repo | Domain |
|---|---|---|
| Week 3 | [integrity-code-series-week3-f1-lap-simulation](https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation) | F1 lap simulation (six coupled ODEs) |
| Week 6 | [integrity-code-series-week6-smartphone-galvanic](https://github.com/felipearocha/integrity-code-series-week6-smartphone-galvanic) | Smartphone galvanic corrosion (Laplace + Butler-Volmer) |
| Week 7 | [integrity-code-series-week7-h2-lferw](https://github.com/felipearocha/integrity-code-series-week7-h2-lferw) | LF-ERW H2 conversion (B31.12 + NACE TM0316) |
| Week 8 | [integrity-code-series-week8-creep-fatigue-heater](https://github.com/felipearocha/integrity-code-series-week8-creep-fatigue-heater) | Creep-fatigue 9Cr-1Mo (Norton/Omega + Coffin-Manson) |
| Week 9 | [integrity-code-series-week9-cui](https://github.com/felipearocha/integrity-code-series-week9-cui) | CUI thermohygro-electrochemical (3 PDEs, Strang) |
| Week 10 | [integrity-code-series-week10-nnph-scc](https://github.com/felipearocha/integrity-code-series-week10-nnph-scc) | NNpHSCC full-physics (Chen-Sutherby-Xing + BS 7910) |
| **Week 11** | **[integrity-code-series-week11-erosion-corrosion-multiphase](https://github.com/felipearocha/integrity-code-series-week11-erosion-corrosion-multiphase)** | **Erosion-corrosion multiphase (NORSOK M-506 + DNV-RP-O501 + G119 + API 579) — this repo** |
