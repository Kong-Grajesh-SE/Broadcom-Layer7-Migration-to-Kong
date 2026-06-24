"""XML parser for Layer 7 gateway policy bundles.

Handles multiple XML formats:
- RESTMAN bundle format (l7: namespace)
- Policy XML format (L7p: + wsp: namespaces)
- Policy Manager export format (exp: namespace)
"""

from typing import Any

import defusedxml.ElementTree as SafeET
from lxml import etree

from layer7_kong_migration.ingestion.extractors import extract_assertion_config
from layer7_kong_migration.models.ir import (
    AssertionConfig,
    Endpoint,
    Flow,
    FlowStep,
    PolicyBundle,
    ServiceDefinition,
)

NS = {
    "l7": "http://ns.l7tech.com/2010/04/gateway-management",
    "L7p": "http://www.layer7tech.com/ws/policy",
    "wsp": "http://schemas.xmlsoap.org/ws/2002/12/policy",
    "exp": "http://www.layer7tech.com/ws/policy/export",
}


class PolicyParser:
    def parse_bundle(self, xml_content: str) -> PolicyBundle:
        SafeET.fromstring(xml_content)
        root = etree.fromstring(xml_content.encode("utf-8"))

        tag = etree.QName(root.tag).localname if "}" in root.tag else root.tag

        if tag == "Item":
            return self._parse_restman_item(root)
        if tag == "Bundle":
            return self._parse_restman_bundle(root)
        if tag == "Export":
            return self._parse_policy_export(root)
        if tag == "Policy" or tag == "All":
            return self._parse_standalone_policy(root)

        raise ValueError(f"Unrecognized root element: {root.tag}")

    def _parse_restman_item(self, root: etree._Element) -> PolicyBundle:
        bundle_elem = root.find(".//l7:Bundle", NS)
        if bundle_elem is None:
            bundle_elem = root.find(".//l7:Resource/l7:Bundle", NS)
        if bundle_elem is None:
            raise ValueError("No <l7:Bundle> found inside <l7:Item>")
        return self._parse_restman_bundle(bundle_elem)

    def _parse_restman_bundle(self, bundle_elem: etree._Element) -> PolicyBundle:
        bundle = PolicyBundle(name="bundle", source_format="restman")
        refs = bundle_elem.find("l7:References", NS)
        if refs is None:
            return bundle

        for item in refs.findall("l7:Item", NS):
            item_type = self._text(item, "l7:Type")
            resource = item.find("l7:Resource", NS)
            if resource is None:
                continue

            if item_type == "SERVICE":
                svc = self._parse_service_item(item, resource)
                if svc:
                    bundle.services.append(svc)
            elif item_type == "POLICY":
                pol = self._parse_policy_item(item, resource)
                if pol:
                    bundle.shared_policies.append(pol)
            elif item_type == "ENCAPSULATED_ASSERTION":
                enc = self._parse_encass_item(item, resource)
                if enc:
                    bundle.encapsulated_assertions.append(enc)
            elif item_type == "CLUSTER_PROPERTY":
                self._parse_cluster_property(resource, bundle)
            elif item_type == "JDBC_CONNECTION":
                self._parse_jdbc_connection(resource, bundle)
            elif item_type == "STORED_PASSWORD":
                name = self._text(item, "l7:Name")
                if name:
                    bundle.stored_passwords.append(name)

        return bundle

    def _parse_service_item(
        self, item: etree._Element, resource: etree._Element
    ) -> ServiceDefinition | None:
        svc_elem = resource.find("l7:Service", NS)
        if svc_elem is None:
            return None

        name = self._text(item, "l7:Name") or "unnamed-service"
        svc_id = item.get("id", "")

        svc = ServiceDefinition(name=name, service_id=svc_id)

        detail = svc_elem.find("l7:ServiceDetail", NS)
        if detail is not None:
            svc.folder_path = detail.get("folderId", "/")
            svc.enabled = self._bool_prop(detail, "enabled", True)

            props = detail.find("l7:Properties", NS)
            if props is not None:
                for prop in props.findall("l7:Property", NS):
                    key = prop.get("key", "")
                    val_elem = prop.find("l7:StringValue", NS)
                    if val_elem is not None and val_elem.text:
                        svc.properties[key] = val_elem.text
                        if key == "property.soap" and val_elem.text.lower() == "true":
                            svc.soap = True

            url_elem = detail.find("l7:ServiceMappings/l7:HttpMapping/l7:UrlPattern", NS)
            if url_elem is not None and url_elem.text:
                svc.resolution_path = url_elem.text

        resources = svc_elem.find("l7:Resources", NS)
        if resources is not None:
            policy_res = resources.find("l7:ResourceSet/l7:Resource[@type='policy']", NS)
            if policy_res is not None and policy_res.text:
                flow, assertions = self._parse_policy_xml(policy_res.text)
                svc.policy_flow = flow
                svc.assertions = assertions

            wsdl_res = resources.find("l7:ResourceSet/l7:Resource[@type='wsdl']", NS)
            if wsdl_res is not None:
                svc.wsdl_url = wsdl_res.get("sourceUrl", "")

        for assertion in svc.assertions:
            if assertion.assertion_type == "HttpRoutingAssertion":
                url = assertion.configuration.get("protected_service_url", "")
                if url:
                    svc.endpoints.append(Endpoint(name=f"{name}-backend", url=url))

        return svc

    def _parse_policy_item(
        self, item: etree._Element, resource: etree._Element
    ) -> ServiceDefinition | None:
        policy_elem = resource.find("l7:Policy", NS)
        if policy_elem is None:
            return None

        name = self._text(item, "l7:Name") or "unnamed-policy"
        pol = ServiceDefinition(name=name, service_id=item.get("id", ""))

        res = policy_elem.find("l7:Resources/l7:ResourceSet/l7:Resource[@type='policy']", NS)
        if res is not None and res.text:
            flow, assertions = self._parse_policy_xml(res.text)
            pol.policy_flow = flow
            pol.assertions = assertions

        return pol

    def _parse_encass_item(
        self, item: etree._Element, resource: etree._Element
    ) -> ServiceDefinition | None:
        enc_elem = resource.find("l7:EncapsulatedAssertion", NS)
        if enc_elem is None:
            return None
        name = self._text(item, "l7:Name") or "unnamed-encass"
        return ServiceDefinition(name=name, service_id=item.get("id", ""))

    def _parse_cluster_property(self, resource: etree._Element, bundle: PolicyBundle) -> None:
        prop = resource.find("l7:ClusterProperty", NS)
        if prop is None:
            return
        name_elem = prop.find("l7:Name", NS)
        val_elem = prop.find("l7:Value", NS)
        if name_elem is not None and name_elem.text and val_elem is not None:
            bundle.cluster_properties[name_elem.text] = val_elem.text or ""

    def _parse_jdbc_connection(self, resource: etree._Element, bundle: PolicyBundle) -> None:
        jdbc = resource.find("l7:JDBCConnection", NS)
        if jdbc is None:
            return
        conn: dict[str, Any] = {}
        for child in jdbc:
            tag = etree.QName(child.tag).localname
            conn[tag] = child.text or ""
        bundle.jdbc_connections.append(conn)

    def _parse_policy_export(self, root: etree._Element) -> PolicyBundle:
        bundle = PolicyBundle(name="export", source_format="policy_export")
        refs = root.findall(".//l7:References/l7:Item", NS)
        if not refs:
            policy_elem = root.find(".//wsp:Policy", NS) or root.find(".//wsp:All", NS)
            if policy_elem is not None:
                xml_str = etree.tostring(policy_elem, encoding="unicode")
                flow, assertions = self._parse_policy_xml(xml_str)
                svc = ServiceDefinition(name="exported-policy", policy_flow=flow, assertions=assertions)
                bundle.services.append(svc)
        return bundle

    def _parse_standalone_policy(self, root: etree._Element) -> PolicyBundle:
        bundle = PolicyBundle(name="standalone", source_format="policy_xml")
        xml_str = etree.tostring(root, encoding="unicode")
        flow, assertions = self._parse_policy_xml(xml_str)
        svc = ServiceDefinition(name="standalone-policy", policy_flow=flow, assertions=assertions)
        bundle.services.append(svc)
        return bundle

    def _parse_policy_xml(self, policy_xml: str) -> tuple[Flow, list[AssertionConfig]]:
        try:
            root = etree.fromstring(policy_xml.encode("utf-8"))
        except etree.XMLSyntaxError:
            wrapped = f'<wsp:Policy xmlns:L7p="http://www.layer7tech.com/ws/policy" xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">{policy_xml}</wsp:Policy>'
            root = etree.fromstring(wrapped.encode("utf-8"))

        assertions: list[AssertionConfig] = []
        flow = self._parse_flow_element(root, assertions)
        return flow, assertions

    def _parse_flow_element(
        self, elem: etree._Element, assertions: list[AssertionConfig], depth: int = 0
    ) -> Flow:
        local = etree.QName(elem.tag).localname if "}" in elem.tag else elem.tag

        logic = "all"
        if local == "OneOrMore":
            logic = "one_or_more"
        elif local == "ExactlyOne":
            logic = "exactly_one"

        flow = Flow(name=f"flow-{depth}", logic=logic)

        for child in elem:
            if not isinstance(child.tag, str):
                continue
            child_local = etree.QName(child.tag).localname if "}" in child.tag else child.tag
            child_ns = etree.QName(child.tag).namespace if "}" in child.tag else ""

            if child_local in ("All", "OneOrMore", "ExactlyOne", "Policy"):
                sub_flow = self._parse_flow_element(child, assertions, depth + 1)
                flow.sub_flows.append(sub_flow)
            elif child_ns == NS["L7p"] or (child_ns == "" and child_local.startswith("L7p:")):
                assertion_type = child_local.replace("L7p:", "")
                raw_xml = etree.tostring(child, encoding="unicode", pretty_print=True)
                config = extract_assertion_config(assertion_type, child, NS)

                assertion = AssertionConfig(
                    name=config.pop("_name", assertion_type),
                    assertion_type=assertion_type,
                    configuration=config,
                    raw_xml=raw_xml,
                )
                assertions.append(assertion)
                flow.steps.append(FlowStep(
                    assertion_name=assertion.name,
                    enabled=config.get("_enabled", True),
                ))

        return flow

    def _text(self, elem: etree._Element, xpath: str) -> str:
        found = elem.find(xpath, NS)
        return found.text.strip() if found is not None and found.text else ""

    def _bool_prop(self, elem: etree._Element, key: str, default: bool = False) -> bool:
        props = elem.find("l7:Properties", NS)
        if props is None:
            return default
        for prop in props.findall("l7:Property", NS):
            if prop.get("key") == key:
                val = prop.find("l7:BooleanValue", NS)
                if val is not None and val.text:
                    return val.text.lower() == "true"
        return default
