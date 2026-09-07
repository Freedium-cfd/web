import os
from typing import Optional

from dependency_injector import containers, providers

from freedium_library.services.medium.validators import (
    MediumServicePathValidator,
)
from freedium_library.utils.http import CurlRequest
from freedium_library.utils.http.client.config import (
    RequestConfig,
    RequestProxyConfig,
)

from .api import MediumApiService
from .config import MediumConfig
from .markdown_export import MarkdownExportService
from .medium import MediumService


def _public_url_from_env() -> str:
    return os.environ.get("FREEDIUM_PUBLIC_URL", "https://freedium-mirror.cfd").rstrip("/")


def _proxy_from_env() -> Optional[RequestProxyConfig]:
    """Build a RequestProxyConfig from WARP_PROXY_BALANCER / PROXY_LIST."""
    from freedium_library.utils.http import get_warp_proxy_config

    return get_warp_proxy_config()


def _build_request_config() -> RequestConfig:
    """Construct a RequestConfig honouring PROXY_LIST if set.

    Kept as a top-level function (rather than inlined into a
    ``providers.Callable``) so unit tests can patch it cleanly and so
    the proxy parsing has a single source of truth.
    """
    return RequestConfig(proxy=_proxy_from_env())


class MediumContainer(containers.DeclarativeContainer):
    config = providers.Singleton(MediumConfig)

    # RequestConfig is built once per container instance; CurlRequest reads
    # config.proxy and threads it through to curl_cffi sessions so all
    # outbound traffic goes via Warp when PROXY_LIST is set.
    request_config = providers.Singleton(_build_request_config)
    request = providers.Singleton(CurlRequest, config=request_config)

    # Injected from outside (CacheContainer.backend or None when CACHE_ENABLED=false).
    # Default to None so unit tests that instantiate MediumContainer in isolation
    # still work without a Mongo.
    cache_backend = providers.Object(None)

    api_service = providers.Singleton(
        MediumApiService,
        request=request,
        config=config,
        cache=cache_backend,
    )
    validator = providers.Singleton(
        MediumServicePathValidator,
        api_service=api_service,
    )
    service = providers.Singleton(
        MediumService,
        request=request,
        api_service=api_service,
        path_validator=validator,
    )

    public_url = providers.Callable(_public_url_from_env)
    markdown_export = providers.Singleton(
        MarkdownExportService,
        medium_service=service,
        public_url=public_url,
        gist_mode="raw",
    )
