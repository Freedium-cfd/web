from freedium_library.services.exceptions import BaseServiceError


class MediumServiceError(BaseServiceError):
    pass


class InvalidMediumServicePathError(MediumServiceError):
    pass


class InvalidMediumServiceHashError(InvalidMediumServicePathError):
    pass


class InvalidMediumServiceUrlError(InvalidMediumServicePathError):
    pass
