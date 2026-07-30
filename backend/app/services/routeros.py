import socket
import ssl
from collections.abc import Mapping
from typing import Any

import routeros
from routeros.errors import LoginError, RouterOSError

from app.models.mikrotik import DeviceSummary, MikroTikConnection


CONNECTION_TIMEOUT_SECONDS = 5.0


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


def _read_device_summary(client: Any) -> DeviceSummary:
    identity = _first_row(client.run("/system/identity/print"))
    resource = _first_row(client.run("/system/resource/print"))

    identity_name = identity.get("name")
    routeros_version = resource.get("version")

    if not identity_name or not routeros_version:
        raise MikroTikResponseError

    return DeviceSummary(
        identity=identity_name,
        model=resource.get("board-name"),
        routeros_version=routeros_version,
        architecture=resource.get("architecture-name"),
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

