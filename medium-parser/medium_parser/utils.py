import difflib
import hashlib
import re
import secrets
import string
import urllib.parse
from datetime import datetime
from functools import lru_cache
from urllib.parse import parse_qs, urlparse

import aiohttp
import tld
from aiohttp_retry import RetryClient
from async_lru import alru_cache
from bs4 import BeautifulSoup
from loguru import logger

from medium_parser import exceptions, retry_options

DEFAULT_URL_PROTOCOL = "https://"

VALID_ID_CHARS = set(string.ascii_letters + string.digits)

KNOWN_MEDIUM_CUSTOM_DOMAINS = (
    "javascript.plainenglish.io",
    "blog.llamaindex.ai",
    "code.likeagirl.io",
    "medium.datadriveninvestor.com",
    "blog.det.life",
    "python.plainenglish.io",
    "blog.stackademic.com",
    "ai.gopubby.com",
    "blog.devops.dev",
    "levelup.gitconnected.com",
    "betterhumans.coach.me",
    "ai.plainenglish.io",
)
KNOWN_MEDIUM_DOMAINS = (
    "medium.com",
    "uxplanet.org",
    "osintteam.blog",
    "ahmedelfakharany.com",
    "drlee.io",
    "artificialcorner.com",
    "generativeai.pub",
    "productcoalition.com",
    "towardsdev.com",
    "infosecwriteups.com",
    "towardsdatascience.com",
    "thetaoist.online",
    "devopsquare.com",
    "laceydearie.com",
    "bettermarketing.pub",
    "itnext.io",
    "eand.co",
    "betterprogramming.pub",
    "curiouse.co",
    "betterhumans.pub",
    "uxdesign.cc",
    "thebolditalic.com",
    "arcdigital.media",
    "codeburst.io",
    "psiloveyou.xyz",
    "writingcooperative.com",
    "entrepreneurshandbook.co",
    "prototypr.io",
    "theascent.pub",
    "storiusmag.com",
)
NOT_MEDIUM_DOMAINS = (
    "github.com",
    "yandex.ru",
    "yandex.kz",
    "youtube.com",
    "nytimes.com",
    "wsj.com",
    "reddit.com",
    "elpais.com",
    "forbes.com",
    "bloomberg.com",
    "lesechos.fr",
    "otz.de",
    "businessinsider.com",
    "buff.ly",
    "delish.com",
    "economist.com",
    "wired.com",
    "rollingstone.com",
)


