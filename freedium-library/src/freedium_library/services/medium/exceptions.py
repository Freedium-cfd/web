from freedium_library.services.exceptions import ArticleNotFoundError, BaseServiceError


class MediumServiceError(BaseServiceError):
    pass


class InvalidMediumServicePathError(ArticleNotFoundError, MediumServiceError):
    pass


class InvalidMediumServiceHashError(InvalidMediumServicePathError):
    pass


class InvalidMediumServiceUrlError(InvalidMediumServicePathError):
    pass

