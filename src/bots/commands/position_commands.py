"""Position management commands for Discord bot."""
import logging
from typing import Dict, Optional

import discord
from discord import app_commands, Interaction, Embed, Color
from discord.ext import commands

from src.bots.utils.position_utils import (
    close_user_position,
    create_position_from_chart_data,
    get_position_details,
    get_user_positions_summary,
    list_user_positions,
    stop_user_position,
    update_user_position,
)
from src.positions.models import PlatformType, PositionType

logger = logging.getLogger(__name__)


class PositionCommands(commands.Cog):
    """Commands for managing trading positions."""

    def __init__(self, bot):
        self.bot = bot
        
        # Create the position command group
        self.position_group = app_commands.Group(
            name="position",
            description="Trading position management commands",
            guild_ids=None  # This will use the same guild_ids as defined in bot setup
        )
        
        # Add the command group to the bot's command tree
        self.bot.tree.add_command(self.position_group)
        
        # Setup all position commands
        self.setup_commands()
        
        logger.info("Position commands group initialized")
    
    def setup_commands(self):
        """Register all commands to the position command group."""
        
        @self.position_group.command(name="list", description="List your active positions")
        async def positions(interaction: Interaction):
            """List the user's active positions."""
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            
            positions_text = await list_user_positions(user_id, PlatformType.DISCORD)
            
            await interaction.followup.send(positions_text, ephemeral=True)

        @self.position_group.command(name="details", description="Get details of a position")
        @app_commands.describe(position_id="The ID of the position")
        async def position_details(interaction: Interaction, position_id: str):
            """Get details of a specific position."""
            await interaction.response.defer(ephemeral=True)
            
            position_text = await get_position_details(position_id)
            
            await interaction.followup.send(position_text, ephemeral=True)

        @self.position_group.command(name="close", description="Close a position")
        @app_commands.describe(position_id="The ID of the position to close")
        async def close_position(interaction: Interaction, position_id: str):
            """Close a position."""
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            
            result = await close_user_position(position_id, user_id, PlatformType.DISCORD)
            
            await interaction.followup.send(result, ephemeral=True)

        @self.position_group.command(name="update", description="Update a position")
        @app_commands.describe(
            position_id="The ID of the position to update",
            entry_price="New entry price",
            take_profit="New take profit",
            stop_loss="New stop loss",
            notes="Notes about the position",
        )
        async def update_position(
            interaction: Interaction,
            position_id: str,
            entry_price: Optional[float] = None,
            take_profit: Optional[float] = None,
            stop_loss: Optional[float] = None,
            notes: Optional[str] = None,
        ):
            """Update a position."""
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            
            update_data = {}
            if entry_price is not None:
                update_data["entry_price"] = entry_price
            if take_profit is not None:
                update_data["take_profit"] = take_profit
            if stop_loss is not None:
                update_data["stop_loss"] = stop_loss
            if notes is not None:
                update_data["notes"] = notes
                
            if not update_data:
                await interaction.followup.send("No updates provided.", ephemeral=True)
                return
                
            result = await update_user_position(position_id, user_id, PlatformType.DISCORD, update_data)
            
            await interaction.followup.send(result, ephemeral=True)

        @self.position_group.command(name="stop", description="Stop tracking a position")
        @app_commands.describe(position_id="The ID of the position to stop tracking")
        async def stop_position(interaction: Interaction, position_id: str):
            """Stop tracking a position (soft-delete)."""
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            
            result = await stop_user_position(position_id, user_id, PlatformType.DISCORD)
            
            await interaction.followup.send(result, ephemeral=True)

        @self.position_group.command(name="summary", description="Get a summary of your positions")
        async def summary(interaction: Interaction):
            """Get a summary of the user's positions."""
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            
            summary_text = await get_user_positions_summary(user_id, PlatformType.DISCORD)
            
            await interaction.followup.send(summary_text, ephemeral=True)

        @self.position_group.command(name="create", description="Create a new position")
        @app_commands.describe(
            symbol="Trading pair symbol (e.g., BTCUSDT)",
            position_type="Type of position",
            entry_price="Entry price",
            take_profit="Take profit price (optional)",
            stop_loss="Stop loss price (optional)",
            notes="Notes about the position (optional)",
        )
        @app_commands.choices(
            position_type=[
                app_commands.Choice(name="Long", value="long"),
                app_commands.Choice(name="Short", value="short"),
            ]
        )
        async def create_position(
            interaction: Interaction,
            symbol: str,
            position_type: str,
            entry_price: float,
            take_profit: Optional[float] = None,
            stop_loss: Optional[float] = None,
            notes: Optional[str] = None,
        ):
            """Create a new position manually."""
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            
            chart_data = {
                "symbol": symbol.upper(),
                "entry": entry_price,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "position_type": position_type,
                "notes": notes,
            }
            
            position = await create_position_from_chart_data(
                user_id, PlatformType.DISCORD, chart_data
            )
            
            if position:
                await interaction.followup.send(
                    f"Position created successfully!\n\n{await get_position_details(str(position.id))}",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Failed to create position. Please try again later.",
                    ephemeral=True,
                )
        
        @self.position_group.command(name="help", description="Get help with position management")
        async def help_command(interaction: Interaction):
            """Display help information for position management."""
            embed = Embed(
                title="Position Management - Trading Positions Tracker",
                description="I can help you track and manage your trading positions.",
                color=Color.green()
            )

            embed.add_field(
                name="📋 Position List",
                value="Use `/position list` to see all your active positions.",
                inline=False
            )

            embed.add_field(
                name="➕ Create Position",
                value="Use `/position create` to manually create a new position.",
                inline=False
            )

            embed.add_field(
                name="📊 Position Details",
                value="Use `/position details <position_id>` to see details about a specific position.",
                inline=False
            )

            embed.add_field(
                name="✏️ Update Position",
                value="Use `/position update <position_id>` to modify an existing position.",
                inline=False
            )

            embed.add_field(
                name="✅ Close Position",
                value="Use `/position close <position_id>` to close a position.",
                inline=False
            )

            embed.add_field(
                name="⏹️ Stop Tracking",
                value="Use `/position stop <position_id>` to stop tracking a position.",
                inline=False
            )

            embed.add_field(
                name="📑 Position Summary",
                value="Use `/position summary` to get statistics about your positions.",
                inline=False
            )

            embed.set_footer(text="Positions are also created automatically when you share chart images.")

            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Add a listener to detect chart images and automatically create positions
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages with chart images and extract position data."""
        # Skip messages from bots
        if message.author.bot:
            return
            
        # Check if the message has attachments
        if not message.attachments:
            return
            
        # Check if any attachment is an image
        image_attachments = [
            a for a in message.attachments
            if a.content_type and a.content_type.startswith("image/")
        ]
        
        if not image_attachments:
            return
            
        # Process the first image attachment
        image_attachment = image_attachments[0]
        
        # Here you would call your chart analysis function to extract data
        # For demonstration purposes, we'll use a mock example
        
        # This is where you would analyze the chart image
        # chart_data = await analyze_chart_image(image_attachment.url)
        
        # For now, we'll use mock data
        chart_data = {
            "symbol": "BTCUSDT",
            "entry": 50000,
            "take_profit": 55000,
            "stop_loss": 48000,
            "position_type": "long",
        }
        
        # Create a position from the chart data
        user_id = str(message.author.id)
        position = await create_position_from_chart_data(
            user_id, PlatformType.DISCORD, chart_data
        )
        
        if position:
            # Send a message to the channel
            await message.channel.send(
                f"Position detected from chart! Created for {message.author.mention}.\n"
                f"Use `/position details {position.id}` to see details."
            )


async def setup(bot):
    """Add the position commands to the bot."""
    await bot.add_cog(PositionCommands(bot))
