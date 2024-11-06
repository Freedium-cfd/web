from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from dependency_injector.wiring import Provide

from freedium_library.container import Container
from freedium_library.services.base import BaseService

from .api import MediumApiService
from .container import MediumContainer
from .exceptions import InvalidMediumServicePathError
from .models import MediumPostDataResponse
from .validators import MediumServicePathValidator

if TYPE_CHECKING:
    from freedium_library.models.request import Request


class MediumService(BaseService):
    def __init__(
        self,
        request: Request = Provide[Container.request],
        api_service: MediumApiService = Provide[MediumContainer.medium_api_service],
        path_validator: MediumServicePathValidator = Provide[
            MediumContainer.medium_path_validator
        ],
    ):
        self.request = request
        self.api_service = api_service
        self.path_validator = path_validator
        _content: Optional[str] = None

    def is_valid(self, path: str) -> bool:
        return self.path_validator.is_valid(path)

    async def ais_valid(self, path: str) -> bool:
        return await self.path_validator.ais_valid(path)

    def render(self, path: str) -> str:
        if not self.is_valid(path):
            raise InvalidMediumServicePathError("Invalid Medium URL")

        response = self.request.get(self._url)
        response_json = response.json()
        _model = self._process_response(response_json)
        _content = self._process_content(_model)
        return _content

    async def arender(self, path: str) -> str:
        if not await self.ais_valid(path):
            raise InvalidMediumServicePathError("Invalid Medium URL")

        response = await self.request.aget(self._url)
        _model = self._process_response(response.json())
        _content = self._process_content(_model)
        return _content

    def _process_response(self, response: str) -> MediumPostDataResponse:
        return MediumPostDataResponse.model_validate_json(response)

    def _process_content(self, data: MediumPostDataResponse) -> str:
        return "data"

    def set_url(self, url: str) -> None:
        self._url = url
        _content = None
