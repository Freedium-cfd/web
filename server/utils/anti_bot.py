from loguru import logger


bot_signatures = {
    "facebookexternalhit",
    "/apple-touch-icon",
    "Googlebot",
    "AdsBot-Google",
    "Google-Adwords-Instant",
    "Apache-HttpClient",
    "SafeDNSBot",
    "RevueBot",
    "MetaURI API",
    "redback/v",
    "Slackbot",
    "HTTP_Request2/",
    "python-requests/",
    "LightspeedSystemsCrawler/",
    "CipaCrawler/",
    "Twitterbot/",
    "Go-http-client/",
    "/cheese_service",
    "undici",
    "database",
    "node-fetch",
    "Java/",
    "axios/",
    "okhttp/",
    "go-resty/",
    "Faraday v",
    "curl/",
}


def filter_bots(details: str) -> bool:
    is_bot = any(bot_signature in details for bot_signature in bot_signatures)
    logger.debug(f"{details} is a bot: {is_bot}")
    return is_bot
