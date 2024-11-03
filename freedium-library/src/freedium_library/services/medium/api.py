from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freedium_library.models import Request


class MediumApiService:
    def __init__(self, request: Request):
        self.request = request
