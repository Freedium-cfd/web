"""Service resolver for detecting and resolving content types to appropriate services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from loguru import logger

from freedium_library.services.exceptions import InvalidServiceError

if TYPE_CHECKING:
    from freedium_library.services.base import BaseService


class ServiceResolutionError(InvalidServiceError):
    """Raised when no service can handle the provided content."""

    pass


class ServiceResolver:
    """Detects and resolves content to appropriate service handlers."""

    def __init__(self):
        """Initialize the service resolver."""
        self._services: dict[str, BaseService] = {}

    def register(self, service_name: str, service: BaseService) -> None:
        """
        Register a service handler.

        Args:
            service_name: Unique identifier for the service (e.g., "medium")
            service: The service instance that implements BaseService
        """
        self._services[service_name] = service
        logger.debug(f"Registered service: {service_name}")

    async def resolve(
        self, content: str
    ) -> tuple[str, BaseService]:
        """
        Resolve content to the appropriate service.

        Tries each registered service to find one that can handle the content.

        Args:
            content: The content string (URL, ID, or any string)

        Returns:
            A tuple of (service_name, service_instance)

        Raises:
            ServiceResolutionError: If no service can handle the content
        """
        logger.debug(f"Resolving content: {content[:50]}...")

        # Try each service in order
        for service_name, service in self._services.items():
            logger.debug(f"Trying service: {service_name}")
            try:
                if await service.ais_valid(content):
                    logger.debug(f"Content resolved to service: {service_name}")
                    return service_name, service
            except Exception as e:
                logger.debug(
                    f"Service {service_name} validation failed: {e}"
                )
                continue

        # No service could handle this content
        available_services = ", ".join(self._services.keys())
        raise ServiceResolutionError(
            f"No service could handle the provided content. "
            f"Available services: {available_services}"
        )

    def get_service(self, service_name: str) -> BaseService:
        """
        Get a specific service by name.

        Args:
            service_name: The service identifier

        Returns:
            The service instance

        Raises:
            ServiceResolutionError: If service is not registered
        """
        if service_name not in self._services:
            available = ", ".join(self._services.keys())
            raise ServiceResolutionError(
                f"Service '{service_name}' not found. "
                f"Available services: {available}"
            )
        return self._services[service_name]

    def list_services(self) -> list[str]:
        """List all registered service names."""
        return list(self._services.keys())


def build_service_resolver(
    proxy: str | None = None,
    medium_service: BaseService | None = None,
) -> ServiceResolver:
    """Build and configure the standard ServiceResolver with all enabled publications.

    Mirrors the canonical registration order: specific hosts first (Athletic,
    NYT, WaPo, FT, Economist, Reuters, Bloomberg, Quora), and Medium last as
    the permissive fallback.
    """
    from freedium_library.api.config import (
        AthleticConfig,
        BloombergConfig,
        EconomistConfig,
        FtConfig,
        MediumConfig,
        NytConfig,
        QuoraConfig,
        ReutersConfig,
        WapoConfig,
    )

    resolver = ServiceResolver()

    ath_cfg = AthleticConfig()
    if ath_cfg.ENABLED:
        from freedium_library.services.athletic import AthleticService

        resolver.register("athletic", AthleticService(mdream_url=ath_cfg.MDREAM_URL))
        logger.info("Athletic service registered")

    nyt_cfg = NytConfig()
    if nyt_cfg.ENABLED:
        from freedium_library.services.nyt import NytService
        from freedium_library.services.nyt import client as _nyt_client

        if _nyt_client._NYT_PRIVATE_KEY is not None:
            resolver.register(
                "nyt", NytService(proxy=proxy, mdream_url=nyt_cfg.MDREAM_URL)
            )
            logger.info("NYT service registered (egress via WARP)")
        else:
            logger.warning("NYT_ENABLED but NYT_SIGNING_KEY missing/invalid — NYT not registered")

    if WapoConfig().ENABLED:
        from freedium_library.services.wapo import WapoService

        resolver.register("wapo", WapoService())
        logger.info("WaPo service registered")

    if FtConfig().ENABLED:
        from freedium_library.services.ft import FtService

        resolver.register("ft", FtService())
        logger.info("FT service registered")

    if EconomistConfig().ENABLED:
        from freedium_library.services.economist import EconomistService

        resolver.register("economist", EconomistService())
        logger.info("Economist service registered")

    if ReutersConfig().ENABLED:
        from freedium_library.services.reuters import ReutersService

        resolver.register("reuters", ReutersService(proxy=proxy))
        logger.info("Reuters service registered")

    if BloombergConfig().ENABLED:
        from freedium_library.services.bloomberg import BloombergService

        resolver.register("bloomberg", BloombergService(proxy=proxy))
        logger.info("Bloomberg service registered")

    if QuoraConfig().ENABLED:
        from freedium_library.services.quora import QuoraService

        resolver.register("quora", QuoraService(proxy=proxy))
        logger.info("Quora service registered")

    if MediumConfig().ENABLED:
        if medium_service is None:
            from freedium_library.services.medium.container import MediumContainer

            medium_service = MediumContainer().service()
        resolver.register("medium", medium_service)
        logger.info("Medium service registered (last — catch-all)")
    else:
        logger.info("Medium service disabled (MEDIUM_ENABLED=false)")

    return resolver
