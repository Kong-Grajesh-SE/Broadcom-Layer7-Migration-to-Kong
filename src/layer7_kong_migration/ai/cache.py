"""MD5-keyed result cache for AI analysis.

Avoids duplicate API calls for identical assertions across bundles.
Cache key: MD5(assertion_type | configuration | resource_content).
"""

import hashlib
import json
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()


class AICache:
    def __init__(self, cache_dir: str = ".cache/ai") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_key(self, assertion_type: str, config: dict, resource: str = "") -> str:
        content = f"{assertion_type}|{json.dumps(config, sort_keys=True, default=str)}|{resource}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        path = self.cache_dir / f"{key}.yaml"
        if path.exists():
            data = yaml.load(path)
            return dict(data) if data else None
        return None

    def put(self, key: str, result: dict) -> None:
        path = self.cache_dir / f"{key}.yaml"
        yaml.dump(dict(result), path)

    def clear(self) -> int:
        count = 0
        for f in self.cache_dir.glob("*.yaml"):
            f.unlink()
            count += 1
        return count

    def stats(self) -> dict[str, int]:
        files = list(self.cache_dir.glob("*.yaml"))
        return {"entries": len(files), "size_bytes": sum(f.stat().st_size for f in files)}
