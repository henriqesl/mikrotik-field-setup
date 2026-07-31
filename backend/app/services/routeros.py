import re
import socket
import ssl
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

import routeros
from routeros.errors import DeviceError, LoginError, RouterOSError

from app.models.mikrotik import (
    DeviceSummary,
    MikroTikConnection,
    PingRequest,
    PingResult,
    WiFiInterface,
    WiFiPeer,
)


CONNECTION_TIMEOUT_SECONDS = 5.0
WIFI_PACKAGES = ("wifi-qcom", "wifi-qcom-ac", "wifiwave2", "wireless")
WIFI_MENUS = {
    "wifi": "/interface/wifi/print",
    "wifiwave2": "/interface/wifiwave2/print",
    "wireless": "/interface/wireless/print",
}
REGISTRATION_MENUS = {
    "wifi": "/interface/wifi/registration-table/print",
    "wifiwave2": "/interface/wifiwave2/registration-table/print",
    "wireless": "/interface/wireless/registration-table/print",
}
TIME_FACTORS_MS = {
    "d": 86_400_000,
    "h": 3_600_000,
    "m": 60_000,
    "s": 1_000,
    "ms": 1,
    "us": 0.001,
    "ns": 0.000001,
}
ResultType = TypeVar("ResultType")


class MikroTikError(Exception):
    """Base error for friendly RouterOS error translation."""


class MikroTikAuthenticationError(MikroTikError):
    """The device rejected the supplied credentials."""


class MikroTikTimeoutError(MikroTikError):
    """The device did not respond within the configured timeout."""


class MikroTikTLSVerificationError(MikroTikError):
    """The TLS certificate could not be verified."""


class MikroTikConnectionError(MikroTikError):
    """The device could not be reached through the RouterOS API."""


class MikroTikResponseError(MikroTikError):
    """The device response did not contain the expected fields."""


