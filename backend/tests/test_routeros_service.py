from types import SimpleNamespace

import pytest
from routeros.errors import DeviceError

from app.models.mikrotik import MikroTikConnection, PingRequest
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
            "/interface/wifi/registration-table/print": [
                {
                    "interface": "wifi1",
                    "ssid": "ORION-Link",
                    "mac-address": "11:22:33:44:55:66",
                    "authorized": "true",
                    "signal": "-61",
                    "tx-rate": "144.1Mbps",
                    "rx-rate": "120.1Mbps",
                    "tx-bits-per-second": "12000000",
                    "rx-bits-per-second": "9000000",
                    "uptime": "1h20m",
                    "last-activity": "20ms",
                    "band": "5ghz-ax",
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
    assert result.registration_table_available is True
    assert result.wifi_peers[0].signal == "-61"
    assert result.wifi_peers[0].signal_dbm == -61
    assert result.wifi_peers[0].authorized is True
    assert result.wifi_peers[0].tx_bits_per_second == 12000000
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
        "/interface/wifi/registration-table/print",
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
            elif command == "/interface/wireless/registration-table/print":
                rows = [
                    {
                        "interface": "wlan1",
                        "mac-address": "AA:BB:CC:DD:EE:FF",
                        "radio-name": "AP-Torre",
                        "signal-strength": "-78dBm@6Mbps",
                        "tx-rate": "54Mbps",
                        "rx-rate": "48Mbps",
                        "uptime": "3h12m",
                        "last-activity": "30ms",
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
    assert result.registration_table_available is True
    assert result.wifi_peers[0].radio_name == "AP-Torre"
    assert result.wifi_peers[0].signal == "-78dBm@6Mbps"
    assert result.wifi_peers[0].signal_dbm == -78
    assert result.wifi_peers[0].authorized is None


@pytest.mark.parametrize(
    ("raw_signal", "expected"),
    [
        ("-61", -61),
        ("-78dBm@6Mbps", -78),
        (None, None),
        ("not-informed", None),
    ],
)
def test_signal_dbm_normalization(raw_signal, expected) -> None:
    assert service._signal_dbm(raw_signal) == expected


def test_registration_table_reports_unavailable_menu() -> None:
    class UnavailableClient:
        def run(self, _command: str):
            raise DeviceError(
                SimpleNamespace(map={"message": "menu unavailable"})
            )

    available, peers = service._read_registration_table(
        UnavailableClient(),
        "wifi",
    )

    assert available is False
    assert peers == []


@pytest.mark.parametrize(
    ("routeros_duration", "expected_ms"),
    [
        ("453us", 0.453),
        ("3ms200us", 3.2),
        ("1s20ms", 1020.0),
        ("0ms", 0.0),
        (None, None),
    ],
)
def test_routeros_duration_normalization(
    routeros_duration,
    expected_ms,
) -> None:
    assert service._duration_ms(routeros_duration) == expected_ms


def test_ping_device_uses_routeros_summary(monkeypatch) -> None:
    class PingClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def run(self, *words):
            assert words == (
                "/ping",
                "=address=10.0.0.2",
                "=count=5",
                "=interval=200ms",
            )
            rows = [
                {
                    "seq": "0",
                    "time": "1ms200us",
                    "sent": "1",
                    "received": "1",
                    "packet-loss": "0",
                    "min-rtt": "1ms200us",
                    "avg-rtt": "1ms200us",
                    "max-rtt": "1ms200us",
                },
                {
                    "seq": "1",
                    "time": "4ms",
                    "sent": "5",
                    "received": "4",
                    "packet-loss": "20",
                    "min-rtt": "1ms200us",
                    "avg-rtt": "2ms500us",
                    "max-rtt": "4ms",
                },
            ]
            return SimpleNamespace(
                re=[SimpleNamespace(map=row) for row in rows],
            )

    monkeypatch.setattr(
        service,
        "_open_client",
        lambda _connection: PingClient(),
    )
    request = PingRequest(
        connection=MikroTikConnection(
            host="192.168.88.1",
            username="orion",
            password="secret",
        ),
        target="10.0.0.2",
    )

    result = service.ping_device(request)

    assert result.sent == 5
    assert result.received == 4
    assert result.packet_loss_percent == 20
    assert result.minimum_latency_ms == 1.2
    assert result.average_latency_ms == 2.5
    assert result.maximum_latency_ms == 4
    assert result.samples_ms == [1.2, 4.0]
    assert result.measurement_source == "routeros_summary"


def test_ping_device_calculates_fallback_when_summary_is_missing(
    monkeypatch,
) -> None:
    class PingClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def run(self, *_words):
            return SimpleNamespace(
                re=[
                    SimpleNamespace(map={"time": "2ms"}),
                    SimpleNamespace(map={"status": "timeout"}),
                    SimpleNamespace(map={"time": "4ms"}),
                ]
            )

    monkeypatch.setattr(
        service,
        "_open_client",
        lambda _connection: PingClient(),
    )
    request = PingRequest(
        connection=MikroTikConnection(
            host="192.168.88.1",
            username="orion",
            password="secret",
        ),
        target="10.0.0.2",
        count=3,
    )

    result = service.ping_device(request)

    assert result.sent == 3
    assert result.received == 2
    assert result.packet_loss_percent == 33.33
    assert result.average_latency_ms == 3
    assert result.measurement_source == "orion_calculation"
