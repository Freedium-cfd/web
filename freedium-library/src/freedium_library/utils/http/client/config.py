from dataclasses import dataclass
from typing import Literal, Optional
from urllib.parse import urlparse


@dataclass
class RequestProxyConfig:
    type: Literal["http", "https", "socks5"]
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

    @classmethod
    def from_url(cls, url: str | None) -> Optional["RequestProxyConfig"]:
        """Parse proxy URL (e.g. socks5://haproxy-pb:1080) safely using urlparse."""
        if not url or not url.strip():
            return None
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https", "socks5", "socks5h"):
            return None
        normalized_scheme: Literal["http", "https", "socks5"] = (
            "socks5" if "socks" in scheme else ("https" if scheme == "https" else "http")
        )
        return cls(
            type=normalized_scheme,
            host=parsed.hostname or "",
            port=parsed.port or (1080 if "socks" in scheme else 8080),
            username=parsed.username,
            password=parsed.password,
        )

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
    timeout: int = 25
    retries: int = 2  # one initial attempt + two retries = 3 tries total
    proxy: Optional[RequestProxyConfig] = None
    # backoff_factor: float = 0.1 # not possible. Default value: 0.5. https://github.com/encode/httpx/discussions/1895

    @classmethod
    def with_proxy(
        cls,
        proxy: str | RequestProxyConfig | None = None,
        timeout: int = 25,
        retries: int = 2,
    ) -> "RequestConfig":
        """Factory accepting URL string or pre-built RequestProxyConfig."""
        proxy_cfg = (
            RequestProxyConfig.from_url(proxy)
            if isinstance(proxy, str)
            else proxy
        )
        return cls(timeout=timeout, retries=retries, proxy=proxy_cfg)

