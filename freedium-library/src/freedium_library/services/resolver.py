"""Service resolver for detecting and resolving content types to appropriate services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from loguru import logger

if TYPE_CHECKING:
    from freedium_library.services.base import BaseService


class ServiceResolutionError(Exception):
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
