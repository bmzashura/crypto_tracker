"""
CoinGecko API Service untuk CryptoTracker BMZ.
Semua request ke CoinGecko dilakukan melalui modul ini.
Mendukung in-memory cache dan error handling terstruktur.
"""
import logging
from typing import Any, Literal, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.coingecko.com/api/v3"
HEADERS = {}

# Singleton session — menggunakan satu TCP connection untuk efisien
_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Dapatkan atau buat ulang requests session (tanpa menyimpan API key di headers)."""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def _build_headers(api_key: str) -> dict:
    """Build headers per-request. API key tidak disimpan di session global."""
    headers = {"Accept": "application/json", "User-Agent": "CryptoTracker-UAS/1.0"}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
    return headers


# ─── Custom Exceptions ─────────────────────────────────────────

class CoinGeckoServiceError(Exception):
    """Base exception untuk semua error dari CoinGecko service."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class CoinGeckoTimeout(CoinGeckoServiceError):
    """Request timeout."""
    pass


class CoinGeckoRateLimit(CoinGeckoServiceError):
    """HTTP 429 — Rate limit exceeded."""
    pass


class CoinGeckoAPIError(CoinGeckoServiceError):
    """HTTP 4xx/5xx error dari API."""
    pass


class CoinGeckoDataError(CoinGeckoServiceError):
    """Data tidak sesuai schema yang diharapkan."""
    pass


# ─── Internal Helpers ─────────────────────────────────────────

def _get(api_key: str, url: str, params: dict, timeout: int) -> dict:
    """
    Helper internal untuk melakukan GET request ke CoinGecko.
    Headers dibuat per-request, API key tidak disimpan di session global.
    """
    session = _get_session()
    headers = _build_headers(api_key)
    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout as e:
        logger.warning("CoinGecko timeout: %s params=%s", url, params)
        raise CoinGeckoTimeout(f"Request timeout untuk {url}", status_code=None) from e
    except requests.exceptions.ConnectionError as e:
        logger.warning("CoinGecko connection error: %s", e)
        raise CoinGeckoServiceError(f"Koneksi gagal: {e}", status_code=None) from e
    except requests.exceptions.RequestException as e:
        logger.error("CoinGecko request error: %s", e)
        raise CoinGeckoServiceError(str(e), status_code=None) from e

    if response.status_code == 429:
        logger.warning("CoinGecko rate limit hit")
        raise CoinGeckoRateLimit("Rate limit tercapai. Coba lagi nanti.", status_code=429)
    elif response.status_code >= 500:
        logger.warning("CoinGecko server error: %d", response.status_code)
        raise CoinGeckoAPIError(
            f"CoinGecko server error: {response.status_code}",
            status_code=response.status_code,
        )
    elif response.status_code >= 400:
        logger.warning("CoinGecko API error: %d body=%s", response.status_code, response.text[:200])
        raise CoinGeckoAPIError(
            f"CoinGecko API error: {response.status_code}",
            status_code=response.status_code,
        )

    try:
        return response.json()
    except ValueError as e:
        logger.error("Invalid JSON from CoinGecko: %s", e)
        raise CoinGeckoDataError(f"Response bukan JSON valid: {e}") from e


def _get_with_fallback(api_keys: list[str], url: str, params: dict, timeout: int) -> dict:
    """
    Coba semua API keys secara berurutan. Gagal rate limit → coba key berikutnya.
    Semua key gagal → lempar exception terakhir. Tidak pernah log API key.
    """
    for key in api_keys:
        try:
            return _get(key, url, params, timeout)
        except CoinGeckoRateLimit:
            logger.info("API key rate-limited, trying next key...")
            continue
        except CoinGeckoServiceError:
            raise  # Non-rate-limit errors — don't try other keys

    # Semua key rate-limited
    raise CoinGeckoRateLimit("Semua API key mengalami rate limit. Coba lagi nanti.", status_code=429)


# ─── Public API Functions ──────────────────────────────────────

