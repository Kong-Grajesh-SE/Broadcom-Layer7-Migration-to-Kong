"""Kong Gateway declarative configuration models."""

from typing import Any

from pydantic import BaseModel, Field


class KongPlugin(BaseModel):
    name: str
    service_name: str = ""
    route_name: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class KongRoute(BaseModel):
    name: str
    paths: list[str] = Field(default_factory=list)
    methods: list[str] | None = None
    strip_path: bool = True
    protocols: list[str] = Field(default_factory=lambda: ["https", "http"])
    tags: list[str] = Field(default_factory=list)


class KongService(BaseModel):
    name: str
    url: str = ""
    host: str = ""
    port: int = 443
    protocol: str = "https"
    path: str = ""
    connect_timeout: int = 30000
    read_timeout: int = 60000
    write_timeout: int = 60000
    retries: int = 5
    routes: list[KongRoute] = Field(default_factory=list)
    plugins: list[KongPlugin] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KongConsumer(BaseModel):
    username: str
    custom_id: str = ""
    tags: list[str] = Field(default_factory=list)
    credentials: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class KongUpstream(BaseModel):
    name: str
    targets: list[dict[str, Any]] = Field(default_factory=list)
    healthchecks: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class KongVault(BaseModel):
    """Kong Vaults entity - references a secret backend."""

    name: str
    prefix: str
    config: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class KongCertificate(BaseModel):
    """Kong Certificate entity for TLS/mTLS."""

    cert: str = ""
    key: str = ""
    cert_alt: str = ""
    key_alt: str = ""
    snis: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KongCACertificate(BaseModel):
    """Kong CA Certificate for mTLS trust chains."""

    cert: str = ""
    cert_digest: str = ""
    tags: list[str] = Field(default_factory=list)


class KongKey(BaseModel):
    """Kong Key entity (JWK) for JWT/JWE operations."""

    name: str
    kid: str = ""
    set_name: str = ""
    jwk: str = ""
    pem_private_key: str = ""
    pem_public_key: str = ""
    tags: list[str] = Field(default_factory=list)


class KongKeySet(BaseModel):
    """Kong Key Set - groups related keys."""

    name: str
    tags: list[str] = Field(default_factory=list)


class KongConfig(BaseModel):
    """Complete Kong declarative configuration output."""

    format_version: str = "3.0"
    services: list[KongService] = Field(default_factory=list)
    consumers: list[KongConsumer] = Field(default_factory=list)
    upstreams: list[KongUpstream] = Field(default_factory=list)
    plugins: list[KongPlugin] = Field(default_factory=list)
    vaults: list[KongVault] = Field(default_factory=list)
    certificates: list[KongCertificate] = Field(default_factory=list)
    ca_certificates: list[KongCACertificate] = Field(default_factory=list)
    keys: list[KongKey] = Field(default_factory=list)
    key_sets: list[KongKeySet] = Field(default_factory=list)
