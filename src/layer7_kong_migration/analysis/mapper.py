"""Policy-to-plugin mapping loader.

Loads mappings from knowledge/mappings/assertion-to-plugin.yaml and provides
lookup by assertion type. Falls back to built-in defaults.
"""

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from layer7_kong_migration.analysis.classifier import CONDITIONAL_ASSERTIONS, DIRECT_ASSERTIONS

yaml = YAML()


DEFAULT_MAPPINGS: dict[str, dict[str, Any]] = {
    atype: {"kong_plugin": plugin, "complexity": "direct"}
    for atype, plugin in DIRECT_ASSERTIONS.items()
    if plugin != "_skip"
}
DEFAULT_MAPPINGS.update({
    atype: {"kong_plugin": plugin, "complexity": "conditional", "review_flag": flag.value}
    for atype, (plugin, flag) in CONDITIONAL_ASSERTIONS.items()
    if not plugin.startswith("_")
})


class PolicyMapper:
    def __init__(self, mappings_path: Path | None = None) -> None:
        self.mappings: dict[str, dict[str, Any]] = dict(DEFAULT_MAPPINGS)
        if mappings_path and mappings_path.exists():
            self._load_yaml(mappings_path)

    def _load_yaml(self, path: Path) -> None:
        data = yaml.load(path)
        if data and "mappings" in data:
            for entry in data["mappings"]:
                atype = entry.get("assertion_type", "")
                if atype:
                    self.mappings[atype] = entry

    def get_kong_plugin(self, assertion_type: str) -> str | None:
        entry = self.mappings.get(assertion_type)
        if entry:
            return entry.get("kong_plugin")
        return None

    def get_mapping(self, assertion_type: str) -> dict[str, Any] | None:
        return self.mappings.get(assertion_type)

    def all_mappings(self) -> dict[str, dict[str, Any]]:
        return dict(self.mappings)
