from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

SITEMAP_URL = "https://mybasic.pl/sitemap.xml"
BASE_URL = "https://mybasic.pl"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 10


class ProductImageFetcher:
    def __init__(self):
        self._url_cache: dict[str, str] = {}
        self._cache_time: datetime | None = None

    def _is_cache_valid(self) -> bool:
        if not self._cache_time:
            return False
        return datetime.now() - self._cache_time < timedelta(hours=CACHE_TTL_HOURS)

    def load_sitemap(self) -> None:
        try:
            response = requests.get(SITEMAP_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to load sitemap: %s", e)
            return

        urls = re.findall(r"https://mybasic\.pl/p/[^<]+", response.text)

        for url in urls:
            match = re.search(r"-([a-z]{2}\d{3,5}[a-z0-9]*)$", url)
            if match:
                model = match.group(1)[:5].upper()
                if model not in self._url_cache:
                    self._url_cache[model] = url

        self._cache_time = datetime.now()

    def find_product_url(self, model: str) -> str | None:
        if not self._is_cache_valid():
            self.load_sitemap()

        model_key = model[:5].upper()
        return self._url_cache.get(model_key)

    def fetch_image_url(self, product_url: str) -> str | None:
        try:
            response = requests.get(product_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to fetch product page: %s", e)
            return None

        match = re.search(
            r"https://shopware-storage\.s3\.eu-central-1\.amazonaws\.com/media/[^\"'<>\s]+\.(jpg|png|webp)",
            response.text,
        )
        if match:
            return match.group(0)

        return None


_fetcher: ProductImageFetcher | None = None


def get_fetcher() -> ProductImageFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = ProductImageFetcher()
    return _fetcher


def get_product_image_and_url(model: str) -> tuple[str | None, str | None]:
    fetcher = get_fetcher()
    product_url = fetcher.find_product_url(model)
    if not product_url:
        return None, None
    image_url = fetcher.fetch_image_url(product_url)
    return image_url, product_url
