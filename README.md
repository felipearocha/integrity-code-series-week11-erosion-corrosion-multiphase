# Integrity Code Series — Week 11

## Coupled Erosion-Corrosion in Multiphase Oil & Gas Production Piping at Bends

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 466](https://img.shields.io/badge/tests-466%20passing-brightgreen.svg)]()

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

## Governing Models (every constant tagged to source)

### Erosion - DNV-RP-O501 Rev.4.2 (designated by NORSOK P-002 Clause 8.6.4)
- Bend rate (Eq.8.15-8.21): characteristic angle `alpha = atan(1/(2*sqrt(R/D)))`,
  `E = [K m_dot U^n F(alpha)/(rho_t A_t)] C1 C_unit`, `A_t = pi D^2/(4 sin alpha)`
  (angle dependence is F(alpha) and the 1/sin(alpha) in A_t - no extra sin term)
- Carbon steel: K = 2.0e-9, n = 2.6, C1 = 2.5 (Table 7-2)
- Angle function F(alpha): 8-term polynomial (Table 7-1)

### Corrosion - NORSOK M-506:2017 (Rev.3)
- `CR_t = K_t fCO2^0.62 (S/19)^(0.146+0.0324 log10 fCO2) f(pH)_t`  (Eq.1)
- 9-node Kt table (5-150 C); separate low-T equations at 5 C and 15 C
- Wall shear S from Eq.21-22; pH factor from Table 2

### Synergy - ASTM G119
- `T = E0 + C0 + dCw + dWc`; scale-removal fraction driven by wall shear + erosion

### Multiphase flow - Beggs-Brill (1973)
- Regime boundaries L1-L4; horizontal holdup E_L(0) = a C_L^b / Fr^c

### FFS - API 579-1 Part 5
- RSF, RSFa = 0.90, remaining life = (t_actual - t_min)/rate

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py                 # benchmarks + dataset + all visuals
python validation/benchmarks.py   # QC Gate 1 (11 hand-calcs)
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
tests/                  460 tests across 11 modules
assets/                 hero, 6 secondary PNGs, GIF, dataset, surrogate metrics
linkedin/post_draft.txt
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

## Anti-Hallucination Note

Every equation and constant carries an explicit `[SOURCE: ...]` tag with tier
(T1 standard/paper, T2 derived, T3 practitioner). The NORSOK M-506 model was
transcribed from the controlled 2017 (Rev.3) copy - not the older Rev.1 widely
posted online, which lacks the 5 C / 15 C nodes and the pH2S applicability limit.

## License

MIT - Felipe Rocha
