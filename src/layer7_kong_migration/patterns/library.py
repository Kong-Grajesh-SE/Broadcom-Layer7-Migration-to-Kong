"""Pattern library: loads and manages YAML pattern files."""

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML()


class PatternLibrary:
    def __init__(self, patterns_dir: str = "knowledge/patterns") -> None:
        self.patterns_dir = Path(patterns_dir)
        self.patterns: dict[str, dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self.patterns_dir.exists():
            return
        for path in sorted(self.patterns_dir.glob("*.yaml")):
            try:
                data = yaml.load(path)
                if data and "pattern" in data:
                    pid = data["pattern"].get("id", path.stem)
                    self.patterns[pid] = data["pattern"]
            except Exception as e:
                print(f"Warning: Failed to load pattern {path}: {e}")

    def get(self, pattern_id: str) -> dict[str, Any] | None:
        return self.patterns.get(pattern_id)

    def search(self, query: str) -> list[dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for pattern in self.patterns.values():
            searchable = f"{pattern.get('name', '')} {pattern.get('description', '')}".lower()
            layer7 = pattern.get("layer7", {})
            searchable += f" {layer7.get('assertion_type', '')}".lower()
            keywords = layer7.get("keywords", [])
            searchable += " " + " ".join(str(k) for k in keywords)
            if query_lower in searchable:
                results.append(pattern)
        return results

    def by_assertion_type(self, assertion_type: str) -> list[dict[str, Any]]:
        return [
            p for p in self.patterns.values()
            if p.get("layer7", {}).get("assertion_type") == assertion_type
        ]

    def list_all(self) -> list[dict[str, Any]]:
        return list(self.patterns.values())

    def count(self) -> int:
        return len(self.patterns)
