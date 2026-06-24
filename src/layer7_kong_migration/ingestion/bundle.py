"""Bundle loader for Layer 7 gateway exports.

Supports multiple export formats:
- RESTMAN bundle XML (.bundle, .xml)
- GMU export directory
- Graphman JSON export
- Policy Manager XML export
"""

import tempfile
import zipfile
from pathlib import Path

from layer7_kong_migration.ingestion.graphman import GraphmanParser
from layer7_kong_migration.ingestion.parser import PolicyParser
from layer7_kong_migration.models.ir import PolicyBundle


class BundleLoader:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.parser = PolicyParser()
        self.graphman = GraphmanParser()

    def load(self) -> PolicyBundle:
        if self.path.is_file():
            return self._load_file(self.path)
        if self.path.is_dir():
            return self._load_directory(self.path)
        raise FileNotFoundError(f"Bundle path not found: {self.path}")

    def _load_file(self, file_path: Path) -> PolicyBundle:
        if file_path.suffix == ".zip":
            return self._load_zip(file_path)
        if file_path.suffix in (".xml", ".bundle"):
            return self._load_xml_bundle(file_path)
        if file_path.suffix == ".json":
            return self._load_graphman(file_path)
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def _load_xml_bundle(self, file_path: Path) -> PolicyBundle:
        xml_content = file_path.read_text(encoding="utf-8")
        bundle = self.parser.parse_bundle(xml_content)
        bundle.name = file_path.stem
        bundle.source_path = str(file_path)
        return bundle

    def _load_zip(self, zip_path: Path) -> PolicyBundle:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)
            bundle = self._load_directory(Path(tmp_dir))
            bundle.name = zip_path.stem
            bundle.source_path = str(zip_path)
            self._capture_raw_xml(bundle)
            return bundle

    def _load_directory(self, dir_path: Path) -> PolicyBundle:
        xml_files = list(dir_path.rglob("*.xml")) + list(dir_path.rglob("*.bundle"))
        json_files = list(dir_path.rglob("*.json"))
        graphman_policy_files = list(dir_path.rglob("*.policy.json"))

        if not xml_files and not json_files:
            raise FileNotFoundError(f"No XML, bundle, or JSON files found in {dir_path}")

        combined = PolicyBundle(name=dir_path.name, source_path=str(dir_path), source_format="directory")

        if graphman_policy_files:
            sub = self.graphman._parse_exploded(dir_path)
            self._merge_bundle(combined, sub)
        else:
            for jf in json_files:
                try:
                    sub = self.graphman.parse_file(jf)
                    self._merge_bundle(combined, sub)
                except Exception as e:
                    print(f"Warning: Failed to parse {jf}: {e}")

        for bf in xml_files:
            try:
                xml_content = bf.read_text(encoding="utf-8")
                sub_bundle = self.parser.parse_bundle(xml_content)
                self._merge_bundle(combined, sub_bundle)
            except Exception as e:
                print(f"Warning: Failed to parse {bf}: {e}")

        return combined

    def _merge_bundle(self, target: PolicyBundle, source: PolicyBundle) -> None:
        target.services.extend(source.services)
        target.shared_policies.extend(source.shared_policies)
        target.encapsulated_assertions.extend(source.encapsulated_assertions)
        target.cluster_properties.update(source.cluster_properties)
        target.jdbc_connections.extend(source.jdbc_connections)
        target.stored_passwords.extend(source.stored_passwords)
        target.certificates.extend(source.certificates)

    def _load_graphman(self, file_path: Path) -> PolicyBundle:
        bundle = self.graphman.parse_file(file_path)
        bundle.name = file_path.stem
        bundle.source_path = str(file_path)
        return bundle

    def _capture_raw_xml(self, bundle: PolicyBundle) -> None:
        """Ensure raw_xml is captured before temp directory teardown."""
        for svc in bundle.services:
            for assertion in svc.assertions:
                if not assertion.raw_xml:
                    assertion.raw_xml = f"<!-- raw XML not captured for {assertion.assertion_type} -->"
