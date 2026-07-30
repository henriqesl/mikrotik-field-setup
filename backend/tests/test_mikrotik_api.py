from fastapi.testclient import TestClient

from app.api import mikrotik
from app.main import app
from app.models.mikrotik import DeviceSummary
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
