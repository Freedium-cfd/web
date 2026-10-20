from freedium_library.services.exceptions import (
    ArticleNotFoundError,
    BaseServiceError,
    UpstreamBlockedError,
)


class MediumServiceError(BaseServiceError):
    pass


class InvalidMediumServicePathError(ArticleNotFoundError, MediumServiceError):
    pass


class InvalidMediumServiceHashError(InvalidMediumServicePathError):
    pass


class InvalidMediumServiceUrlError(InvalidMediumServicePathError):
    pass


class MediumBlockedError(UpstreamBlockedError, MediumServiceError):
    """Raised when Medium GraphQL queries fail due to soft-blocks or rate-limits."""
    pass

