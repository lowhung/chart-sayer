"""
TradingView chart rendering functionality for Discord bot.
"""
import logging
import urllib.parse
from io import BytesIO
from typing import List, Optional

import discord
from discord import Embed, Color

logger = logging.getLogger(__name__)

# Color schemes for TradingView charts
CHART_COLOR_SCHEMES = {
    "light": "light",
    "dark": "dark",
    "colored": "colored",
}

# Timeframes for TradingView charts
CHART_TIMEFRAMES = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "1d": "D",
    "1w": "W",
    "1M": "M",
}

# TA indicators for TradingView charts
CHART_INDICATORS = {
    "volume": "Volume@tv-basicstudies",
    "macd": "MACD@tv-basicstudies",
    "rsi": "RSI@tv-basicstudies",
    "bollinger_bands": "BB@tv-basicstudies",
    "moving_average": "MA@tv-basicstudies",
    "ema": "EMA@tv-basicstudies",
    "stochastic": "Stochastic@tv-basicstudies",
    "ichimoku_cloud": "IchimokuCloud@tv-basicstudies",
    "atr": "ATR@tv-basicstudies",
    "awesome_oscillator": "AwesomeOscillator@tv-basicstudies",
    "parabolic_sar": "PSAR@tv-basicstudies",
    "pivot_points": "PivotPointsStandard@tv-basicstudies",
    "fibonacci": "FibonacciRetracement@tv-basicstudies",
}


async def generate_tradingview_url(
        symbol: str,
        timeframe: str = "1d",
        theme: str = "dark",
        indicators: Optional[List[str]] = None,
        width: int = 800,
        height: int = 500,
) -> str:
    """
    Generate a TradingView chart URL for the given symbol and parameters.
    
    Args:
        symbol: The trading pair symbol (e.g., BTCUSDT)
        timeframe: Chart timeframe (default: "1d")
        theme: Chart theme/color scheme (default: "dark")
        indicators: List of TA indicators to include
        width: Chart width in pixels
        height: Chart height in pixels
        
    Returns:
        TradingView chart URL
    """
    # Normalize the symbol
    if ":" not in symbol:
        # Add default exchange for common crypto
        if symbol.endswith("USD") or symbol.endswith("USDT") or symbol.endswith("USDC"):
            symbol = f"BINANCE:{symbol}"
        # Add default exchange for common stocks
        elif symbol.isalpha():
            symbol = f"NASDAQ:{symbol}"

    # Get the timeframe code
    tf_code = CHART_TIMEFRAMES.get(timeframe, "D")

    # Get the theme
    chart_theme = CHART_COLOR_SCHEMES.get(theme, "dark")

    # Base URL for the TradingView widget
    base_url = "https://s.tradingview.com/widgetembed/"

    # Parameters for the TradingView widget
    params = {
        "symbol": symbol,
        "interval": tf_code,
        "hidesidetoolbar": "1",
        "symboledit": "1",
        "saveimage": "1",
        "toolbarbg": "f1f3f6",
        "studies": ",".join([CHART_INDICATORS.get(ind, ind) for ind in (indicators or [])]),
        "theme": chart_theme,
        "style": "1",
        "timezone": "Etc/UTC",
        "withdateranges": "1",
        "hideideas": "1",
        "width": str(width),
        "height": str(height),
    }

    # Encode parameters
    encoded_params = urllib.parse.urlencode(params)

    # Generate the final URL
    final_url = f"{base_url}?{encoded_params}"

    return final_url


async def create_tradingview_embed(
        symbol: str,
        timeframe: str = "1d",
        theme: str = "dark",
        indicators: Optional[List[str]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        width: int = 800,
        height: int = 500,
) -> Embed:
    """
    Create a Discord embed for a TradingView chart.
    
    Args:
        symbol: The trading pair symbol (e.g., BTCUSDT)
        timeframe: Chart timeframe (default: "1d")
        theme: Chart theme/color scheme (default: "dark")
        indicators: List of TA indicators to include
        title: Embed title (default: symbol + timeframe)
        description: Embed description
        width: Chart width in pixels
        height: Chart height in pixels
        
    Returns:
        Discord embed with TradingView chart URL
    """
    # Generate the TradingView URL
    tv_url = await generate_tradingview_url(
        symbol=symbol,
        timeframe=timeframe,
        theme=theme,
        indicators=indicators,
        width=width,
        height=height,
    )

    # Create default title if not provided
    if not title:
        title = f"{symbol} ({timeframe.upper()}) Chart"

    # Create embed
    embed = Embed(
        title=title,
        description=description or "Click the link below to view the interactive chart on TradingView:",
        color=Color.blue() if theme == "light" else Color.darker_grey(),
        url=tv_url,
    )

    # Add TradingView logo and credit
    embed.set_footer(
        text="Powered by TradingView",
        icon_url="https://static.tradingview.com/static/images/favicon.ico",
    )

    # Add URL to the embed
    embed.add_field(
        name="Interactive Chart",
        value=f"[Open in TradingView]({tv_url})",
        inline=False,
    )

    return embed


async def render_tradingview_image(
        symbol: str,
        timeframe: str = "1d",
        theme: str = "dark",
        indicators: Optional[List[str]] = None,
        width: int = 800,
        height: int = 500,
) -> Optional[BytesIO]:
    """
    Render a TradingView chart as an image and return it as a BytesIO object.
    
    This is a more advanced feature that requires a headless browser or other
    screenshot capability, which is complex to implement in this context.
    
    For now, this is a placeholder that would need third-party services 
    or more complex browser automation to implement fully.
    
    Args:
        symbol: The trading pair symbol (e.g., BTCUSDT)
        timeframe: Chart timeframe (default: "1d")
        theme: Chart theme/color scheme (default: "dark")
        indicators: List of TA indicators to include
        width: Chart width in pixels
        height: Chart height in pixels
        
    Returns:
        BytesIO object containing the rendered chart image, or None if rendering failed
    """
    # This would require a more complex implementation with browser automation
    # or a third-party service to render the chart as an image
    return None


async def send_tradingview_chart(
        interaction: discord.Interaction,
        symbol: str,
        timeframe: str = "1d",
        theme: str = "dark",
        indicators: Optional[List[str]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        width: int = 800,
        height: int = 500,
) -> None:
    """
    Send a TradingView chart embed to a Discord channel.
    
    Args:
        interaction: Discord interaction
        symbol: The trading pair symbol (e.g., BTCUSDT)
        timeframe: Chart timeframe (default: "1d")
        theme: Chart theme/color scheme (default: "dark")
        indicators: List of TA indicators to include
        title: Embed title (default: symbol + timeframe)
        description: Embed description
        width: Chart width in pixels
        height: Chart height in pixels
    """
    try:
        # Create the embed
        embed = await create_tradingview_embed(
            symbol=symbol,
            timeframe=timeframe,
            theme=theme,
            indicators=indicators,
            title=title,
            description=description,
            width=width,
            height=height,
        )

        # Send the embed
        await interaction.followup.send(embed=embed)

        logger.info(f"Sent TradingView chart for {symbol} ({timeframe}) to Discord")
    except Exception as e:
        logger.error(f"Error sending TradingView chart: {e}")
        await interaction.followup.send(
            "Error generating TradingView chart. Please try again.",
            ephemeral=True,
        )
