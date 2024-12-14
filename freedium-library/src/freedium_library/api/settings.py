from typing import Any, Optional

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel, Field

from freedium_library import __NAME__, __VERSION__
from freedium_library.api.config import APIConfig
from freedium_library.api.container import APIContainer


class ApplicationSettings(BaseModel):
    title: str = Field(default=f"{__NAME__} API Service")
    version: str = Field(default=__VERSION__)
    prefix_path: str = Field(default="/api")
    openapi_url: Optional[str] = None
    docs_url: Optional[str] = None
    redoc_url: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}

    @inject
    def __init__(
        self,
        title: str = __NAME__,
        version: str = __VERSION__,
        api_config: APIConfig = Provide[APIContainer.config],
        **data: Any,
    ):
        prefix_path = api_config.PREFIX_PATH
        super().__init__(
            title=title,
            version=version,
            prefix_path=prefix_path,
            openapi_url=f"{prefix_path}/openapi.json",
            docs_url=f"{prefix_path}/docs",
            redoc_url=f"{prefix_path}/redoc",
            **data,
        )

    def disable_docs(self) -> None:
        self.openapi_url = None
        self.docs_url = None
        self.redoc_url = None

    def to_dict(self) -> dict[str, str | None]:
        return self.model_dump()
