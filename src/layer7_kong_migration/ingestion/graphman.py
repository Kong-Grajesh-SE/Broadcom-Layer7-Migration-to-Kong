"""Graphman JSON bundle parser.

Parses the Graphman export format used by Layer 7 gateway's modern management API.
Supports both "imploded" (single JSON) and "exploded" (directory tree) formats.

Graphman policy structure:
    {
        "policies": [
            {
                "goid": "...",
                "guid": "...",
                "name": "My Policy",
                "policyType": "SERVICE" | "FRAGMENT" | "GLOBAL",
                "folderPath": "/path/to/folder",
                "soap": false,
                "policy": {
                    "xml": "<wsp:Policy ...>...</wsp:Policy>",
                    "code": { ... },    # parsed JSON representation
                    "json": "{ ... }"   # stringified JSON representation
                }
            }
        ],
        "services": [
            {
                "goid": "...",
                "name": "My Service",
                "resolutionPath": "/api/v1/resource",
                "enabled": true,
                "folderPath": "/services",
                "policy": { "xml": "..." },
                "properties": { ... }
            }
        ],
        "clusterProperties": [
            {"name": "...", "value": "..."}
        ],
        "properties": { ... }
    }
"""

import json
from pathlib import Path
from typing import Any

from layer7_kong_migration.ingestion.parser import PolicyParser
from layer7_kong_migration.models.ir import PolicyBundle, ServiceDefinition


