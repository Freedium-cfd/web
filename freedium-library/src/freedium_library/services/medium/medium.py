from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide

from freedium_library.container import Container
from freedium_library.services.base import BaseService

from .api import MediumApiService
from .container import MediumContainer
from .exceptions import InvalidMediumServicePathError
from .models import MediumPostDataResponse
from .validators import MediumServicePathValidator

if TYPE_CHECKING:
    from freedium_library.utils.http import Request


class MediumService(BaseService):
    def __init__(
        self,
        request: Request = Provide[Container.request],
        api_service: MediumApiService = Provide[MediumContainer.api_service],
        path_validator: MediumServicePathValidator = Provide[MediumContainer.validator],
    ):
        self.request = request
        self.api_service = api_service
        self.path_validator = path_validator

    def _is_valid(self, path: str) -> bool:
        return self.path_validator.is_valid(path)

    async def _ais_valid(self, path: str) -> bool:
        return await self.path_validator.ais_valid(path)

    def _render(self, path: str) -> str:
        if not self._is_valid(path):
            raise InvalidMediumServicePathError("Invalid Medium URL")

        response = self.request.get(path)
        response_json = response.json()
        _model = self._process_response(response_json)
        _content = self._process_content(_model)
        return _content

    async def _arender(self, path: str) -> str:
        if not await self._ais_valid(path):
            raise InvalidMediumServicePathError("Invalid Medium URL")

        response = await self.request.aget(path)
        _model = self._process_response(response.json())
        _content = self._process_content(_model)
        return _content

    def _process_response(self, response: str) -> MediumPostDataResponse:
        return MediumPostDataResponse.model_validate_json(response)

    def _process_content(self, data: MediumPostDataResponse) -> str:
        return "data"
