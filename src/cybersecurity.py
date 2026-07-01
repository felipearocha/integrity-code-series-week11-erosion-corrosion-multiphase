"""
cybersecurity.py - Integrity-data audit chain + sensor validation for the
erosion-corrosion digital twin.

Threat model (data drives the corrosion/erosion decision, so it is in scope):
  - Sensor spoofing: falsified flow/temperature/pressure feeds inflate or hide
    the predicted wall-loss rate.
  - Data poisoning: corrupted MC training rows bias the surrogate.
  - Model tampering: silent edits to coefficients (NORSOK Kt, DNV K/n).
Mitigations implemented here:
  - SHA-256 hash chain over every record (tamper-evident audit log).
  - Physical-range sensor validation against NORSOK M-506 envelopes.
  - Coefficient fingerprint to detect tampering of the constants module.
"""
from __future__ import annotations

import hashlib
import json

from . import constants as C


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditChain:
    """Tamper-evident hash chain of model records."""

    def __init__(self, genesis: str = "ICS2-WEEK11-EC"):
        self.records = []
        self._prev = _hash(genesis)
        self.genesis = self._prev

    def append(self, record: dict) -> str:
        body = json.dumps(record, sort_keys=True, default=float)
        h = _hash(self._prev + body)
        self.records.append({"record": record, "prev": self._prev, "hash": h})
        self._prev = h
        return h

    def verify(self) -> bool:
        prev = self.genesis
        for entry in self.records:
            body = json.dumps(entry["record"], sort_keys=True, default=float)
            if entry["prev"] != prev:
                return False
            if entry["hash"] != _hash(prev + body):
                return False
            prev = entry["hash"]
        return True

    def to_json(self) -> str:
        return json.dumps({"genesis": self.genesis, "records": self.records},
                          indent=2, default=float)


def validate_sensor(name: str, value: float) -> tuple[bool, str]:
    """Validate a sensor reading against the NORSOK M-506 applicability envelope.
    [SOURCE: NORSOK M-506:2017 Tables 3-6]  T1
    """
    bounds = {
        "temp_c": (C.NORSOK_T_MIN, C.NORSOK_T_MAX),
        "ph": (C.NORSOK_PH_MIN, C.NORSOK_PH_MAX),
        "p_co2_bar": (C.NORSOK_FCO2_MIN, C.NORSOK_FCO2_MAX),
        "p_total_bar": (C.NORSOK_P_MIN, C.NORSOK_P_MAX),
        "u_sl": (0.0, C.NORSOK_VL_MAX),
        "u_sg": (0.0, C.NORSOK_VG_MAX),
    }
    if name not in bounds:
        return True, "no envelope defined"
    lo, hi = bounds[name]
    if value < lo or value > hi:
        return False, f"{name}={value} outside [{lo},{hi}] (possible spoofing)"
    return True, "ok"


def coefficient_fingerprint() -> str:
    """Fingerprint the load-bearing model coefficients to detect tampering."""
    payload = json.dumps({
        "NORSOK_KT": C.NORSOK_KT,
        "DNV_K_STEEL": C.DNV_K_STEEL,
        "DNV_N_STEEL": C.DNV_N_STEEL,
        "DNV_C1_BEND": C.DNV_C1_BEND,
        "BERGER_HAU": [C.BERGER_HAU_C, C.BERGER_HAU_RE_EXP, C.BERGER_HAU_SC_EXP],
        "API579_RSF": C.API579_RSF_ALLOWABLE,
    }, sort_keys=True)
    return _hash(payload)