class GraphmanParser:
    def __init__(self) -> None:
        self.policy_parser = PolicyParser()

    def parse_file(self, path: Path) -> PolicyBundle:
        if path.is_dir():
            return self._parse_exploded(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return self._parse_imploded(data, path.stem, str(path))

    def _parse_imploded(self, data: dict[str, Any], name: str, source: str) -> PolicyBundle:
        bundle = PolicyBundle(name=name, source_format="graphman", source_path=source)

        for svc_data in data.get("services", []):
            svc = self._parse_service(svc_data)
            if svc:
                bundle.services.append(svc)

        for pol_data in data.get("policies", []):
            policy_type = pol_data.get("policyType", "")
            pol = self._parse_policy(pol_data)
            if pol:
                if policy_type == "FRAGMENT":
                    if "encapsulated" in pol_data.get("name", "").lower():
                        bundle.encapsulated_assertions.append(pol)
                    else:
                        bundle.shared_policies.append(pol)
                elif policy_type == "GLOBAL":
                    bundle.shared_policies.append(pol)
                else:
                    bundle.services.append(pol)

        for cp in data.get("clusterProperties", []):
            cp_name = cp.get("name", "")
            cp_value = cp.get("value", "")
            if cp_name:
                bundle.cluster_properties[cp_name] = cp_value

        return bundle

    def _parse_service(self, data: dict[str, Any]) -> ServiceDefinition | None:
        name = data.get("name", "unnamed")
        svc = ServiceDefinition(
            name=name,
            service_id=data.get("goid", ""),
            folder_path=data.get("folderPath", "/"),
            resolution_path=data.get("resolutionPath", ""),
            enabled=data.get("enabled", True),
            soap=data.get("soapVersion") is not None,
        )

        props = data.get("properties", {})
        if isinstance(props, dict):
            svc.properties = {k: str(v) for k, v in props.items()}

        policy_xml = self._extract_policy_xml(data)
        if policy_xml:
            try:
                flow, assertions = self.policy_parser._parse_policy_xml(policy_xml)
                svc.policy_flow = flow
                svc.assertions = assertions
            except Exception as e:
                print(f"Warning: Failed to parse policy XML for service '{name}': {e}")

        return svc

    def _parse_policy(self, data: dict[str, Any]) -> ServiceDefinition | None:
        name = data.get("name", "unnamed")
        pol = ServiceDefinition(
            name=name,
            service_id=data.get("goid", ""),
            folder_path=data.get("folderPath", "/"),
            soap=data.get("soap", False),
        )

        policy_xml = self._extract_policy_xml(data)
        if policy_xml:
            try:
                flow, assertions = self.policy_parser._parse_policy_xml(policy_xml)
                pol.policy_flow = flow
                pol.assertions = assertions
            except Exception as e:
                print(f"Warning: Failed to parse policy XML for '{name}': {e}")

        return pol

    def _extract_policy_xml(self, data: dict[str, Any]) -> str | None:
        policy = data.get("policy", {})
        if not policy:
            return None

        if isinstance(policy.get("xml"), str) and policy["xml"].strip():
            return policy["xml"]

        if isinstance(policy.get("code"), dict):
            return self._code_to_xml(policy["code"])

        if isinstance(policy.get("json"), str):
            try:
                code = json.loads(policy["json"])
                return self._code_to_xml(code)
            except (json.JSONDecodeError, TypeError):
                pass

        return None

    def _code_to_xml(self, code: dict[str, Any]) -> str:
        """Convert Graphman JSON policy code to XML for the existing parser.

        The JSON code format mirrors the XML structure but uses JSON objects:
            {"All": [{"SetVariable": {...}}, {"HttpRoutingAssertion": {...}}]}
        """
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy"'
            ' xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">',
        ]
        self._code_node_to_xml(code, lines, indent=2)
        lines.append("</wsp:Policy>")
        return "\n".join(lines)

    def _code_node_to_xml(
        self, node: Any, lines: list[str], indent: int = 0
    ) -> None:
        prefix = " " * indent

        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("All", "OneOrMore", "ExactlyOne"):
                    lines.append(f"{prefix}<wsp:{key} wsp:Usage=\"Required\">")
                    if isinstance(value, list):
                        for item in value:
                            self._code_node_to_xml(item, lines, indent + 2)
                    elif isinstance(value, dict):
                        self._code_node_to_xml(value, lines, indent + 2)
                    lines.append(f"{prefix}</wsp:{key}>")
                else:
                    if isinstance(value, dict) and value:
                        lines.append(f"{prefix}<L7p:{key}>")
                        for k, v in value.items():
                            if isinstance(v, str):
                                lines.append(f'{prefix}  <L7p:{k} stringValue="{_xml_escape(v)}"/>')
                            elif isinstance(v, bool):
                                lines.append(f'{prefix}  <L7p:{k} booleanValue="{str(v).lower()}"/>')
                            elif isinstance(v, int):
                                lines.append(f'{prefix}  <L7p:{k} intValue="{v}"/>')
                            elif isinstance(v, dict):
                                self._code_node_to_xml({k: v}, lines, indent + 2)
                            elif isinstance(v, list):
                                lines.append(f'{prefix}  <L7p:{k}>')
                                for item in v:
                                    if isinstance(item, dict):
                                        self._code_node_to_xml(item, lines, indent + 4)
                                    else:
                                        lines.append(f'{prefix}    <L7p:item stringValue="{_xml_escape(str(item))}"/>')
                                lines.append(f'{prefix}  </L7p:{k}>')
                        lines.append(f"{prefix}</L7p:{key}>")
                    elif value is None or value == {}:
                        lines.append(f"{prefix}<L7p:{key}/>")
                    else:
                        lines.append(f"{prefix}<L7p:{key}/>")

        elif isinstance(node, list):
            for item in node:
                self._code_node_to_xml(item, lines, indent)

    def _parse_exploded(self, dir_path: Path) -> PolicyBundle:
        """Parse exploded Graphman format (directory tree with individual .policy.json files)."""
        bundle = PolicyBundle(name=dir_path.name, source_format="graphman_exploded", source_path=str(dir_path))

        policy_files = list(dir_path.rglob("*.policy.json"))
        if not policy_files:
            json_files = list(dir_path.rglob("*.json"))
            for jf in json_files:
                try:
                    data = json.loads(jf.read_text(encoding="utf-8"))
                    if "policies" in data or "services" in data:
                        sub = self._parse_imploded(data, jf.stem, str(jf))
                        bundle.services.extend(sub.services)
                        bundle.shared_policies.extend(sub.shared_policies)
                        bundle.encapsulated_assertions.extend(sub.encapsulated_assertions)
                        bundle.cluster_properties.update(sub.cluster_properties)
                except (json.JSONDecodeError, KeyError):
                    continue
            return bundle

        for pf in policy_files:
            try:
                data = json.loads(pf.read_text(encoding="utf-8"))
                pol = self._parse_policy(data)
                if pol:
                    ptype = data.get("policyType", "")
                    if ptype == "FRAGMENT":
                        bundle.shared_policies.append(pol)
                    else:
                        bundle.services.append(pol)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to parse {pf}: {e}")

        cp_files = list(dir_path.rglob("*.clusterproperty.json")) + list(
            dir_path.rglob("clusterProperties/*.json")
        )
        for cpf in cp_files:
            try:
                data = json.loads(cpf.read_text(encoding="utf-8"))
                name = data.get("name", cpf.stem)
                value = data.get("value", "")
                bundle.cluster_properties[name] = value
            except (json.JSONDecodeError, KeyError):
                continue

        return bundle


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
