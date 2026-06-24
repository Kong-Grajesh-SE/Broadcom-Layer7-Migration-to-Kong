"""Tests for vault/secrets mapper."""

import pytest

from layer7_kong_migration.generation.vaults import (
    VaultMapper,
    generate_env_manifest,
    generate_vault_reference_map,
    generate_vault_yaml,
)
from layer7_kong_migration.models.ir import PolicyBundle


@pytest.fixture
def mapper():
    return VaultMapper(vault_backend="env")


@pytest.fixture
def bundle_with_secrets():
    return PolicyBundle(
        name="test-bundle",
        cluster_properties={
            "env.backend.url": "http://backend:8080",
            "env.api.secret.key": "super-secret-123",
            "log.level": "INFO",
        },
        stored_passwords=["db-password", "ldap-bind-credential"],
        jdbc_connections=[
            {
                "Name": "OrdersDB",
                "JdbcUrl": "jdbc:mysql://db.internal:3306/orders",
                "DriverClass": "com.mysql.cj.jdbc.Driver",
                "UserName": "app_user",
                "Password": "db-secret",
            }
        ],
        certificates=[
            {
                "name": "backend-tls",
                "pem": "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----",
                "subjectCN": "api.backend.com",
            },
            {
                "name": "root-ca",
                "pem": "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----",
                "trustedForSigningServerCerts": "true",
            },
        ],
    )


def test_creates_env_vault(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    assert len(result["vaults"]) == 1
    vault = result["vaults"][0]
    assert vault.name == "env"
    assert vault.prefix == "layer7-migrated"
    assert vault.config["prefix"] == "L7_MIGRATED_"


def test_maps_cluster_properties(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    refs = result["vault_references"]
    assert "env.backend.url" in refs
    assert refs["env.backend.url"] == "{vault://layer7-migrated/ENV_BACKEND_URL}"
    assert "log.level" in refs


def test_secrets_redacted_in_env(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    env = result["env_manifest"]
    assert env["ENV_API_SECRET_KEY"] == "REPLACE-WITH-SECRET"
    assert env["ENV_BACKEND_URL"] == "http://backend:8080"
    assert env["LOG_LEVEL"] == "INFO"


def test_maps_stored_passwords(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    refs = result["vault_references"]
    assert "stored_password:db-password" in refs
    assert "REPLACE-WITH-SECRET" in result["env_manifest"]["SECRET_DB_PASSWORD"]


def test_maps_jdbc_connections(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    refs = result["vault_references"]
    assert "jdbc:OrdersDB:JdbcUrl" in refs
    assert "jdbc:OrdersDB:password" in refs
    assert "jdbc:OrdersDB:username" in refs
    env = result["env_manifest"]
    assert env["ORDERSDB_PASSWORD"] == "REPLACE-WITH-SECRET"
    assert env["ORDERSDB_USERNAME"] == "app_user"


def test_maps_certificates(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    assert len(result["certificates"]) == 1
    assert result["certificates"][0].snis == ["api.backend.com"]
    assert len(result["ca_certificates"]) == 1


def test_generate_vault_yaml(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    yaml_str = generate_vault_yaml(result)
    assert "layer7-migrated" in yaml_str
    assert "L7_MIGRATED_" in yaml_str
    assert "certificates" in yaml_str
    assert "ca_certificates" in yaml_str


def test_generate_env_manifest(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    env_str = generate_env_manifest(result)
    assert "L7_MIGRATED_ENV_BACKEND_URL=http://backend:8080" in env_str
    assert "L7_MIGRATED_ORDERSDB_PASSWORD=REPLACE-WITH-SECRET" in env_str


def test_generate_reference_map(mapper, bundle_with_secrets):
    result = mapper.map_bundle(bundle_with_secrets)
    ref_str = generate_vault_reference_map(result)
    assert "env.backend.url" in ref_str
    assert "{vault://layer7-migrated/" in ref_str


def test_aws_backend():
    m = VaultMapper(vault_backend="aws")
    bundle = PolicyBundle(name="t", cluster_properties={"k": "v"})
    result = m.map_bundle(bundle)
    assert result["vaults"][0].name == "aws"
    assert "region" in result["vaults"][0].config


def test_hcv_backend():
    m = VaultMapper(vault_backend="hcv")
    bundle = PolicyBundle(name="t", cluster_properties={"k": "v"})
    result = m.map_bundle(bundle)
    assert result["vaults"][0].name == "hcv"
    assert result["vaults"][0].config["kv"] == "v2"


def test_empty_bundle_no_vault(mapper):
    result = mapper.map_bundle(PolicyBundle(name="empty"))
    assert len(result["vaults"]) == 0
    assert len(result["vault_references"]) == 0
