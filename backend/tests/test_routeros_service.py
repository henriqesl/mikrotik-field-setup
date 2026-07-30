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
            "/system/package/print": [
                {"name": "routeros", "version": "7.20.8"},
                {"name": "wifi-qcom", "version": "7.20.8"},
            ],
            "/interface/wifi/print": [
                {
                    "name": "wifi1",
                    "default-name": "wifi1",
                    "mac-address": "AA:BB:CC:DD:EE:FF",
                    "disabled": "false",
                    "running": "true",
                }
            ],
        }
        command_rows = rows[command]

        if not isinstance(command_rows, list):
            command_rows = [command_rows]

        return SimpleNamespace(
            re=[SimpleNamespace(map=row) for row in command_rows],
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
    assert result.wifi_package == "wifi-qcom"
    assert result.wifi_stack == "wifi"
    assert result.wifi_interfaces[0].name == "wifi1"
    assert result.wifi_interfaces[0].running is True
    assert captured == {
        "address": "192.168.88.1:8728",
        "username": "orion",
        "password": "secret",
        "kwargs": {"timeout": service.CONNECTION_TIMEOUT_SECONDS},
    }
    assert fake_client.commands == [
        "/system/identity/print",
        "/system/resource/print",
        "/system/package/print",
        "/interface/wifi/print",
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


def test_discover_device_falls_back_to_legacy_wireless_menu(monkeypatch) -> None:
    class LegacyClient(FakeClient):
        def run(self, command: str):
            self.commands.append(command)

            if command == "/system/identity/print":
                rows = [{"name": "ORION-Legacy"}]
            elif command == "/system/resource/print":
                rows = [
                    {
                        "board-name": "LHG 5",
                        "version": "6.49.18",
                        "architecture-name": "mipsbe",
                    }
                ]
            elif command == "/system/package/print":
                rows = [{"name": "system"}, {"name": "wireless"}]
            elif command == "/interface/wireless/print":
                rows = [
                    {
                        "name": "wlan1",
                        "mac-address": "11:22:33:44:55:66",
                        "disabled": "false",
                        "running": "false",
                    }
                ]
            else:
                raise DeviceError(
                    SimpleNamespace(map={"message": "menu unavailable"})
                )

            return SimpleNamespace(
                re=[SimpleNamespace(map=row) for row in rows],
            )

    legacy_client = LegacyClient()
    monkeypatch.setattr(service.routeros, "dial", lambda *_args, **_kwargs: legacy_client)

    result = service.discover_device(
        MikroTikConnection(
            host="192.168.88.1",
            username="orion",
            password="secret",
        )
    )

    assert result.wifi_package == "wireless"
    assert result.wifi_stack == "wireless"
    assert result.wifi_interfaces[0].name == "wlan1"
    assert result.wifi_interfaces[0].running is False
