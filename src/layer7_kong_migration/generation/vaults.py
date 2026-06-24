"""Vault and secrets mapper for Layer 7 → Kong migration.

Maps Layer 7 configuration entities to Kong's native secret management:
  - Cluster properties  → Kong Vault references ({vault://env/...})
  - Stored passwords    → Kong Vault secrets
  - Certificates/keys   → Kong Certificates + Keys entities
  - JDBC credentials    → Kong Vault secrets (connection strings stay as config)
"""

import re
from typing import Any

from layer7_kong_migration.models.ir import PolicyBundle
from layer7_kong_migration.models.kong import (
    KongCACertificate,
    KongCertificate,
    KongKey,
    KongKeySet,
    KongVault,
)

SECRET_PATTERNS = re.compile(
    r"(password|secret|token|api[_-]?key|private[_-]?key|credential|auth)",
    re.IGNORECASE,
)

JDBC_SECRET_KEYS = {"Password", "password"}


class VaultMapper:
    def __init__(self, vault_backend: str = "env") -> None:
        self.vault_backend = vault_backend

    def map_bundle(self, bundle: PolicyBundle) -> dict[str, Any]:
        result: dict[str, Any] = {
            "vaults": [],
            "vault_references": {},
            "env_manifest": {},
            "certificates": [],
            "ca_certificates": [],
            "keys": [],
            "key_sets": [],
        }

        if bundle.cluster_properties or bundle.stored_passwords or bundle.jdbc_connections:
            vault = self._create_vault()
            result["vaults"].append(vault)

        refs, env = self._map_cluster_properties(bundle.cluster_properties)
        result["vault_references"].update(refs)
        result["env_manifest"].update(env)

        pw_refs, pw_env = self._map_stored_passwords(bundle.stored_passwords)
        result["vault_references"].update(pw_refs)
        result["env_manifest"].update(pw_env)

        jdbc_refs, jdbc_env = self._map_jdbc_connections(bundle.jdbc_connections)
        result["vault_references"].update(jdbc_refs)
        result["env_manifest"].update(jdbc_env)

        certs, ca_certs = self._map_certificates(bundle.certificates)
        result["certificates"] = certs
        result["ca_certificates"] = ca_certs

        keys, key_sets = self._map_keys_from_assertions(bundle)
        result["keys"] = keys
        result["key_sets"] = key_sets

        return result

    def _create_vault(self) -> KongVault:
        if self.vault_backend == "env":
            return KongVault(
                name="env",
                prefix="layer7-migrated",
                config={"prefix": "L7_MIGRATED_"},
                description="Environment variable vault for migrated Layer 7 cluster properties and secrets",
                tags=["migrated-from-layer7"],
            )
        if self.vault_backend == "aws":
            return KongVault(
                name="aws",
                prefix="layer7-migrated",
                config={"region": "REPLACE-WITH-REGION"},
                description="AWS Secrets Manager vault for migrated Layer 7 secrets",
                tags=["migrated-from-layer7"],
            )
        if self.vault_backend == "hcv":
            return KongVault(
                name="hcv",
                prefix="layer7-migrated",
                config={
                    "protocol": "https",
                    "host": "REPLACE-WITH-VAULT-HOST",
                    "port": 8200,
                    "mount": "secret",
                    "kv": "v2",
                },
                description="HashiCorp Vault for migrated Layer 7 secrets",
                tags=["migrated-from-layer7"],
            )
        if self.vault_backend == "gcp":
            return KongVault(
                name="gcp",
                prefix="layer7-migrated",
                config={"project_id": "REPLACE-WITH-PROJECT-ID"},
                description="GCP Secret Manager vault for migrated Layer 7 secrets",
                tags=["migrated-from-layer7"],
            )
        return KongVault(
            name="env",
            prefix="layer7-migrated",
            config={"prefix": "L7_MIGRATED_"},
            tags=["migrated-from-layer7"],
        )

    def _map_cluster_properties(
        self, props: dict[str, str]
    ) -> tuple[dict[str, str], dict[str, str]]:
        refs: dict[str, str] = {}
        env: dict[str, str] = {}

        for name, value in props.items():
            env_key = _to_env_key(name)
            vault_ref = f"{{vault://layer7-migrated/{env_key}}}"
            refs[name] = vault_ref

            if SECRET_PATTERNS.search(name):
                env[env_key] = "REPLACE-WITH-SECRET"
            else:
                env[env_key] = value

        return refs, env

    def _map_stored_passwords(
        self, passwords: list[str]
    ) -> tuple[dict[str, str], dict[str, str]]:
        refs: dict[str, str] = {}
        env: dict[str, str] = {}

        for pw_name in passwords:
            env_key = _to_env_key(f"secret_{pw_name}")
            vault_ref = f"{{vault://layer7-migrated/{env_key}}}"
            refs[f"stored_password:{pw_name}"] = vault_ref
            env[env_key] = "REPLACE-WITH-SECRET"

        return refs, env

    def _map_jdbc_connections(
        self, connections: list[dict[str, Any]]
    ) -> tuple[dict[str, str], dict[str, str]]:
        refs: dict[str, str] = {}
        env: dict[str, str] = {}

        for conn in connections:
            conn_name = conn.get("Name", conn.get("name", "unnamed"))
            slug = _to_env_key(conn_name)

            for key in ("JdbcUrl", "jdbcUrl", "DriverClass", "driverClass"):
                val = conn.get(key, "")
                if val:
                    env_key = f"{slug}_{_to_env_key(key)}"
                    refs[f"jdbc:{conn_name}:{key}"] = f"{{vault://layer7-migrated/{env_key}}}"
                    env[env_key] = val

            for key in JDBC_SECRET_KEYS:
                if key in conn:
                    env_key = f"{slug}_PASSWORD"
                    refs[f"jdbc:{conn_name}:password"] = f"{{vault://layer7-migrated/{env_key}}}"
                    env[env_key] = "REPLACE-WITH-SECRET"

            user = conn.get("UserName", conn.get("userName", conn.get("user", "")))
            if user:
                env_key = f"{slug}_USERNAME"
                refs[f"jdbc:{conn_name}:username"] = f"{{vault://layer7-migrated/{env_key}}}"
                env[env_key] = user

        return refs, env

    def _map_certificates(
        self, certs: list[dict[str, str]]
    ) -> tuple[list[KongCertificate], list[KongCACertificate]]:
        kong_certs: list[KongCertificate] = []
        ca_certs: list[KongCACertificate] = []

        for cert_data in certs:
            name = cert_data.get("name", cert_data.get("alias", ""))
            pem = cert_data.get("pem", cert_data.get("encoded", ""))
            is_ca = cert_data.get("trustedForSigningServerCerts", "") == "true" or \
                    cert_data.get("trustedForSigningClientCerts", "") == "true" or \
                    cert_data.get("trustAnchor", "") == "true"

            if is_ca:
                ca_certs.append(KongCACertificate(
                    cert=pem or f"# Paste CA certificate '{name}' PEM here",
                    tags=["migrated-from-layer7", name],
                ))
            else:
                snis = []
                subject_cn = cert_data.get("subjectCN", cert_data.get("subject_cn", ""))
                if subject_cn:
                    snis.append(subject_cn)

                kong_certs.append(KongCertificate(
                    cert=pem or f"# Paste certificate '{name}' PEM here",
                    key=f"# Paste private key for '{name}' PEM here",
                    snis=snis,
                    tags=["migrated-from-layer7", name],
                ))

        return kong_certs, ca_certs

    def _map_keys_from_assertions(
        self, bundle: PolicyBundle
    ) -> tuple[list[KongKey], list[KongKeySet]]:
        keys: list[KongKey] = []
        key_sets: list[KongKeySet] = []
        seen_sets: set[str] = set()

        for svc in bundle.services + bundle.shared_policies:
            for a in svc.assertions:
                if a.assertion_type in ("DecodeJsonWebToken", "EncodeJsonWebToken"):
                    kid = a.configuration.get("key_id", "")
                    source = a.configuration.get("source_variable", "")
                    set_name = f"layer7-jwt-{_to_env_key(svc.name)}"

                    if set_name not in seen_sets:
                        key_sets.append(KongKeySet(
                            name=set_name,
                            tags=["migrated-from-layer7"],
                        ))
                        seen_sets.add(set_name)

                    key_name = f"jwt-key-{_to_env_key(svc.name)}-{kid or 'default'}"
                    keys.append(KongKey(
                        name=key_name,
                        kid=kid or "REPLACE-WITH-KEY-ID",
                        set_name=set_name,
                        jwk="# Paste JWK here or use vault reference: {vault://layer7-migrated/" + _to_env_key(f"jwt_key_{svc.name}") + "}",
                        tags=["migrated-from-layer7"],
                    ))

        return keys, key_sets


