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
