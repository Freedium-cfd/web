from freedium_library.__init__ import __VERSION__
from freedium_library.api.container import APIContainer

__NAME__ = "Freedium Library API"

api_container = APIContainer()
api_container.wire(
    modules=["freedium_library.api.settings", "freedium_library.api.main"]
)


__all__ = ["__NAME__", "__VERSION__"]
