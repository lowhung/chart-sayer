"""Price commands for Discord bot."""
import logging
from typing import Dict, Optional, List

import discord
from discord import app_commands, Interaction, Embed, Color
from discord.ext import commands

from src.market_data.price_service import get_crypto_price, get_multiple_crypto_prices

logger = logging.getLogger(__name__)


class PriceCommands(commands.Cog):
    """Commands for fetching real-time price data."""

    def __init__(self, bot):
        self.bot = bot
        
        # Create the price command group
        self.price_group = app_commands.Group(
            name="price",
            description="Cryptocurrency price commands",
            guild_ids=None  # This will use the same guild_ids as defined in bot setup
        )
        
        # Add the command group to the bot's command tree
        self.bot.tree.add_command(self.price_group)
        
        # Setup all price commands
        self.setup_commands()
        
        logger.info("Price commands group initialized")
    
    def setup_commands(self):
        """Register all commands to the price command group."""
        
        @self.price_group.command(name="check", description="Get current price of a cryptocurrency")
        @app_commands.describe(
            symbol="Cryptocurrency symbol (e.g., BTC, ETH)",
            currency="Currency to convert to (default: USD)"
        )
        async def price_check(interaction: Interaction, symbol: str, currency: str = "USD"):
            """Get the current price of a cryptocurrency."""
            await interaction.response.defer()
            
            try:
                price_data = await get_crypto_price(symbol, currency)
                
                if not price_data:
                    await interaction.followup.send(
                        f"Could not find price data for {symbol}. Please check the symbol and try again.",
                        ephemeral=True
                    )
                    return
                
                # Format the price with appropriate decimal places
                price = price_data['price']
                if price < 0.01:
                    formatted_price = f"{price:.8f}"
                elif price < 1:
                    formatted_price = f"{price:.6f}"
                elif price < 1000:
                    formatted_price = f"{price:.4f}"
                else:
                    formatted_price = f"{price:,.2f}"
                
                # Create embed with price information
                embed = Embed(
                    title=f"{price_data['name']} ({price_data['symbol']})",
                    description=f"Current price information",
                    color=Color.blue() if price_data['percent_change_24h'] >= 0 else Color.red()
                )
                
                # Add price field
                embed.add_field(
                    name="Price",
                    value=f"{formatted_price} {price_data['currency']}",
                    inline=False
                )
                
                # Add price changes
                embed.add_field(
                    name="1 Hour Change",
                    value=f"{price_data['percent_change_1h']:.2f}%",
                    inline=True
                )
                
                embed.add_field(
                    name="24 Hour Change",
                    value=f"{price_data['percent_change_24h']:.2f}%",
                    inline=True
                )
                
                embed.add_field(
                    name="7 Day Change",
                    value=f"{price_data['percent_change_7d']:.2f}%",
                    inline=True
                )
                
                # Add market data
                embed.add_field(
                    name="Market Cap",
                    value=f"{price_data['market_cap']:,.0f} {price_data['currency']}",
                    inline=True
                )
                
                embed.add_field(
                    name="24h Volume",
                    value=f"{price_data['volume_24h']:,.0f} {price_data['currency']}",
                    inline=True
                )
                
                # Add last updated timestamp
                embed.set_footer(text=f"Last Updated: {price_data['last_updated']}")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error checking price: {e}")
                await interaction.followup.send(
                    "Error fetching price data. Please try again later.",
                    ephemeral=True
                )
        
        @self.price_group.command(name="multi", description="Get prices for multiple cryptocurrencies")
        @app_commands.describe(
            symbols="Comma-separated list of cryptocurrency symbols (e.g., BTC,ETH,XRP)",
            currency="Currency to convert to (default: USD)"
        )
        async def multi_price(interaction: Interaction, symbols: str, currency: str = "USD"):
            """Get prices for multiple cryptocurrencies at once."""
            await interaction.response.defer()
            
            # Parse the symbols
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            
            if not symbol_list:
                await interaction.followup.send(
                    "Please provide at least one cryptocurrency symbol.",
                    ephemeral=True
                )
                return
            
            try:
                price_data = await get_multiple_crypto_prices(symbol_list, currency)
                
                if not price_data:
                    await interaction.followup.send(
                        "Could not find price data for any of the provided symbols.",
                        ephemeral=True
                    )
                    return
                
                # Create embed with price information
                embed = Embed(
                    title="Cryptocurrency Prices",
                    description=f"Current prices in {currency}",
                    color=Color.blue()
                )
                
                # Add each cryptocurrency to the embed
                for symbol, data in price_data.items():
                    if not data:
                        continue
                    
                    # Format the price with appropriate decimal places
                    price = data['price']
                    if price < 0.01:
                        formatted_price = f"{price:.8f}"
                    elif price < 1:
                        formatted_price = f"{price:.6f}"
                    elif price < 1000:
                        formatted_price = f"{price:.4f}"
                    else:
                        formatted_price = f"{price:,.2f}"
                    
                    # Format 24h change with color indicator
                    change_24h = data['percent_change_24h']
                    change_text = f"{change_24h:.2f}%"
                    if change_24h >= 0:
                        change_text = f"▲ {change_text}"
                    else:
                        change_text = f"▼ {change_text}"
                    
                    embed.add_field(
                        name=f"{data['name']} ({data['symbol']})",
                        value=f"**Price:** {formatted_price} {currency}\n**24h:** {change_text}",
                        inline=True
                    )
                
                embed.set_footer(text=f"Last Updated: {data['last_updated']}")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error checking multiple prices: {e}")
                await interaction.followup.send(
                    "Error fetching price data. Please try again later.",
                    ephemeral=True
                )
                
        @self.price_group.command(name="help", description="Get help with price commands")
        async def price_help(interaction: Interaction):
            """Display help for price commands."""
            embed = Embed(
                title="Price Commands - Cryptocurrency Price Tracker",
                description="Get real-time cryptocurrency prices directly in Discord.",
                color=Color.gold()
            )
            
            embed.add_field(
                name="📊 Check Price",
                value="Use `/price check <symbol>` to get detailed information about a specific cryptocurrency.",
                inline=False
            )
            
            embed.add_field(
                name="📈 Multiple Prices",
                value="Use `/price multi <symbols>` to check multiple cryptocurrencies at once. Separate symbols with commas, e.g., `BTC,ETH,XRP`.",
                inline=False
            )
            
            embed.add_field(
                name="💱 Currency Conversion",
                value="Add a currency parameter to any price command to convert to a different currency, e.g., `/price check BTC EUR`.",
                inline=False
            )
            
            embed.set_footer(text="Powered by CoinMarketCap")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Add the price commands to the bot."""
    await bot.add_cog(PriceCommands(bot))
