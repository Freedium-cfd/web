from dataclasses import dataclass

from freedium_library import __NAME__, __VERSION__
from freedium_library.api.container import APIContainer

container = APIContainer()


@dataclass
class ApplicationSettings:
    title: str = __NAME__
    version: str = __VERSION__
    openapi_url: str | None = f"{container.config.PREFIX_PATH}/openapi.json"
    docs_url: str | None = f"{container.config.PREFIX_PATH}/docs"
    redoc_url: str | None = f"{container.config.PREFIX_PATH}/redoc"

    def disable_docs(self) -> None:
        self.openapi_url = None
        self.docs_url = None
        self.redoc_url = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "title": self.title,
            "version": self.version,
            "openapi_url": self.openapi_url,
            "docs_url": self.docs_url,
            "redoc_url": self.redoc_url,
        }