def fetch_coins(
    api_key: str,
    timeout: int,
    per_page: int = 20,
    page: int = 1,
    vs_currency: str = "usd",
    order: str = "market_cap_desc",
    api_keys: list = None,
) -> list[dict]:
    """Ambil daftar koin dari CoinGecko /coins/markets."""
    keys = api_keys or [api_key]
    params = {
        "vs_currency": vs_currency,
        "order": order,
        "per_page": min(per_page, 50),   # Max 50 per request
        "page": max(page, 1),
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    data = _get_with_fallback(keys, f"{BASE_URL}/coins/markets", params, timeout)
    if not isinstance(data, list):
        raise CoinGeckoDataError(f"Unexpected response type: {type(data)}")
    return data


def fetch_coin_detail(api_key: str, timeout: int, coin_id: str, api_keys: list = None) -> dict:
    """Ambil detail satu koin dari CoinGecko /coins/{id}."""
    keys = api_keys or [api_key]
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    data = _get_with_fallback(keys, f"{BASE_URL}/coins/{coin_id}", params, timeout)
    if not isinstance(data, dict):
        raise CoinGeckoDataError(f"Unexpected response type for coin {coin_id}")
    return data


def fetch_price_history(
    api_key: str,
    timeout: int,
    coin_id: str,
    days: Literal[7, 30, 90] = 7,
    api_keys: list = None,
) -> dict:
    """Ambil data harga historis dari CoinGecko /coins/{id}/market_chart."""
    keys = api_keys or [api_key]
    params = {
        "vs_currency": "usd",
        "days": days,
    }
    data = _get_with_fallback(keys, f"{BASE_URL}/coins/{coin_id}/market_chart", params, timeout)
    if not isinstance(data, dict) or "prices" not in data:
        raise CoinGeckoDataError(f"Invalid market_chart response for {coin_id}")
    return data


def fetch_market_by_ids(
    api_key: str,
    timeout: int,
    coin_ids: list[str],
    vs_currency: str = "usd",
    api_keys: list = None,
) -> list[dict]:
    """Ambil market data untuk beberapa coin IDs sekaligus."""
    keys = api_keys or [api_key]
    if not coin_ids:
        return []
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(coin_ids[:50]),   # Max 50 IDs per request
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    data = _get_with_fallback(keys, f"{BASE_URL}/coins/markets", params, timeout)
    if not isinstance(data, list):
        raise CoinGeckoDataError(f"Unexpected response type for market by ids")
    return data


def fetch_search(api_key: str, timeout: int, query: str, api_keys: list = None) -> list[dict]:
    """Cari koin berdasarkan nama dari CoinGecko /search."""
    keys = api_keys or [api_key]
    params = {"query": query}
    data = _get_with_fallback(keys, f"{BASE_URL}/search", params, timeout)
    if not isinstance(data, dict) or "coins" not in data:
        raise CoinGeckoDataError(f"Invalid search response")
    return data.get("coins", [])[:20]   # Max 20 hasil


def fetch_trending(api_key: str, timeout: int, api_keys: list = None) -> list[dict]:
    """Ambil 7 koin trending dari CoinGecko /search/trending."""
    keys = api_keys or [api_key]
    params = {}
    data = _get_with_fallback(keys, f"{BASE_URL}/search/trending", params, timeout)
    if not isinstance(data, dict) or "coins" not in data:
        raise CoinGeckoDataError(f"Invalid trending response")
    coins = data.get("coins", [])
    return [c.get("item", {}) for c in coins[:7]]


def fetch_global_stats(api_key: str, timeout: int, api_keys: list = None) -> dict:
    """Ambil statistik pasar global dari CoinGecko /global."""
    keys = api_keys or [api_key]
    data = _get_with_fallback(keys, f"{BASE_URL}/global", {}, timeout)
    if not isinstance(data, dict) or "data" not in data:
        raise CoinGeckoDataError(f"Invalid global response")
    return data.get("data", {})
