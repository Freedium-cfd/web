"""Tests for centralized WARP proxy resolution and proxy config parsing."""
from __future__ import annotations

import pytest

from freedium_library.utils.http.client.config import RequestConfig, RequestProxyConfig
from freedium_library.utils.http.proxy import get_warp_proxy, get_warp_proxy_config


class TestRequestProxyConfigFromUrl:
    def test_parses_socks5_url(self):
        cfg = RequestProxyConfig.from_url("socks5://haproxy-pb:1080")
        assert cfg is not None
        assert cfg.type == "socks5"
        assert cfg.host == "haproxy-pb"
        assert cfg.port == 1080
        assert cfg.url == "socks5://haproxy-pb:1080"

    def test_parses_socks5h_as_socks5(self):
        cfg = RequestProxyConfig.from_url("socks5h://haproxy-pb:1080")
        assert cfg is not None
        assert cfg.type == "socks5"
        assert cfg.host == "haproxy-pb"
        assert cfg.port == 1080

    def test_parses_http_and_https_urls(self):
        cfg_http = RequestProxyConfig.from_url("http://127.0.0.1:8080")
        assert cfg_http is not None
        assert cfg_http.type == "http"
        assert cfg_http.host == "127.0.0.1"
        assert cfg_http.port == 8080

        cfg_https = RequestProxyConfig.from_url("https://proxy.example.com:8443")
        assert cfg_https is not None
        assert cfg_https.type == "https"
        assert cfg_https.host == "proxy.example.com"
        assert cfg_https.port == 8443

    def test_parses_credentials(self):
        cfg = RequestProxyConfig.from_url("socks5://user:pass@127.0.0.1:1080")
        assert cfg is not None
        assert cfg.username == "user"
        assert cfg.password == "pass"
        assert cfg.url == "socks5://user:pass@127.0.0.1:1080"

    def test_empty_or_none_returns_none(self):
        assert RequestProxyConfig.from_url(None) is None
        assert RequestProxyConfig.from_url("") is None
        assert RequestProxyConfig.from_url("   ") is None

    def test_unsupported_scheme_returns_none(self):
        assert RequestProxyConfig.from_url("ftp://example.com:21") is None


class TestRequestConfigWithProxy:
    def test_with_proxy_string(self):
        cfg = RequestConfig.with_proxy("socks5://haproxy-pb:1080")
        assert cfg.proxy is not None
        assert cfg.proxy.host == "haproxy-pb"
        assert cfg.proxy.port == 1080

    def test_with_proxy_config_instance(self):
        proxy_cfg = RequestProxyConfig(type="socks5", host="proxy", port=1080)
        cfg = RequestConfig.with_proxy(proxy_cfg)
        assert cfg.proxy == proxy_cfg

    def test_with_none_proxy(self):
        cfg = RequestConfig.with_proxy(None)
        assert cfg.proxy is None


class TestGetWarpProxy:
    def test_prefers_warp_proxy_balancer(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WARP_PROXY_BALANCER", "socks5://warp-new:1080")
        monkeypatch.setenv("PROXY_LIST", "socks5://old:1080")
        assert get_warp_proxy() == "socks5://warp-new:1080"

    def test_falls_back_to_proxy_list(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("WARP_PROXY_BALANCER", raising=False)
        monkeypatch.setenv("PROXY_LIST", "socks5://haproxy-pb:1080,socks5://backup:1080")
        assert get_warp_proxy() == "socks5://haproxy-pb:1080"

    def test_returns_none_when_both_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("WARP_PROXY_BALANCER", raising=False)
        monkeypatch.delenv("PROXY_LIST", raising=False)
        assert get_warp_proxy() is None

    def test_get_warp_proxy_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WARP_PROXY_BALANCER", "socks5://haproxy-pb:1080")
        cfg = get_warp_proxy_config()
        assert cfg is not None
        assert cfg.host == "haproxy-pb"
        assert cfg.port == 1080
