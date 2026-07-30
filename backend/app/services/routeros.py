import socket
import ssl
from collections.abc import Mapping
from typing import Any

import routeros
from routeros.errors import DeviceError, LoginError, RouterOSError

from app.models.mikrotik import DeviceSummary, MikroTikConnection, WiFiInterface


CONNECTION_TIMEOUT_SECONDS = 5.0
WIFI_PACKAGES = ("wifi-qcom", "wifi-qcom-ac", "wifiwave2", "wireless")
WIFI_MENUS = {
    "wifi": "/interface/wifi/print",
    "wifiwave2": "/interface/wifiwave2/print",
    "wireless": "/interface/wireless/print",
}


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


def _read_device_summary(client: Any) -> DeviceSummary:
    identity = _first_row(client.run("/system/identity/print"))
    resource = _first_row(client.run("/system/resource/print"))
    wifi_package, wifi_stack, wifi_interfaces = _read_wifi(client)

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
    )


def discover_device(connection: MikroTikConnection) -> DeviceSummary:
    """Open one short-lived API session and read basic RouterOS information."""
    address = f"{connection.host}:{connection.port}"
    password = connection.password.get_secret_value()

    try:
        if connection.use_tls:
            client = routeros.dial_tls(
                address,
                connection.username,
                password,
                timeout=CONNECTION_TIMEOUT_SECONDS,
                tls_context=_create_tls_context(connection.verify_tls),
            )
        else:
            client = routeros.dial(
                address,
                connection.username,
                password,
                timeout=CONNECTION_TIMEOUT_SECONDS,
            )

        with client:
            return _read_device_summary(client)
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