def generate_vault_yaml(vault_result: dict[str, Any]) -> str:
    """Generate Kong declarative YAML fragment for vault entities."""
    from io import StringIO
    from ruamel.yaml import YAML

    y = YAML()
    y.default_flow_style = False

    output: dict[str, Any] = {}

    if vault_result["vaults"]:
        output["vaults"] = []
        for v in vault_result["vaults"]:
            vd: dict[str, Any] = {
                "name": v.name,
                "prefix": v.prefix,
                "config": v.config,
                "description": v.description,
                "tags": v.tags,
            }
            output["vaults"].append(vd)

    if vault_result["certificates"]:
        output["certificates"] = []
        for c in vault_result["certificates"]:
            cd: dict[str, Any] = {"cert": c.cert, "key": c.key, "tags": c.tags}
            if c.snis:
                cd["snis"] = [{"name": s} for s in c.snis]
            output["certificates"].append(cd)

    if vault_result["ca_certificates"]:
        output["ca_certificates"] = [
            {"cert": ca.cert, "tags": ca.tags}
            for ca in vault_result["ca_certificates"]
        ]

    if vault_result["key_sets"]:
        output["key_sets"] = [
            {"name": ks.name, "tags": ks.tags}
            for ks in vault_result["key_sets"]
        ]

    if vault_result["keys"]:
        output["keys"] = []
        for k in vault_result["keys"]:
            kd: dict[str, Any] = {
                "name": k.name,
                "kid": k.kid,
                "set": {"name": k.set_name},
                "tags": k.tags,
            }
            if k.jwk:
                kd["jwk"] = k.jwk
            output["keys"].append(kd)

    buf = StringIO()
    y.dump(output, buf)
    return buf.getvalue()


