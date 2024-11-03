from urllib.parse import urlparse, urlunparse


class URLProcessor:
    """A class for processing and sanitizing URLs."""

    @staticmethod
    def un_wwwify(url: str) -> str:
        """Remove 'www.' prefix from URLs while preserving URL structure.

        Args:
            url: The URL string to process

        Returns:
            str: URL with 'www.' prefix removed if present, otherwise unchanged

        Raises:
            TypeError: If url is not a string
            ValueError: If url is empty or malformed
        """
        if not isinstance(url, str):
            raise TypeError("url must be a string")

        if not url:
            raise ValueError("url must not be empty")

        try:
            parsed = urlparse(url)
            netloc = parsed.netloc or parsed.path

            if netloc.startswith("www."):
                netloc = netloc[4:]

            if parsed.netloc:
                return urlunparse(parsed._replace(netloc=netloc))
            elif parsed.path:
                return urlunparse(parsed._replace(path=netloc))

            return netloc
        except Exception as e:
            raise ValueError(f"Invalid URL format: {str(e)}")

    @staticmethod
    def unquerify_url(url: str) -> str:
        """Sanitizes a URL by removing all query parameters.

        Args:
            url: The URL to sanitize.

        Returns:
            str: A sanitized URL without query parameters and trailing slash.
        """
        parsed_url = urlparse(url)
        query = parsed_url.query
        if query:
            parsed_url = parsed_url._replace(query="")

        sanitized_url = urlunparse(parsed_url)
        return sanitized_url.removesuffix("/")
