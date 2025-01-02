import os
from typing import Optional

import httpx
import pytest
from bs4 import BeautifulSoup
from loguru import logger


def check_medium_meta_tag(domain: str) -> Optional[bool]:
    url = f"https://{domain}"
    logger.info(f"Checking Medium meta tag for domain: {domain}")

    try:
        with httpx.Client(timeout=10.0) as client:
            logger.debug(f"Sending GET request to {url}")
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            meta_tag = soup.find(
                "meta",
                {"property": "al:android:package", "content": "com.medium.reader"},
            )

            if meta_tag is not None:
                logger.success(f"Medium meta tag found for domain: {domain}")
                return True
            else:
                logger.warning(f"No Medium meta tag found for domain: {domain}")
                return False

    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error(f"Error checking {domain}: {str(e)}")
        return None


def get_domains_from_file(filepath: str) -> list[str]:
    logger.info(f"Reading domains from file: {filepath}")
    with open(filepath, "r") as file:
        domains = [line.strip() for line in file if line.strip()]
    logger.debug(f"Loaded {len(domains)} domains from file")
    return domains


def get_file_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "../", filename)


@pytest.mark.integration
@pytest.mark.parametrize(
    "domain",
    get_domains_from_file(get_file_path("medium_domains.txt")),
)
def test_medium_domain_meta_tag(domain: str):
    logger.info(f"Starting test for domain: {domain}")
    result = check_medium_meta_tag(domain)
    assert result is not None, f"Failed to check domain {domain}"
    assert result is True, f"Domain {domain} does not have Medium meta tag"
    logger.success(f"Test passed for domain: {domain}")


@pytest.mark.integration
@pytest.mark.parametrize(
    "domain",
    get_domains_from_file(get_file_path("non_active_medium_domains.txt")),
)
def test_non_active_medium_domain(domain: str):
    logger.info(f"Starting test for non-active domain: {domain}")
    result = check_medium_meta_tag(domain)
    assert (
        result is False or result is None
    ), f"Domain {domain} should be non-active but appears to be active"
    logger.success(f"Test passed for non-active domain: {domain}")
