#!/usr/bin/env python3
"""
freedium_sitemap_poster.py

Download and parse the Medium sitemap index (default: /tmp/medium_sitemap.xml),
iterate each nested sitemap and POST/GET each discovered URL to a freedium endpoint.

Features:
- Loads sitemap index from local file or from a remote URL
- Recursively parses sitemapindex or urlset structures
- Extracts path component of each URL and sends GET request to https://freedium.cfd{path}
- Accepts --limit to limit number of processed URLs
- Optional --dry-run to only print the URLs without making requests
"""

from __future__ import annotations

import argparse
import sys
import os
import xml.etree.ElementTree as ET
from typing import Generator
from urllib.parse import urlparse
import threading

# Optional dependency; fallback to urllib if requests not available
try:
    import requests
except Exception:
    requests = None

# Optional curl_cffi for browser-like HTTP impersonation
try:
    import curl_cffi
except Exception:
    curl_cffi = None

# For gzipped sitemap support
import gzip

SITEMAP_NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


class SitemapProcessor:
    def __init__(self, session=None, verbose: bool = False, sitemap_ua: str = None, destination_ua: str = None, impersonate: str = None):
        self.session = session
        self.verbose = verbose
        self.sitemap_ua = sitemap_ua
        self.destination_ua = destination_ua
        self.impersonate = impersonate

        # Build headers for fetching sitemaps and contacting destination to mimic a browser
        self.sitemap_headers = {
            'User-Agent': sitemap_ua or 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://medium.com',
        }

        self.destination_headers = {
            'User-Agent': destination_ua or 'freedium-sitemap-poster/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def _log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def fetch_url(self, url: str, for_sitemap: bool = False, impersonate: str | None = None, timeout: int = 30, no_wait: bool = False):
        """Fetch a URL and return (status_code, content bytes).

        Prefer curl_cffi for TLS/browser impersonation,fall back to requests/urllib.
        """
        headers = self.sitemap_headers if for_sitemap else self.destination_headers

        # 1) curl_cffi
        if curl_cffi is not None:
            try:
                imp = impersonate or 'chrome136'
                if no_wait:
                    # No-wait: fire and forget by launching a thread that calls curl_cffi.get and discards body
                    def _bg_call():
                        try:
                            curl_cffi.get(url, impersonate=imp, headers=headers, timeout=timeout)
                        except Exception as e:
                            self._log(f"curl_cffi fire-and-forget for {url} failed: {e}")
                    threading.Thread(target=_bg_call, daemon=True).start()
                    return 0, b''
                r = curl_cffi.get(url, impersonate=imp, headers=headers, timeout=timeout)
                # curl_cffi Response-like
                status = getattr(r, 'status_code', getattr(r, 'status', None))
                content = getattr(r, 'content', None)
                if status is None:
                    # try to infer from r.status
                    status = getattr(r, 'status', None)
                if content is None:
                    # fallback to r.text encoded
                    text = getattr(r, 'text', None)
                    content = text.encode() if text else b''
                return status, content
            except Exception as e:
                self._log(f"curl_cffi failed for {url}: {e}")

        # 2) requests
        if requests is not None and self.session is not None:
            try:
                if no_wait:
                    # requests does not support non-blocking easily; launch a thread with a simple get
                    def _bg_call():
                        try:
                            self.session.get(url, timeout=timeout, headers=headers)
                        except Exception as e:
                            self._log(f"requests fire-and-forget for {url} failed: {e}")
                    threading.Thread(target=_bg_call, daemon=True).start()
                    return 0, b''
                r = self.session.get(url, timeout=timeout, headers=headers)
                r.raise_for_status()
                return r.status_code, r.content
            except Exception as e:
                self._log(f"requests failed for {url}: {e}")

        # 3) urllib fallback
        try:
            import urllib.request
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status = r.getcode()
                content = r.read()
            return status, content
        except Exception as e:
            self._log(f"urllib failed for {url}: {e}")
            return None, None

    def parse_local_sitemap_file(self, file_path: str) -> Generator[str, None, None]:
        """Yield sitemap URLs (locs) from a local sitemap file which can be sitemapindex or urlset."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        tree = ET.parse(file_path)
        root = tree.getroot()
        local_name = root.tag.rpartition('}')[-1]
        if local_name == 'sitemapindex':
            for sitemap in root.findall('s:sitemap', SITEMAP_NS):
                loc_el = sitemap.find('s:loc', SITEMAP_NS)
                if loc_el is not None and loc_el.text:
                    yield loc_el.text.strip()
        elif local_name == 'urlset':
            for url in root.findall('s:url', SITEMAP_NS):
                loc_el = url.find('s:loc', SITEMAP_NS)
                if loc_el is not None and loc_el.text:
                    yield loc_el.text.strip()
        else:
            raise ValueError(f"Unexpected root element {root.tag}")

    def _xml_root_from_bytes(self, content: bytes) -> ET.Element:
        """Parse XML bytes, handling gz compression if needed."""
        try:
            root = ET.fromstring(content)
            return root
        except ET.ParseError:
            # try gzip
            try:
                decompressed = gzip.decompress(content)
                root = ET.fromstring(decompressed)
                return root
            except Exception as e:
                raise

    def parse_sitemap_url(self, sitemap_url: str) -> Generator[str, None, None]:
        """Fetch a remote sitemap url and yield content locs (or nested sitemaps).

        Will try the following in order:
        1. curl_cffi (if available) with impersonation
        2. requests
        3. urllib.request fallback
        """
        self._log(f"Fetching sitemap: {sitemap_url}")

        # 1) curl_cffi
        if curl_cffi is not None:
            try:
                # curl_cffi provides a simple get API
                r = curl_cffi.get(sitemap_url, impersonate='chrome136', headers=self.sitemap_headers, timeout=30)
                # r is a curl_cffi Response-like object; access r.content
                content = r.content
                self._log("Fetched sitemap via curl_cffi")
            except Exception:
                content = None
        else:
            content = None

        # If nothing fetched yet, try a unified fetch method which prefers curl_cffi
        if content is None:
            status, content = self.fetch_url(sitemap_url, for_sitemap=True, impersonate=self.impersonate, timeout=30)
            if content is not None:
                self._log(f"Fetched sitemap via fetch_url (status {status})")

        # If after all methods content is still None, raise
        if content is None:
            raise Exception("Failed to fetch sitemap via all methods")


        root = self._xml_root_from_bytes(content)
        local_name = root.tag.rpartition('}')[-1]

        if local_name == 'sitemapindex':
            for sitemap in root.findall('s:sitemap', SITEMAP_NS):
                loc_el = sitemap.find('s:loc', SITEMAP_NS)
                if loc_el is not None and loc_el.text:
                    yield loc_el.text.strip()
        elif local_name == 'urlset':
            for url_el in root.findall('s:url', SITEMAP_NS):
                loc_el = url_el.find('s:loc', SITEMAP_NS)
                if loc_el is not None and loc_el.text:
                    yield loc_el.text.strip()
        else:
            # unknown type
            self._log(f"Unknown sitemap root: {root.tag}")
            return


def main():
    parser = argparse.ArgumentParser(description='Fetch Medium sitemap and call freedium.cfd for each URL (path only).')
    parser.add_argument('--sitemap-url', default='https://medium.com/sitemap/sitemap.xml', help='Remote sitemap index URL')
    parser.add_argument('--sitemap-file', default='/tmp/medium_sitemap.xml', help='Local sitemap index filename (downloaded if not present)')
    parser.add_argument('--destination', default='https://freedium.cfd', help='Base destination to call (path appended)')
    parser.add_argument('--limit', '-n', type=int, default=0, help='Maximum number of URLs to process, 0 for unlimited')
    parser.add_argument('--dry-run', action='store_true', help='Do not make network requests, only print URLs')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--sitemap-ua', default='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', help='User-Agent for fetching sitemaps (browser UA)')
    parser.add_argument('--destination-ua', default='freedium-sitemap-poster/1.0', help='User-Agent for contacting destination (freedium)')
    parser.add_argument('--impersonate', default='chrome136', help='Impersonation profile for curl_cffi (e.g., chrome136)')
    parser.add_argument('--no-wait', action='store_true', help='Fire-and-forget; do not wait for the response body from freedium')
    args = parser.parse_args()

    # Prepare requests session or urllib fallback
    session = None
    if requests is not None:
        session = requests.Session()
        session.headers.update({'User-Agent': 'freedium-sitemap-poster/1.0'})

    proc = SitemapProcessor(session=session, verbose=args.verbose, sitemap_ua=args.sitemap_ua, destination_ua=args.destination_ua, impersonate=args.impersonate)
    impersonate = args.impersonate

    # Ensure we have the sitemap index file locally
    if not os.path.exists(args.sitemap_file):
        if args.verbose:
            print(f"Downloading sitemap index from {args.sitemap_url} -> {args.sitemap_file}")
        if requests is None:
            import urllib.request
            with urllib.request.urlopen(args.sitemap_url) as r:
                content = r.read()
            with open(args.sitemap_file, 'wb') as f:
                f.write(content)
        else:
            r = session.get(args.sitemap_url, timeout=30)
            r.raise_for_status()
            with open(args.sitemap_file, 'wb') as f:
                f.write(r.content)
    else:
        if args.verbose:
            print(f"Using existing local sitemap file: {args.sitemap_file}")

    # Parse the sitemap file for nested sitemaps
    try:
        sitemap_urls = list(proc.parse_local_sitemap_file(args.sitemap_file))
    except Exception as e:
        print(f"Error parsing local sitemap file {args.sitemap_file}: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(sitemap_urls)} sitemap URLs in index.")

    processed = 0
    seen_paths = set()

    # iterate each sitemap url and parse
    for sitemap_url in sitemap_urls:
        try:
            # The sitemap_url might be a urlset or a sitemapindex; parse_sitemap_url yields either nested sitemaps or content urls
            for content_loc in proc.parse_sitemap_url(sitemap_url):
                # get path only
                parsed = urlparse(content_loc)
                path = parsed.path or ''
                if not path:
                    # skip weird URLs with no path
                    continue
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                dest = args.destination.rstrip('/') + path
                if args.dry_run:
                    print(dest)
                else:
                    # perform GET with proc.fetch_url
                    try:
                        status, body = proc.fetch_url(dest, for_sitemap=False, impersonate=proc.impersonate, timeout=15, no_wait=args.no_wait)
                        if args.no_wait:
                            print(f"GET {dest} -> FIRED")
                        elif status is None or body is None:
                            print(f"GET {dest} -> FAILED")
                        else:
                            print(f"GET {dest} -> {status} ({len(body)} bytes)")
                    except Exception as e:
                        print(f"Error requesting {dest}: {e}", file=sys.stderr)

                processed += 1
                if args.limit > 0 and processed >= args.limit:
                    print(f"Reached limit {args.limit}. Processed {processed} items.")
                    return
        except Exception as e:
            print(f"Failed to process sitemap {sitemap_url}: {e}", file=sys.stderr)

    print(f"Done. Processed {processed} items.")


if __name__ == '__main__':
    main()
