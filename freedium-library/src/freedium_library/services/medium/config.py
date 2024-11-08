from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class MediumConfig(BaseSettings):
    cookies: Optional[str] = Field(default=None)
