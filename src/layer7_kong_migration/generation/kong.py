"""Kong declarative YAML generator.

Converts the classified/analyzed PolicyBundle IR into Kong Gateway
declarative configuration (format version 3.0).
"""

import io
from typing import Any

from ruamel.yaml import YAML

from layer7_kong_migration.generation.plugins import generate_plugin, integrate_ai_results
from layer7_kong_migration.models.ir import AssertionConfig, Complexity, PolicyBundle, ServiceDefinition
from layer7_kong_migration.models.kong import KongConfig, KongConsumer, KongRoute, KongService

yaml = YAML()
yaml.default_flow_style = False


class KongGenerator:
    def __init__(self, vault_references: dict[str, str] | None = None) -> None:
        self.vault_references = vault_references or {}

    def generate(self, bundle: PolicyBundle) -> str:
        config = self._build_config(bundle)
        return self._to_yaml(config)

    def _build_config(self, bundle: PolicyBundle) -> KongConfig:
        config = KongConfig()

        for svc_def in bundle.services:
            kong_svc = self._generate_service(svc_def)
            if kong_svc:
                config.services.append(kong_svc)

        consumers = self._generate_consumers(bundle)
        config.consumers.extend(consumers)

        return config

    def _generate_service(self, svc_def: ServiceDefinition) -> KongService | None:
        if not svc_def.enabled:
            return None

        backend_url = ""
        for endpoint in svc_def.endpoints:
            if endpoint.url:
                backend_url = endpoint.url
                break

        if not backend_url:
            for assertion in svc_def.assertions:
                if assertion.assertion_type == "HttpRoutingAssertion":
                    backend_url = assertion.configuration.get("protected_service_url", "")
                    break

        svc_name = _slugify(svc_def.name)

        kong_svc = KongService(
            name=svc_name,
            url=self._resolve_vault_ref(backend_url) or "https://REPLACE-WITH-BACKEND-URL",
            tags=["migrated-from-layer7", svc_def.name],
        )

        if svc_def.endpoints:
            ep = svc_def.endpoints[0]
            kong_svc.connect_timeout = ep.connection_timeout_ms
            kong_svc.read_timeout = ep.read_timeout_ms

        route_path = svc_def.resolution_path or f"/{svc_name}"
        kong_svc.routes.append(KongRoute(
            name=f"{svc_name}-route",
            paths=[route_path],
            tags=["migrated-from-layer7"],
        ))

        for assertion in svc_def.assertions:
            plugins = self._generate_plugins_for_assertion(assertion, svc_name)
            kong_svc.plugins.extend(plugins)

        return kong_svc

    def _generate_plugins_for_assertion(
        self, assertion: AssertionConfig, service_name: str
    ) -> list[dict[str, Any]]:
        if assertion.complexity == Complexity.DIRECT:
            plugin = generate_plugin(assertion, service_name)
            if plugin:
                return [plugin]

        elif assertion.complexity == Complexity.CONDITIONAL:
            if assertion.kong_mapping:
                plugin = integrate_ai_results(assertion, service_name)
                if plugin:
                    return [plugin]
            else:
                plugin = generate_plugin(assertion, service_name)
                if plugin:
                    return [plugin]

        elif assertion.complexity == Complexity.CUSTOM:
            if assertion.kong_mapping:
                plugin = integrate_ai_results(assertion, service_name)
                if plugin:
                    return [plugin]

        return []

    def _generate_consumers(self, bundle: PolicyBundle) -> list[KongConsumer]:
        consumers = []
        has_basic_auth = False
        has_key_auth = False

        for svc in bundle.services:
            for assertion in svc.assertions:
                if assertion.assertion_type in ("HttpBasic", "Authentication"):
                    has_basic_auth = True
                elif assertion.assertion_type == "LookupApiKey":
                    has_key_auth = True

        if has_basic_auth or has_key_auth:
            consumer = KongConsumer(
                username=f"{_slugify(bundle.name)}-test-consumer",
                custom_id=f"migration-{_slugify(bundle.name)}-001",
                tags=["placeholder", "migrated-from-layer7", "replace-with-real-credentials"],
            )
            if has_basic_auth:
                consumer.credentials["basicauth_credentials"] = [{
                    "username": "test-user",
                    "password": "REPLACE-WITH-REAL-PASSWORD",
                    "tags": ["placeholder"],
                }]
            if has_key_auth:
                consumer.credentials["keyauth_credentials"] = [{
                    "key": "test-api-key-REPLACE-ME",
                    "tags": ["placeholder"],
                }]
            consumers.append(consumer)

        return consumers

    def _to_yaml(self, config: KongConfig) -> str:
        output: dict[str, Any] = {"_format_version": config.format_version}

        if config.services:
            output["services"] = []
            for svc in config.services:
                svc_dict: dict[str, Any] = {
                    "name": svc.name,
                    "url": svc.url,
                    "connect_timeout": svc.connect_timeout,
                    "read_timeout": svc.read_timeout,
                    "write_timeout": svc.write_timeout,
                    "retries": svc.retries,
                    "tags": svc.tags,
                }
                if svc.routes:
                    svc_dict["routes"] = [
                        {
                            "name": r.name,
                            "paths": r.paths,
                            "strip_path": r.strip_path,
                            "protocols": r.protocols,
                            "tags": r.tags,
                        }
                        for r in svc.routes
                    ]
                if svc.plugins:
                    svc_dict["plugins"] = svc.plugins
                output["services"].append(svc_dict)

        if config.consumers:
            output["consumers"] = []
            for c in config.consumers:
                c_dict: dict[str, Any] = {
                    "username": c.username,
                    "custom_id": c.custom_id,
                    "tags": c.tags,
                }
                c_dict.update(c.credentials)
                output["consumers"].append(c_dict)

        buf = io.StringIO()
        yaml.dump(output, buf)
        return buf.getvalue()


    def _resolve_vault_ref(self, value: str) -> str:
        if not value or not self.vault_references:
            return value
        import re
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            return self.vault_references.get(var_name, match.group(0))
        return re.sub(r"\$\{([^}]+)\}", _replace, value)


def _slugify(name: str) -> str:
    import re
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    return slug or "unnamed"