def generate_env_manifest(vault_result: dict[str, Any]) -> str:
    """Generate a .env template file for the vault environment variables."""
    lines = [
        "# Kong Vault Environment Variables",
        "# Migrated from Layer 7 Gateway cluster properties and secrets",
        "# Backend: env vault with prefix L7_MIGRATED_",
        "#",
        "# IMPORTANT: Replace all REPLACE-WITH-SECRET values before deploying.",
        "",
    ]

    env = vault_result.get("env_manifest", {})
    secrets = {k: v for k, v in env.items() if v == "REPLACE-WITH-SECRET"}
    config = {k: v for k, v in env.items() if v != "REPLACE-WITH-SECRET"}

    if config:
        lines.append("# --- Cluster Properties (non-secret) ---")
        for k in sorted(config):
            lines.append(f"L7_MIGRATED_{k}={config[k]}")
        lines.append("")

    if secrets:
        lines.append("# --- Secrets (must be replaced) ---")
        for k in sorted(secrets):
            lines.append(f"L7_MIGRATED_{k}=REPLACE-WITH-SECRET")
        lines.append("")

    return "\n".join(lines) + "\n"


def generate_vault_reference_map(vault_result: dict[str, Any]) -> str:
    """Generate a reference map showing Layer 7 name → Kong vault reference."""
    lines = [
        "# Layer 7 → Kong Vault Reference Map",
        "# Use these vault references in Kong plugin configurations",
        "# instead of hardcoded values.",
        "",
    ]

    refs = vault_result.get("vault_references", {})
    for l7_name in sorted(refs):
        lines.append(f"# {l7_name}")
        lines.append(f"#   → {refs[l7_name]}")
        lines.append("")

    return "\n".join(lines) + "\n"


def _to_env_key(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").upper()
    return slug or "UNNAMED"
