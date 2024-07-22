class MediumParserException(Exception):
    pass


class PageLoadingError(MediumParserException):
    pass


class NotValidMediumURL(MediumParserException):
    pass


class InvalidURL(MediumParserException):
    pass


class InvalidMediumPostURL(MediumParserException):
    pass


class InvalidMediumPostID(MediumParserException):
    pass


class MediumPostQueryError(MediumParserException):
    pass


class MediumPostNotFound(MediumPostQueryError):
    pass


class MediumPostUnavailable(MediumPostQueryError):
    pass


class MediumPostDeleted(MediumPostQueryError):
    pass
