from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class MikroTikConnection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: IPv4Address
    username: str = Field(min_length=1, max_length=64)
    password: SecretStr
    port: int = Field(default=8728, ge=1, le=65535)
    use_tls: bool = False
    verify_tls: bool = True


class DeviceSummary(BaseModel):
    identity: str
    model: str | None
    routeros_version: str
    architecture: str | None

