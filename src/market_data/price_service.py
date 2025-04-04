"""
Market data service for fetching real-time price information.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# CoinMarketCap API Key
CMC_API_KEY = os.getenv("CMC_API_KEY", "")

# Default cache TTL in seconds (5 minutes)
DEFAULT_CACHE_TTL = 300

# Price cache
_price_cache = {}
_last_update_time = {}


async def get_crypto_price(
    symbol: str, convert: str = "USD", max_age_seconds: int = DEFAULT_CACHE_TTL
) -> Optional[Dict]:
    """
    Get real-time price data for a cryptocurrency.

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, XRP)
        convert: Currency to convert to (default: USD)
        max_age_seconds: Maximum age of cached data in seconds

    Returns:
        Dictionary with price data, or None if not found
    """
    # Normalize symbol
    symbol = symbol.upper().strip()

    # Remove common suffixes for better matching
    for suffix in ["USD", "USDT", "USDC", "BUSD"]:
        if symbol.endswith(suffix) and len(symbol) > len(suffix):
            symbol = symbol[: -len(suffix)]
            break

    # Check cache first
    cache_key = f"{symbol}:{convert}"
    now = time.time()

    if (
        cache_key in _price_cache
        and cache_key in _last_update_time
        and now - _last_update_time[cache_key] < max_age_seconds
    ):
        logger.debug(f"Using cached price data for {symbol}")
        return _price_cache[cache_key]

    # If no API key, return mock data for development
    if not CMC_API_KEY:
        logger.warning("No CoinMarketCap API key found, using mock data")
        mock_data = _get_mock_price_data(symbol, convert)
        _price_cache[cache_key] = mock_data
        _last_update_time[cache_key] = now
        return mock_data

    try:
        # Fetch from CoinMarketCap API
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

        params = {"symbol": symbol, "convert": convert}

        headers = {
            "X-CMC_PRO_API_KEY": CMC_API_KEY,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error fetching price data: {error_text}")
                    return None

                data = await response.json()

                if "data" not in data or symbol not in data["data"]:
                    logger.error(f"Symbol {symbol} not found in response")
                    return None

                # Extract relevant price data
                crypto_data = data["data"][symbol]
                quote_data = crypto_data["quote"][convert]

                result = {
                    "symbol": crypto_data["symbol"],
                    "name": crypto_data["name"],
                    "price": quote_data["price"],
                    "percent_change_1h": quote_data["percent_change_1h"],
                    "percent_change_24h": quote_data["percent_change_24h"],
                    "percent_change_7d": quote_data["percent_change_7d"],
                    "market_cap": quote_data["market_cap"],
                    "volume_24h": quote_data["volume_24h"],
                    "last_updated": quote_data["last_updated"],
                    "currency": convert,
                }

                # Update cache
                _price_cache[cache_key] = result
                _last_update_time[cache_key] = now

                return result
    except Exception as e:
        logger.error(f"Error fetching price data: {e}")
        return None


async def get_multiple_crypto_prices(
    symbols: List[str], convert: str = "USD", max_age_seconds: int = DEFAULT_CACHE_TTL
) -> Dict[str, Dict]:
    """
    Get real-time price data for multiple cryptocurrencies.

    Args:
        symbols: List of cryptocurrency symbols
        convert: Currency to convert to (default: USD)
        max_age_seconds: Maximum age of cached data in seconds

    Returns:
        Dictionary mapping symbols to price data
    """
    normalized_symbols = [s.upper().strip() for s in symbols]

    # If no API key, return mock data for development
    if not CMC_API_KEY:
        logger.warning("No CoinMarketCap API key found, using mock data for multiple symbols")
        result = {}
        now = time.time()

        for symbol in normalized_symbols:
            cache_key = f"{symbol}:{convert}"
            mock_data = _get_mock_price_data(symbol, convert)
            _price_cache[cache_key] = mock_data
            _last_update_time[cache_key] = now
            result[symbol] = mock_data

        return result

    try:
        # Check which symbols we need to fetch
        symbols_to_fetch = []
        result = {}
        now = time.time()

        for symbol in normalized_symbols:
            cache_key = f"{symbol}:{convert}"

            if (
                cache_key in _price_cache
                and cache_key in _last_update_time
                and now - _last_update_time[cache_key] < max_age_seconds
            ):
                # Use cached data
                result[symbol] = _price_cache[cache_key]
            else:
                # Need to fetch this symbol
                symbols_to_fetch.append(symbol)

        if not symbols_to_fetch:
            # All symbols were in cache
            return result

        # Fetch from CoinMarketCap API
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

        params = {"symbol": ",".join(symbols_to_fetch), "convert": convert}

        headers = {
            "X-CMC_PRO_API_KEY": CMC_API_KEY,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error fetching multiple price data: {error_text}")

                    # Return what we have from cache
                    return result

                data = await response.json()

                if "data" not in data:
                    logger.error("No data in response for multiple symbols")
                    return result

                # Process each symbol in the response
                for symbol in symbols_to_fetch:
                    if symbol not in data["data"]:
                        logger.warning(f"Symbol {symbol} not found in API response")
                        continue

                    crypto_data = data["data"][symbol]
                    quote_data = crypto_data["quote"][convert]

                    symbol_result = {
                        "symbol": crypto_data["symbol"],
                        "name": crypto_data["name"],
                        "price": quote_data["price"],
                        "percent_change_1h": quote_data["percent_change_1h"],
                        "percent_change_24h": quote_data["percent_change_24h"],
                        "percent_change_7d": quote_data["percent_change_7d"],
                        "market_cap": quote_data["market_cap"],
                        "volume_24h": quote_data["volume_24h"],
                        "last_updated": quote_data["last_updated"],
                        "currency": convert,
                    }

                    # Update cache and result
                    cache_key = f"{symbol}:{convert}"
                    _price_cache[cache_key] = symbol_result
                    _last_update_time[cache_key] = now
                    result[symbol] = symbol_result

                return result
    except Exception as e:
        logger.error(f"Error fetching multiple price data: {e}")
        return result  # Return whatever we have from cache


async def get_price_by_symbol(symbol: str, convert: str = "USD") -> Tuple[Optional[float], str]:
    """
    Get the current price for a symbol (simplified version returning just the price).

    Args:
        symbol: Trading symbol (e.g., BTC, ETH, BTCUSDT)
        convert: Currency to convert to (default: USD)

    Returns:
        Tuple of (price, currency) or (None, currency) if not found
    """
    price_data = await get_crypto_price(symbol, convert)

    if price_data and "price" in price_data:
        return price_data["price"], price_data["currency"]

    return None, convert


def _get_mock_price_data(symbol: str, convert: str) -> Dict:
    """
    Get mock price data for development when no API key is available.

    Args:
        symbol: Cryptocurrency symbol
        convert: Currency to convert to

    Returns:
        Mock price data dictionary
    """
    import random
    from datetime import datetime

    # Common cryptocurrencies with realistic price ranges
    mock_prices = {
        "BTC": (35000, 45000),
        "ETH": (1800, 2400),
        "XRP": (0.4, 0.7),
        "SOL": (80, 150),
        "ADA": (0.3, 0.5),
        "DOGE": (0.05, 0.15),
        "DOT": (5, 15),
        "MATIC": (0.5, 1.5),
        "LTC": (50, 100),
        "LINK": (10, 20),
    }

    # Use default range for unknown symbols
    price_range = mock_prices.get(symbol, (1, 100))
    base_price = random.uniform(*price_range)

    return {
        "symbol": symbol,
        "name": f"{symbol} Coin",
        "price": base_price,
        "percent_change_1h": random.uniform(-5, 5),
        "percent_change_24h": random.uniform(-10, 10),
        "percent_change_7d": random.uniform(-20, 20),
        "market_cap": base_price * random.uniform(1000000, 100000000),
        "volume_24h": base_price * random.uniform(100000, 10000000),
        "last_updated": datetime.utcnow().isoformat(),
        "currency": convert,
    }


def clear_price_cache():
    """Clear the price cache."""
    global _price_cache, _last_update_time
    _price_cache.clear()
    _last_update_time.clear()
    logger.info("Price cache cleared")
