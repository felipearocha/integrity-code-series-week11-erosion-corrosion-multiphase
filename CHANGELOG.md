# Changelog

## [Unreleased]
- FIX (physics): DNV bend impact angle now follows Eq.8.15, alpha = atan(1/sqrt(2 R/D)):
  30.0 deg at R/D=1.5 (was 22.2 deg), bend erosion x1.37 at that geometry. The QC gate
  and tests had pinned the old form and now use the hand value.
- FIX (physics): Folias shell parameter uses the diameter, lambda = 1.285 L/sqrt(D t)
  (was the radius, which doubled the L^2 term of Mt^2).
- FIX (standards): t_min now uses ASME B31.3 para. 304.1.2 with the outside diameter
  (was a P*R/(S*E-0.6P) form labelled B31.3); remaining life cites API 570 Sec.7.2, not API 510.
- FIX (physics): elbow field scales corrosion with the NORSOK shear exponent
  0.146+0.0324 log10(fCO2) (was an untagged 0.3 described as the NORSOK term).

## v1.0.0 (2026-07-01) - audit remediation, included in the tagged release
- FIX (blocker): elbow wall-loss field is clamped to the pipe wall (12.7 mm);
  hero/GIF no longer show metal loss beyond the wall and report time-to-perforation.
- FIX (physics): removed a spurious extra sin(alpha) from the DNV bend erosion
  numerator (was underpredicting bend erosion by a factor sin(alpha) ~2.6x).
- FIX: Beggs-Brill transition holdup now uses the A-weighted interpolation
  (was a flat 0.5 blend); NORSOK Eq.22 friction uses the exact cube root.
- FIX: corrosion_rate clamps fCO2 to the NORSOK [0.1, 10] fugacity window.
- ADD: ffs_api579.rsf_part5() - true API 579 Part-5 Level-1 RSF with the Folias
  bulging factor Mt (the linear proxy is retained as a screening estimate).
- ADD: QC Gate bend-erosion magnitude and G119-decompose benchmarks (14/14).
- HONESTY: elbow shear profile relabelled as a prescribed fitted shape (not
  "reproduces the experiment"); G119 synergy constants and bare-steel proxy
  relabelled T3 heuristics; surrogate_metrics.json now reports raw mm/yr error
  alongside the log10 metric; README discloses the field is CO2-corrosion-dominated
  (erosion ~2%, synergy ~15%) and that holdup/MTC are diagnostics. 466 tests.

## Initial build (2026-06-08)
- Initial release: coupled erosion-corrosion of multiphase oil & gas piping at bends.
- Erosion engine: DNV-RP-O501 Rev.4.2 (designated by NORSOK P-002 Clause 8.6.4).
- Corrosion engine: NORSOK M-506:2017 (Rev.3), 9-node Kt table, shear-stress term.
- Synergy: ASTM G119 decomposition (E0 + C0 + dCw + dWc).
- Multiphase flow: Beggs-Brill (1973) regime + holdup.
- Hydrodynamics: NORSOK wall shear (Eq.21-22), Berger-Hau mass transfer, elbow
  peak-location profile (El-Gammal 2010 / Kim KAERI 2021).
- FFS: API 579-1 Part 5 RSF + remaining life.
- 12,000-row Monte Carlo dataset; GBR surrogate (R2 ~0.99 on log10 rate).
- Cybersecurity: SHA-256 audit chain, sensor envelope validation, coefficient fingerprint.
- 460 tests passing; QC Gates 1-3 all green.