def _create_tls_context(verify_tls: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()

    if not verify_tls:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    return context


def _first_row(reply: Any) -> Mapping[str, str]:
    if not reply.re:
        raise MikroTikResponseError

    return reply.re[0].map


def _rows(reply: Any) -> list[Mapping[str, str]]:
    return [sentence.map for sentence in reply.re]


def _optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None

    return value.lower() in {"true", "yes"}


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def _signal_dbm(value: str | None) -> int | None:
    if value is None:
        return None

    match = re.search(r"-?\d+", value)
    return int(match.group()) if match else None


def _duration_ms(value: str | None) -> float | None:
    if not value:
        return None

    normalized = value.strip().lower().replace("µs", "us")
    matches = list(
        re.finditer(
            r"(\d+(?:\.\d+)?)(ms|us|ns|d|h|m|s)",
            normalized,
        )
    )

    if not matches or "".join(match.group(0) for match in matches) != normalized:
        return None

    milliseconds = sum(
        float(match.group(1)) * TIME_FACTORS_MS[match.group(2)]
        for match in matches
    )
    return round(milliseconds, 3)


def _packet_loss(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        return float(value.rstrip("%"))
    except ValueError:
        return None


def _active_wifi_package(client: Any) -> str | None:
    try:
        packages = _rows(client.run("/system/package/print"))
    except DeviceError:
        return None

    active_names = {
        package.get("name")
        for package in packages
        if not _optional_bool(package.get("disabled"))
        and not _optional_bool(package.get("available"))
    }

    return next((name for name in WIFI_PACKAGES if name in active_names), None)


def _menu_order(package: str | None) -> list[str]:
    preferred_stack = {
        "wifi-qcom": "wifi",
        "wifi-qcom-ac": "wifi",
        "wifiwave2": "wifiwave2",
        "wireless": "wireless",
    }.get(package)
    stacks = ["wifi", "wireless", "wifiwave2"]

    if preferred_stack:
        stacks.remove(preferred_stack)
        stacks.insert(0, preferred_stack)

    return stacks


def _read_wifi(client: Any) -> tuple[str | None, str, list[WiFiInterface]]:
    package = _active_wifi_package(client)

    for stack in _menu_order(package):
        try:
            rows = _rows(client.run(WIFI_MENUS[stack]))
        except DeviceError:
            continue

        interfaces = [
            WiFiInterface(
                name=row.get("name") or row.get("default-name"),
                default_name=row.get("default-name"),
                mac_address=row.get("mac-address"),
                disabled=_optional_bool(row.get("disabled")),
                running=_optional_bool(row.get("running")),
            )
            for row in rows
        ]
        return package, stack, interfaces

    return package, "not_detected", []


def _read_registration_table(
    client: Any,
    stack: str,
) -> tuple[bool, list[WiFiPeer]]:
    command = REGISTRATION_MENUS.get(stack)

    if not command:
        return False, []

    try:
        rows = _rows(client.run(command))
    except DeviceError:
        return False, []

    peers = []

    for row in rows:
        signal = row.get("signal") or row.get("signal-strength")
        peers.append(
            WiFiPeer(
                interface=row.get("interface"),
                mac_address=row.get("mac-address"),
                radio_name=row.get("radio-name"),
                ssid=row.get("ssid"),
                authorized=_optional_bool(row.get("authorized")),
                signal=signal,
                signal_dbm=_signal_dbm(signal),
                tx_rate=row.get("tx-rate"),
                rx_rate=row.get("rx-rate"),
                tx_bits_per_second=_optional_int(row.get("tx-bits-per-second")),
                rx_bits_per_second=_optional_int(row.get("rx-bits-per-second")),
                uptime=row.get("uptime"),
                last_activity=row.get("last-activity"),
                band=row.get("band"),
            )
        )

    return True, peers


def _read_device_summary(client: Any) -> DeviceSummary:
    identity = _first_row(client.run("/system/identity/print"))
    resource = _first_row(client.run("/system/resource/print"))
    wifi_package, wifi_stack, wifi_interfaces = _read_wifi(client)
    registration_table_available, wifi_peers = _read_registration_table(
        client,
        wifi_stack,
    )

    identity_name = identity.get("name")
    routeros_version = resource.get("version")

    if not identity_name or not routeros_version:
        raise MikroTikResponseError

    return DeviceSummary(
        identity=identity_name,
        model=resource.get("board-name"),
        routeros_version=routeros_version,
        architecture=resource.get("architecture-name"),
        wifi_package=wifi_package,
        wifi_stack=wifi_stack,
        wifi_interfaces=wifi_interfaces,
        registration_table_available=registration_table_available,
        wifi_peers=wifi_peers,
    )


def _open_client(connection: MikroTikConnection) -> Any:
    address = f"{connection.host}:{connection.port}"
    password = connection.password.get_secret_value()

    if connection.use_tls:
        return routeros.dial_tls(
            address,
            connection.username,
            password,
            timeout=CONNECTION_TIMEOUT_SECONDS,
            tls_context=_create_tls_context(connection.verify_tls),
        )

    return routeros.dial(
        address,
        connection.username,
        password,
        timeout=CONNECTION_TIMEOUT_SECONDS,
    )


def _with_connection(
    connection: MikroTikConnection,
    operation: Callable[[Any], ResultType],
) -> ResultType:
    try:
        client = _open_client(connection)
        with client:
            return operation(client)
    except MikroTikResponseError:
        raise
    except LoginError as error:
        raise MikroTikAuthenticationError from error
    except ssl.SSLCertVerificationError as error:
        raise MikroTikTLSVerificationError from error
    except (TimeoutError, socket.timeout) as error:
        raise MikroTikTimeoutError from error
    except RouterOSError as error:
        raise MikroTikResponseError from error
    except OSError as error:
        raise MikroTikConnectionError from error


def discover_device(connection: MikroTikConnection) -> DeviceSummary:
    """Open one short-lived API session and read RouterOS device information."""
    return _with_connection(connection, _read_device_summary)


def _read_ping_result(client: Any, request: PingRequest) -> PingResult:
    rows = _rows(
        client.run(
            "/ping",
            f"=address={request.target}",
            f"=count={request.count}",
            "=interval=200ms",
        )
    )
    samples = [
        latency
        for latency in (_duration_ms(row.get("time")) for row in rows)
        if latency is not None
    ]
    summary = next(
        (
            row
            for row in reversed(rows)
            if row.get("sent") is not None and row.get("received") is not None
        ),
        None,
    )

    if summary:
        sent = _optional_int(summary.get("sent"))
        received = _optional_int(summary.get("received"))
        packet_loss = _packet_loss(summary.get("packet-loss"))

        if sent is not None and received is not None and packet_loss is not None:
            return PingResult(
                target=request.target,
                sent=sent,
                received=received,
                packet_loss_percent=packet_loss,
                minimum_latency_ms=_duration_ms(summary.get("min-rtt")),
                average_latency_ms=_duration_ms(summary.get("avg-rtt")),
                maximum_latency_ms=_duration_ms(summary.get("max-rtt")),
                samples_ms=samples,
                measurement_source="routeros_summary",
            )

    sent = request.count
    received = len(samples)
    packet_loss = ((sent - received) / sent) * 100

    return PingResult(
        target=request.target,
        sent=sent,
        received=received,
        packet_loss_percent=round(packet_loss, 2),
        minimum_latency_ms=min(samples) if samples else None,
        average_latency_ms=(
            round(sum(samples) / received, 3) if received else None
        ),
        maximum_latency_ms=max(samples) if samples else None,
        samples_ms=samples,
        measurement_source="orion_calculation",
    )


def ping_device(request: PingRequest) -> PingResult:
    """Run a bounded ICMP test from the MikroTik itself."""
    return _with_connection(
        request.connection,
        lambda client: _read_ping_result(client, request),
    )
