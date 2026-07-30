from types import SimpleNamespace

from app.models.mikrotik import MikroTikConnection
from app.services import routeros as service


class FakeClient:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def run(self, command: str):
        self.commands.append(command)

        rows = {
            "/system/identity/print": {"name": "ORION-Station"},
            "/system/resource/print": {
                "board-name": "SXTsq 5 ax",
                "version": "7.20.8 (stable)",
                "architecture-name": "arm64",
            },
        }
        return SimpleNamespace(
            re=[SimpleNamespace(map=rows[command])],
        )


def test_discover_device_uses_plain_api_and_maps_real_fields(monkeypatch) -> None:
    fake_client = FakeClient()
    captured: dict = {}

    def fake_dial(address, username, password, **kwargs):
        captured.update(
            address=address,
            username=username,
            password=password,
            kwargs=kwargs,
        )
        return fake_client

    monkeypatch.setattr(service.routeros, "dial", fake_dial)

    connection = MikroTikConnection(
        host="192.168.88.1",
        username="orion",
        password="secret",
    )
    result = service.discover_device(connection)

    assert result.identity == "ORION-Station"
    assert result.model == "SXTsq 5 ax"
    assert result.routeros_version == "7.20.8 (stable)"
    assert result.architecture == "arm64"
    assert captured == {
        "address": "192.168.88.1:8728",
        "username": "orion",
        "password": "secret",
        "kwargs": {"timeout": service.CONNECTION_TIMEOUT_SECONDS},
    }
    assert fake_client.commands == [
        "/system/identity/print",
        "/system/resource/print",
    ]


def test_discover_device_uses_tls_connector(monkeypatch) -> None:
    fake_client = FakeClient()
    captured: dict = {}

    def fake_dial_tls(address, username, password, **kwargs):
        captured.update(address=address, kwargs=kwargs)
        return fake_client

    monkeypatch.setattr(service.routeros, "dial_tls", fake_dial_tls)

    connection = MikroTikConnection(
        host="10.0.0.2",
        username="orion",
        password="secret",
        port=8729,
        use_tls=True,
        verify_tls=False,
    )
    service.discover_device(connection)

    assert captured["address"] == "10.0.0.2:8729"
    assert captured["kwargs"]["timeout"] == service.CONNECTION_TIMEOUT_SECONDS
    assert captured["kwargs"]["tls_context"].verify_mode == service.ssl.CERT_NONE

