"""Cybersecurity: audit chain, sensor validation, coefficient fingerprint."""
import pytest
from src import cybersecurity as cyber
from src import constants as C


def test_chain_verify_clean():
    ch = cyber.AuditChain()
    for i in range(10):
        ch.append({"i": i, "cr": i * 0.5})
    assert ch.verify()


def test_chain_detects_tamper():
    ch = cyber.AuditChain()
    for i in range(5):
        ch.append({"i": i})
    ch.records[2]["record"]["i"] = 999  # tamper
    assert not ch.verify()


def test_chain_detects_hash_edit():
    ch = cyber.AuditChain()
    ch.append({"a": 1})
    ch.append({"a": 2})
    ch.records[1]["hash"] = "deadbeef"
    assert not ch.verify()


def test_chain_length():
    ch = cyber.AuditChain()
    for i in range(7):
        ch.append({"i": i})
    assert len(ch.records) == 7


def test_chain_json_roundtrip():
    ch = cyber.AuditChain()
    ch.append({"x": 1.5})
    js = ch.to_json()
    assert "genesis" in js and "records" in js


@pytest.mark.parametrize("name,val,ok", [
    ("temp_c", 60, True), ("temp_c", 200, False),
    ("ph", 5.0, True), ("ph", 8.0, False),
    ("p_co2_bar", 2.0, True), ("p_co2_bar", 50, False),
    ("u_sl", 10, True), ("u_sl", 30, False),
    ("u_sg", 20, True), ("u_sg", 60, False),
    ("p_total_bar", 100, True), ("p_total_bar", 2000, False)])
def test_sensor_validation(name, val, ok):
    valid, _ = cyber.validate_sensor(name, val)
    assert valid is ok


def test_sensor_unknown_passes():
    valid, _ = cyber.validate_sensor("unknown_tag", 999)
    assert valid


def test_fingerprint_stable():
    a = cyber.coefficient_fingerprint()
    b = cyber.coefficient_fingerprint()
    assert a == b


def test_fingerprint_is_sha256():
    fp = cyber.coefficient_fingerprint()
    assert len(fp) == 64
    int(fp, 16)  # valid hex


def test_fingerprint_changes_on_tamper(monkeypatch):
    original = cyber.coefficient_fingerprint()
    monkeypatch.setitem(C.NORSOK_KT, 60, 99.9)
    tampered = cyber.coefficient_fingerprint()
    assert original != tampered


@pytest.mark.parametrize("temp", [5, 20, 60, 90, 150])
def test_sensor_temp_envelope(temp):
    valid, _ = cyber.validate_sensor("temp_c", temp)
    assert valid


@pytest.mark.parametrize("temp", [-10, 4, 151, 300])
def test_sensor_temp_out_of_envelope(temp):
    valid, _ = cyber.validate_sensor("temp_c", temp)
    assert not valid
