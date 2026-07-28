import json
from pathlib import Path

from codemuscle.application.workspace.service import WorkspaceService


def test_initialize_workspace_creates_manifest_and_private_directories(tmp_path: Path) -> None:
    workspace = tmp_path / "CodeMuscleData"

    result = WorkspaceService().initialize(workspace)

    assert result.path == workspace
    assert (workspace / "workspace.json").is_file()
    assert {path.name for path in workspace.iterdir()} == {
        "workspace.json",
        "imports",
        "exports",
        "backups",
        "logs",
    }
    manifest = json.loads((workspace / "workspace.json").read_text(encoding="utf-8"))
    assert manifest["workspace_version"] == 1
    assert "api_key" not in manifest


def test_initialize_workspace_is_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "CodeMuscleData"
    service = WorkspaceService()

    first = service.initialize(workspace)
    second = service.initialize(workspace)

    assert second.manifest.created_at == first.manifest.created_at
