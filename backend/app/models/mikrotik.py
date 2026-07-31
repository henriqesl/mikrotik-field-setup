from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class MikroTikConnection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: IPv4Address
    username: str = Field(min_length=1, max_length=64)
    password: SecretStr
    port: int = Field(default=8728, ge=1, le=65535)
    use_tls: bool = False
    verify_tls: bool = True


class WiFiInterface(BaseModel):
    name: str | None
    default_name: str | None
    mac_address: str | None
    disabled: bool | None
    running: bool | None


class WiFiPeer(BaseModel):
    interface: str | None
    mac_address: str | None
    radio_name: str | None
    ssid: str | None
    authorized: bool | None
    signal: str | None
    signal_dbm: int | None
    tx_rate: str | None
    rx_rate: str | None
    tx_bits_per_second: int | None
    rx_bits_per_second: int | None
    uptime: str | None
    last_activity: str | None
    band: str | None


class DeviceSummary(BaseModel):
    identity: str
    model: str | None
    routeros_version: str
    architecture: str | None
    wifi_package: str | None
    wifi_stack: Literal["wifi", "wifiwave2", "wireless", "not_detected"]
    wifi_interfaces: list[WiFiInterface]
    registration_table_available: bool
    wifi_peers: list[WiFiPeer]


class PingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connection: MikroTikConnection
    target: IPv4Address
    count: int = Field(default=5, ge=1, le=10)


class PingResult(BaseModel):
    target: IPv4Address
    sent: int
    received: int
    packet_loss_percent: float
    minimum_latency_ms: float | None
    average_latency_ms: float | None
    maximum_latency_ms: float | None
    samples_ms: list[float]
    measurement_source: Literal["routeros_summary", "orion_calculation"]