def is_valid_url(url):
    """
    Check if the given URL is valid by verifying if it has a valid scheme and netloc.

    Parameters:
        url (str): The URL to be validated.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    fld = get_fld(url)
    if not fld:
        return False

    parsed_url = urlparse(url)
    return bool(parsed_url.scheme and parsed_url.netloc)


def getting_percontage_of_match(string: str, matched_string: str) -> float:
    if string is None or matched_string is None:
        return 0.0

    return difflib.SequenceMatcher(None, string, matched_string).ratio() * 100


def generate_random_sha256_hash():
    # Encode the input string to bytes before hashing
    random_input_bytes = secrets.token_bytes()
    # Create the SHA-256 hash object
    sha256_hash = hashlib.sha256()
    # Update the hash object with the input bytes
    sha256_hash.update(random_input_bytes)
    # Get the hexadecimal representation of the hash
    sha256_hex = sha256_hash.hexdigest()
    return sha256_hex


def get_unix_ms() -> int:
    # Get the current date and time
    current_date_time = datetime.now()

    # Convert to the number of milliseconds since January 1, 1970 (Unix Epoch time)
    milliseconds_since_epoch = int(current_date_time.timestamp() * 1000)

    return milliseconds_since_epoch


def unquerify_url(url: str) -> str:
    """
    Sanitizes a URL by removing all query parameters.

    Args:
        url: The URL to sanitize.

    Returns:
        A sanitized URL.
    """

    parsed_url = urllib.parse.urlparse(url)
    query = parsed_url.query
    if query:
        parsed_url = parsed_url._replace(query="")

    sanitized_url = urllib.parse.urlunparse(parsed_url)
    return sanitized_url.removesuffix("/")


@lru_cache(maxsize=500)
def un_wwwify(url: str):
    # TODO: enhanced type checks
    if url.startswith("www."):
        return url.removeprefix("www.")
    return url


def correct_url(url: str) -> str:
    # Workaround for Safari bug. We don't known by what condition this happens, but sometimes we get
    # some broken URL, for example like "", and all of them based on user-agent comes from Safari browser engine,
    # from some kinda different platforms like Windows, and that's strange bcz does Windows has Safari browser? lmao

    # TODO: fix

    # unsafari_url = re.sub(r"https?://", DEFAULT_URL_PROTOCOL, url)
    # logger.debug(f"Is URL broken by Safari bug: {unsafari_url != url}")

    unsafari_url = url

    unquerified_url = unquerify_url(unsafari_url)
    logger.debug(f"Is URL has query data: {unquerified_url != unsafari_url}")

    unplaginated_url = unplaginate_url(unquerified_url)
    logger.debug(f"Is URL has plagination: {unplaginated_url != unquerified_url}")

    # parsed_url = urlparse(url)
    # if not bool(parsed_url.netloc and parsed_url.scheme):
    #     return DEFAULT_PROTOCOL + url

    # if not re.match(r'http[s]?://', url):
    #     url = DEFAULT_PROTOCOL + url

    return url


def unplaginate_url(url):
    """
    Removes page plaginations from URL
    """
    sanitized_url = url.removesuffix("/page/2")
    return sanitized_url.removesuffix("/")


@lru_cache(maxsize=100)
def is_has_valid_medium_post_id(hex_string: str) -> bool:
    return extract_hex_string(hex_string) is not None


@lru_cache(maxsize=100)
def basic_hex_check(hex_string: str) -> bool:
    # Check if the string is a valid hexadecimal string
    for char in hex_string:
        if char not in VALID_ID_CHARS:
            return False

    # Unfortunately, this logic doesn't works correctly sometimes, because
    # there is some unique URLs that are has only digits, like this:
    # https://valeman.medium.com/python-vs-r-for-time-series-forecasting-395390432598

    # Check if the string contains only lowercase hexadecimal characters
    # if not hex_string.islower():
    #     return False

    # Check if the length of the string is correct for a hexadecimal string (e.g., 10, 11 or 12 characters)
    if len(hex_string) not in range(8, 12 + 1):
        return False

    return True


@lru_cache(maxsize=100)
def extract_hex_string(input_string: str) -> str:
    # First try to find a hexadecimal string preceded by a '-'
    match = re.findall(r"-(\b[a-fA-F0-9]{8,12}\b)", input_string)
    if not match:
        # If no match, try to find a hexadecimal string without the '-'
        match = re.findall(r"(\b[a-fA-F0-9]{8,12}\b)", input_string)
    return match[-1] if match else None


async def resolve_medium_short_link(short_url_id: str, timeout: int = 5) -> str:
    async with aiohttp.ClientSession() as session:
        retry_client = RetryClient(
            client_session=session, raise_for_status=False, retry_options=retry_options
        )
        request = await retry_client.get(
            f"https://rsci.app.link/{short_url_id}",
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
            },
            allow_redirects=False,
        )
        post_url = request.headers["Location"]

    return post_url


@alru_cache(maxsize=500)
async def resolve_medium_url(url: str, timeout: int = 5) -> str:
    logger.debug(f"Trying resolve {url=}, with {timeout=}")
    parsed_url = urlparse(url)
    parsed_netloc = un_wwwify(parsed_url.netloc)

    if parsed_url.path.startswith("/p/"):
        logger.debug("URL is Medium 'mobile' link")
        post_id = parsed_url.path.rsplit("/p/")[1]

    elif parsed_netloc == "l.facebook.com" and parsed_url.path.startswith("/l.php"):
        logger.debug("URL seems like is Facebook redirect (tracking) link")

        parsed_query = parse_qs(parsed_url.query)
        if parsed_query.get("u") and len(parsed_query["u"]) == 1:
            post_url = parsed_query["u"][0]
            return await resolve_medium_url(post_url)

        logger.debug("...but we get fucked up...")
        return False

    elif (
        parsed_netloc == "webcache.googleusercontent.com"
        and parsed_url.path.startswith("/search")
    ):
        logger.debug("URL seems like is Google Web Archive page link")

        parsed_query = parse_qs(parsed_url.query)
        if parsed_query.get("q") and len(parsed_query["q"]) == 1:
            post_url = parsed_query["q"][0].removeprefix("cache:")
            return await resolve_medium_url(post_url)

        logger.debug("...but we get fucked up...")
        return False

    elif parsed_netloc == "google.com" and parsed_url.path.startswith("/url"):
        logger.debug("URL seems like is Google redirect (tracking) link")

        parsed_query = parse_qs(parsed_url.query)
        if parsed_query.get("url") and len(parsed_query["url"]) == 1:
            logger.debug("..and we got 'url' passed param. Make resolve them....")
            post_url = parsed_query["url"][0]
            return await resolve_medium_url(post_url)
        elif parsed_query.get("q") and len(parsed_query["q"]) == 1:
            logger.debug("..and we got 'q' passed param. Make resolve them....")
            post_url = parsed_query["q"][0]
            return await resolve_medium_url(post_url)

        logger.debug("...but we get fucked up...")
        return False

    elif parsed_netloc == "12ft.io":
        logger.debug("URL seems like is from our partner named 12ft.io")

        parsed_query = parse_qs(parsed_url.query)
        if parsed_query.get("q") and len(parsed_query["q"]) == 1:
            logger.debug("..and we got 'q' passed param. Make resolve them....")
            post_url = parsed_query["q"][0]
            return await resolve_medium_url(post_url)

        logger.debug("...but we get fucked up...")
        return False

    elif parsed_url.path.startswith("/m/global-identity-2"):
        logger.debug(
            "URL seems like is Medium redirect (tracking) link. Possibly from email subscription"
        )

        parsed_query = parse_qs(parsed_url.query)
        if parsed_query.get("redirectUrl") and len(parsed_query["redirectUrl"]) == 1:
            logger.debug(
                "..and we got 'redirectUrl' passed param. Make resolve them...."
            )
            post_url = parsed_query["redirectUrl"][0]
            return await resolve_medium_url(post_url)

        logger.debug("...but we get fucked up...")
        return False

    elif parsed_netloc == "link.medium.com":
        logger.debug(
            "URL seems like is Medium short (SHORT) redirect (tracking) link. Make resolve them..."
        )
        short_url_id = parsed_url.path.removeprefix("/")
        post_url = await resolve_medium_short_link(short_url_id, timeout)
        return await resolve_medium_url(post_url)

    else:
        logger.debug(
            "We can't determine the URL type. Let's just try to extract the post_id..."
        )
        post_url = parsed_url.path.split("/")[-1]
        post_id = post_url.split("-")[-1]

    if not is_has_valid_medium_post_id(post_id):
        logger.warning(f"...but hoops, that's invalid post_id: {post_id}")
        return False

    return post_id


async def resolve_medium_url_old(url: str, timeout: int = 5) -> str:
    async with aiohttp.ClientSession() as session:
        retry_client = RetryClient(
            client_session=session, raise_for_status=False, retry_options=retry_options
        )
        request = await retry_client.get(url, timeout=timeout)
        response = await request.text()

    soup = BeautifulSoup(response, "html.parser")
    type_meta_tag = soup.head.find("meta", property="og:type")
    if not type_meta_tag or type_meta_tag.get("content") != "article":
        return False

    url_meta_tag = soup.head.find("meta", property="al:android:url")
    if not url_meta_tag or not url_meta_tag.get("content"):
        return False

    parsed_url = urlparse(url_meta_tag["content"])
    path = parsed_url.path.strip("/")
    parsed_value = path.split("/")[-1]
    return parsed_value


async def is_valid_medium_url_old(url: str, timeout: int = 5):
    async with aiohttp.ClientSession() as session:
        retry_client = RetryClient(
            client_session=session, raise_for_status=False, retry_options=retry_options
        )

        try:
            request = await retry_client.get(url, timeout=timeout)
        except Exception as ex:
            raise exceptions.PageLoadingError(ex) from ex

        response = await request.text()

    soup = BeautifulSoup(response, "html.parser")

    if not soup.head:
        return False

    site_name_meta_tag = soup.head.find("meta", property="og:site_name")

    if not site_name_meta_tag or site_name_meta_tag.get("content") != "Medium":
        return False

    return True


@lru_cache(maxsize=500)
def get_fld(url: str):
    try:
        fld = tld.get_fld(url)
    except Exception as ex:
        logger.trace(ex)
        return None
    else:
        return fld


@alru_cache(maxsize=100)
async def is_valid_medium_url(url: str) -> bool:
    """
    Check if the url is a valid Medium article page

    Check if the domain is in the known Medium domains and subdomains list. If the doman/subdomain is in the list, then the url is valid
    """
    domain = get_fld(url)
    parsed_url = urlparse(url)
    domain_netloc = un_wwwify(parsed_url.netloc)

    # TODO: http://freedium.cfd/https://www.google.com.vn/url?sa=i&url=https%3A%2F%2Fmedium.com%2F%40dugguRK%2Fabout-android-hardware-abstraction-layer-hal-5d191dafeb2c&psig=AOvVaw17KP0U_haPMmhAByeMTxSg&ust=1711354113283000&source=images&cd=vfe&opi=89978449&ved=0CBQQjhxqFwoTCMCM_oG5jIUDFQAAAAAdAAAAABAa

    if domain in ["12ft.io", "google.com", "facebook.com", "googleusercontent.com"]:
        return True

    if domain in NOT_MEDIUM_DOMAINS or domain_netloc in NOT_MEDIUM_DOMAINS:
        raise exceptions.NotValidMediumURL("100% not valid Medium URL")

    if domain in KNOWN_MEDIUM_DOMAINS or domain_netloc in KNOWN_MEDIUM_CUSTOM_DOMAINS:
        return True

    logger.warning(f"url '{url}' wasn't detected in known Medium domains")

    # XXX: Unfourtunately, for now we don't know ALL Medium's domains, so we need resolve links
    resolve_result = bool(await resolve_medium_url(url))

    # send_message(f"We found that {domain=}, {domain_netloc=} is not listed in out known Medium database.\nURL: {url}")

    return resolve_result

    # return False
