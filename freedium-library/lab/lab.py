import logging
from typing import Protocol

import requests
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject


# Interfaces
class UserRepository(Protocol):
    def get_user(self, user_id: int) -> dict: ...


class NotificationService(Protocol):
    def send_notification(self, user_id: int, message: str) -> None: ...


# Implementations
class APIUserRepository:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_user(self, user_id: int) -> dict:
        response = requests.get(f"{self.api_url}/users/{user_id}")
        return response.json()


class EmailNotificationService:
    def __init__(self, smtp_host: str, smtp_port: int):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_notification(self, user_id: int, message: str) -> None:
        # Implementation for sending email
        pass


# Container configuration
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Configure logging
    logging = providers.Resource(
        logging.basicConfig,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Services
    user_repository = providers.Singleton(APIUserRepository, api_url=config.api.url)

    notification_service = providers.Singleton(
        EmailNotificationService, smtp_host=config.smtp.host, smtp_port=config.smtp.port
    )


# Service using injected dependencies
class UserNotificationService:
    @inject
    def __init__(
        self,
        user_repo: UserRepository = Provide[Container.user_repository],
        notifier: NotificationService = Provide[Container.notification_service],
    ):
        self.user_repo = user_repo
        self.notifier = notifier

    def notify_user(self, user_id: int, message: str) -> None:
        user = self.user_repo.get_user(user_id)
        self.notifier.send_notification(user_id, message)


# config.yml
config = {
    "api": {"url": "https://api.example.com"},
    "smtp": {"host": "smtp.example.com", "port": 587},
}


# Main application
def main():
    container = Container()
    container.config.from_dict(config)

    # Wire container to current module
    container.wire(modules=[__name__])

    notification_service = UserNotificationService()
    notification_service.notify_user(1, "Hello!")


if __name__ == "__main__":
    main()
