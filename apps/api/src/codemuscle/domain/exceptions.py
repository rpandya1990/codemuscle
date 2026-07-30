import uuid


class DomainError(Exception):
    code = "DOMAIN_ERROR"
    status_code = 400

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProblemNotFoundError(DomainError):
    code = "PROBLEM_NOT_FOUND"
    status_code = 404

    def __init__(self, problem_id: uuid.UUID) -> None:
        super().__init__("The requested problem does not exist.", {"problem_id": str(problem_id)})


class ImportNotFoundError(DomainError):
    code = "IMPORT_NOT_FOUND"
    status_code = 404

    def __init__(self, import_id: uuid.UUID) -> None:
        super().__init__("The requested import does not exist.", {"import_id": str(import_id)})


class QueueNotFoundError(DomainError):
    code = "QUEUE_NOT_FOUND"
    status_code = 404

    def __init__(self, queue_id: uuid.UUID) -> None:
        super().__init__("The requested queue does not exist.", {"queue_id": str(queue_id)})


class WorkspaceNotInitializedError(DomainError):
    code = "WORKSPACE_NOT_INITIALIZED"

    def __init__(self) -> None:
        super().__init__("Initialize a private workspace before importing data.")


class ImportFileError(DomainError):
    code = "INVALID_IMPORT_FILE"


class DataLifecycleError(DomainError):
    code = "DATA_LIFECYCLE_ERROR"


class BackupNotFoundError(DomainError):
    code = "BACKUP_NOT_FOUND"
    status_code = 404

    def __init__(self, backup_id: uuid.UUID) -> None:
        super().__init__("The requested backup does not exist.", {"backup_id": str(backup_id)})
