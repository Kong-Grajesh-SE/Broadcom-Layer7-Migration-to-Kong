"""XML utility functions."""

from lxml import etree


def safe_parse(xml_string: str) -> etree._Element:
    import defusedxml.ElementTree as SafeET
    SafeET.fromstring(xml_string)
    return etree.fromstring(xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string)


def pretty_print(elem: etree._Element) -> str:
    return etree.tostring(elem, encoding="unicode", pretty_print=True)


def strip_namespaces(xml_string: str) -> str:
    import re
    return re.sub(r'\s*xmlns:[a-zA-Z0-9]+="[^"]*"', "", xml_string)
