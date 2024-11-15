from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class RequestProxyConfig:
    type: Literal["http", "https", "socks5"]
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

    @property
    def url(self) -> str:
        type = self.type.replace("https", "http")
        proxy_url = f"{type}://"
        if self.username and self.password:
            proxy_url += f"{self.username}:{self.password}@"
        proxy_url += f"{self.host}:{self.port}"
        return proxy_url


@dataclass
class RequestConfig:
    timeout: int = 6
    retries: int = 3
    proxy: Optional[RequestProxyConfig] = None
    # backoff_factor: float = 0.1 # not possible. Default value: 0.5. https://github.com/encode/httpx/discussions/1895
