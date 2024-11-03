from freedium_library.services.exceptions import BaseServiceError


class MediumServiceError(BaseServiceError):
    pass


class InvalidMediumServicePathError(MediumServiceError):
    pass
