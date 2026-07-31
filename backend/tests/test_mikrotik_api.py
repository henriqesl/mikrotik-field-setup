from fastapi.testclient import TestClient

from app.api import mikrotik
from app.main import app
from app.models.mikrotik import DeviceSummary, PingResult
from app.services.routeros import (
    MikroTikAuthenticationError,
    MikroTikConnectionError,
    MikroTikTimeoutError,
)


client = TestClient(app)

VALID_CONNECTION = {
    "host": "192.168.88.1",
    "username": "orion",
    "password": "field-secret",
    "port": 8728,
    "use_tls": False,
    "verify_tls": True,
}


def test_discover_mikrotik_returns_normalized_device(monkeypatch) -> None:
    def fake_discover(_connection):
        return DeviceSummary(
            identity="Radio-Torre",
            model="LHG 5 ax",
            routeros_version="7.20.8",
            architecture="arm64",
            wifi_package="wifi-qcom",
            wifi_stack="wifi",
            wifi_interfaces=[
                {
                    "name": "wifi1",
                    "default_name": "wifi1",
                    "mac_address": "AA:BB:CC:DD:EE:FF",
                    "disabled": False,
                    "running": True,
                }
            ],
            registration_table_available=True,
            wifi_peers=[
                {
                    "interface": "wifi1",
                    "mac_address": "11:22:33:44:55:66",
                    "radio_name": None,
                    "ssid": "ORION-Link",
                    "authorized": True,
                    "signal": "-72",
                    "signal_dbm": -72,
                    "tx_rate": "144.1Mbps",
                    "rx_rate": "120.1Mbps",
                    "tx_bits_per_second": 12000000,
                    "rx_bits_per_second": 9000000,
                    "uptime": "6h24m21s",
                    "last_activity": "10ms",
                    "band": "5ghz-ax",
                }
            ],
        )

    monkeypatch.setattr(mikrotik, "discover_device", fake_discover)

    response = client.post("/api/mikrotik/discover", json=VALID_CONNECTION)

    assert response.status_code == 200
    assert response.json() == {
        "identity": "Radio-Torre",
        "model": "LHG 5 ax",
        "routeros_version": "7.20.8",
        "architecture": "arm64",
        "wifi_package": "wifi-qcom",
        "wifi_stack": "wifi",
        "wifi_interfaces": [
            {
                "name": "wifi1",
                "default_name": "wifi1",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "disabled": False,
                "running": True,
            }
        ],
        "registration_table_available": True,
        "wifi_peers": [
            {
                "interface": "wifi1",
                "mac_address": "11:22:33:44:55:66",
                "radio_name": None,
                "ssid": "ORION-Link",
                "authorized": True,
                "signal": "-72",
                "signal_dbm": -72,
                "tx_rate": "144.1Mbps",
                "rx_rate": "120.1Mbps",
                "tx_bits_per_second": 12000000,
                "rx_bits_per_second": 9000000,
                "uptime": "6h24m21s",
                "last_activity": "10ms",
                "band": "5ghz-ax",
            }
        ],
    }
    assert "field-secret" not in response.text


def test_discover_mikrotik_translates_authentication_error(monkeypatch) -> None:
    def fake_discover(_connection):
        raise MikroTikAuthenticationError

    monkeypatch.setattr(mikrotik, "discover_device", fake_discover)

    response = client.post("/api/mikrotik/discover", json=VALID_CONNECTION)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Usuário ou senha não foram aceitos pelo MikroTik."
    }


def test_discover_mikrotik_translates_timeout(monkeypatch) -> None:
    def fake_discover(_connection):
        raise MikroTikTimeoutError

    monkeypatch.setattr(mikrotik, "discover_device", fake_discover)

    response = client.post("/api/mikrotik/discover", json=VALID_CONNECTION)

    assert response.status_code == 504


def test_discover_mikrotik_translates_connection_error(monkeypatch) -> None:
    def fake_discover(_connection):
        raise MikroTikConnectionError

    monkeypatch.setattr(mikrotik, "discover_device", fake_discover)

    response = client.post("/api/mikrotik/discover", json=VALID_CONNECTION)

    assert response.status_code == 502


def test_discover_mikrotik_rejects_invalid_ip() -> None:
    invalid_connection = {**VALID_CONNECTION, "host": "mikrotik.local"}

    response = client.post("/api/mikrotik/discover", json=invalid_connection)

    assert response.status_code == 422


def test_ping_from_mikrotik_returns_normalized_metrics(monkeypatch) -> None:
    def fake_ping(_request):
        return PingResult(
            target="10.0.0.2",
            sent=5,
            received=4,
            packet_loss_percent=20,
            minimum_latency_ms=1.2,
            average_latency_ms=3.4,
            maximum_latency_ms=8.7,
            samples_ms=[1.2, 2.4, 3.3, 8.7],
            measurement_source="routeros_summary",
        )

    monkeypatch.setattr(mikrotik, "ping_device", fake_ping)

    response = client.post(
        "/api/mikrotik/ping",
        json={
            "connection": VALID_CONNECTION,
            "target": "10.0.0.2",
            "count": 5,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "target": "10.0.0.2",
        "sent": 5,
        "received": 4,
        "packet_loss_percent": 20.0,
        "minimum_latency_ms": 1.2,
        "average_latency_ms": 3.4,
        "maximum_latency_ms": 8.7,
        "samples_ms": [1.2, 2.4, 3.3, 8.7],
        "measurement_source": "routeros_summary",
    }
    assert "field-secret" not in response.text


def test_ping_from_mikrotik_rejects_invalid_target() -> None:
    response = client.post(
        "/api/mikrotik/ping",
        json={
            "connection": VALID_CONNECTION,
            "target": "internet.example",
        },
    )

    assert response.status_code == 422
