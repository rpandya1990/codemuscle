import json
from datetime import UTC, datetime
from pathlib import Path

from codemuscle.application.workspace.schemas import WorkspaceManifest, WorkspaceResponse


class WorkspaceService:
    directories = ("exports", "backups", "logs")
    manifest_name = "workspace.json"

    def initialize(self, path: Path) -> WorkspaceResponse:
        path.mkdir(parents=True, exist_ok=True)
        manifest_path = path / self.manifest_name

        if manifest_path.exists():
            manifest = WorkspaceManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
        else:
            manifest = WorkspaceManifest(created_at=datetime.now(UTC))
            self._write_manifest(manifest_path, manifest)

        for directory in self.directories:
            (path / directory).mkdir(exist_ok=True)

        return WorkspaceResponse(path=path, manifest=manifest)

    @staticmethod
    def _write_manifest(path: Path, manifest: WorkspaceManifest) -> None:
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8"
        )
        temporary_path.replace(path)
