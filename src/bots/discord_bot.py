import asyncio
import json
import logging
import os

import aiohttp
from discord import app_commands, Intents, Interaction, Attachment, Object, Embed, Color
from discord.ext import commands
from dotenv import load_dotenv
from fastapi import Request

from src.bots.discord_ui import SetupMenuView
from src.bots.chart_rendering.tradingview import send_tradingview_chart, CHART_TIMEFRAMES, CHART_INDICATORS
from src.image_processing.openai_integration import process_chart_with_gpt4o

logger = logging.getLogger(__name__)

bot_ready = asyncio.Event()
shutdown_event = asyncio.Event()
running_tasks = set()

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
application_id = os.getenv('DISCORD_CLIENT_ID')
test_guild_id = os.getenv('DISCORD_TEST_GUILD_ID')

guild_ids = [int(test_guild_id)] if test_guild_id else None

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


def create_tracked_task(coro):
    """Create a task and add it to our set of tracked tasks."""
    task = asyncio.create_task(coro)
    running_tasks.add(task)
    task.add_done_callback(running_tasks.discard)
    return task


class ChartSayerCog(commands.Cog, name="Chart Sayer"):
    def __init__(self, core_bot: commands.Bot):
        self.bot = core_bot

        self.chart_group = app_commands.Group(
            name="chart",
            description="Chart analysis commands",
            guild_ids=guild_ids
        )
        self.admin_group = app_commands.Group(
            name="admin",
            description="Admin commands",
            guild_ids=guild_ids
        )

        self.bot.tree.add_command(self.chart_group)
        self.bot.tree.add_command(self.admin_group)
        self.user_configs = {}
        self.setup_commands()

    def setup_commands(self):
        """Register all commands to the command group"""

        @self.chart_group.command(name="start", description="Start the Chart Sayer bot")
        async def start(interaction: Interaction):
            await interaction.response.send_message('Hello! I am your Chart Sayer bot.')

        @self.chart_group.command(name="help", description="Get help with chart analysis")
        async def help_command(interaction: Interaction):
            embed = Embed(
                title="Chart Sayer - Trading Chart Analysis Bot",
                description="I can analyze trading charts to identify key price levels and trading opportunities.",
                color=Color.blue()
            )

            embed.add_field(
                name="📈 Chart Analysis",
                value="Use `/chart analyze` and attach a chart image to get entry, stop loss, and take profit levels automatically identified.",
                inline=False
            )

            embed.add_field(
                name="📊 TradingView Charts",
                value="Use `/chart tradingview <symbol>` to display an interactive TradingView chart with custom timeframes and indicators.",
                inline=False
            )

            embed.add_field(
                name="⚙️ Custom Settings",
                value="Use `/chart setup` to customize how I analyze your charts, including colors for entry/exit points and which indicators to prioritize.",
                inline=False
            )

            embed.add_field(
                name="📊 Supported Chart Types",
                value="I can analyze most standard trading charts including candlestick, line, and bar charts from any platform.",
                inline=False
            )

            embed.add_field(
                name="🔍 Example Usage",
                value="1. Take a screenshot of your chart\n2. Use `/chart analyze` and upload the image\n3. Receive entry, stop loss, and take profit levels",
                inline=False
            )

            embed.set_footer(text="For more detailed help, visit our documentation or contact the bot administrator.")

            await interaction.response.send_message(embed=embed)

        @self.chart_group.command(name="analyze", description="Analyze a chart image")
        async def analyze(interaction: Interaction, file: Attachment):
            if not file.content_type or not file.content_type.startswith('image/'):
                await interaction.response.send_message(
                    "Please upload an image file. This doesn't appear to be an image."
                )
                return

            await interaction.response.defer(thinking=True)

            try:
                image_path = f"/tmp/{file.filename}"
                await file.save(image_path)

                user_id = str(interaction.user.id)
                config_path = "src/config/chart_config.json"

                if user_id in self.user_configs:
                    result = process_chart_with_gpt4o(image_path, config_path, user_config=self.user_configs[user_id])
                else:
                    result = process_chart_with_gpt4o(image_path, config_path)

                await interaction.followup.send(f"Analysis Result: {result}")

            except Exception as e:
                logger.error(f"Error processing image: {e}")
                await interaction.followup.send(
                    "Sorry, I encountered an error analyzing your chart. Please try again."
                )

        @self.chart_group.command(name="setup", description="Customize chart analysis settings")
        async def setup(interaction: Interaction):
            """Start the setup process for chart analysis configuration"""
            config_path = "src/config/chart_config.json"
            with open(config_path, 'r') as file:
                default_config = json.load(file)

            user_id = str(interaction.user.id)
            if user_id not in self.user_configs:
                self.user_configs[user_id] = default_config.copy()

            view = SetupMenuView(self, user_id)
            await interaction.response.send_message(
                "Welcome to Chart Sayer Setup! Select an option to configure:",
                view=view,
                ephemeral=True
            )
            
        @self.chart_group.command(name="tradingview", description="Display a TradingView chart")
        @app_commands.describe(
            symbol="Trading pair symbol (e.g., BTCUSDT)",
            timeframe="Chart timeframe (default: 1d)",
            theme="Chart theme/color scheme (default: dark)",
            indicators="Comma-separated list of indicators (e.g., volume,rsi,macd)",
        )
        @app_commands.choices(
            timeframe=[
                app_commands.Choice(name=k.upper(), value=k) 
                for k in CHART_TIMEFRAMES.keys()
            ],
            theme=[
                app_commands.Choice(name="Dark", value="dark"),
                app_commands.Choice(name="Light", value="light"),
                app_commands.Choice(name="Colored", value="colored"),
            ]
        )
        async def tradingview(interaction: Interaction, 
                           symbol: str,
                           timeframe: str = "1d",
                           theme: str = "dark",
                           indicators: str = ""):
            """Display a TradingView chart for a symbol."""
            await interaction.response.defer()
            
            # Parse indicators list
            indicator_list = [i.strip() for i in indicators.split(",")] if indicators else []
            # Filter out invalid indicators
            indicator_list = [ind for ind in indicator_list if ind in CHART_INDICATORS]
            
            await send_tradingview_chart(
                interaction=interaction,
                symbol=symbol,
                timeframe=timeframe,
                theme=theme,
                indicators=indicator_list,
            )

        @self.admin_group.command(name="resync", description="Resync application commands")
        async def resync(interaction: Interaction):
            """Resynchronizes application commands with Discord."""
            await interaction.response.send_message("Re-syncing application commands...")

            try:
                if guild_ids:
                    for guild_id in guild_ids:
                        guild = Object(id=guild_id)
                        await self.bot.tree.sync(guild=guild)
                        await interaction.edit_original_response(content=f"Command sync complete for guild {guild_id}")
                else:
                    await self.bot.tree.sync()
                    await interaction.edit_original_response(content="Global command sync complete")

                await interaction.edit_original_response(content="✅ All commands re-synced successfully!")
            except Exception as e:
                logger.error(f"Error syncing commands: {e}")
                await interaction.edit_original_response(
                    content=f"❌ There was an error during re-sync. Please contact support.")

    @commands.command(name='start')
    async def prefix_start(self, ctx):
        await ctx.send('Hello! I am your Chart Sayer bot.')

    @commands.command(name='chart_help')
    async def prefix_chart_help(self, ctx):
        embed = Embed(
            title="Chart Sayer - Trading Chart Analysis Bot",
            description="I can analyze trading charts to identify key price levels and trading opportunities.",
            color=Color.blue()
        )

        embed.add_field(
            name="📈 Chart Analysis",
            value="Use `/chart analyze` and attach a chart image to get entry, stop loss, and take profit levels automatically identified.",
            inline=False
        )

        embed.add_field(
            name="📊 TradingView Charts",
            value="Use `/chart tradingview <symbol>` to display an interactive TradingView chart with custom timeframes and indicators.",
            inline=False
        )

        embed.add_field(
            name="⚙️ Custom Settings",
            value="Use `/chart setup` to customize how I analyze your charts, including colors for entry/exit points and which indicators to prioritize.",
            inline=False
        )

        embed.add_field(
            name="📊 Supported Chart Types",
            value="I can analyze most standard trading charts including candlestick, line, and bar charts from any platform.",
            inline=False
        )

        embed.add_field(
            name="🔍 Example Usage",
            value="1. Take a screenshot of your chart\n2. Use `/chart analyze` and upload the image\n3. Receive entry, stop loss, and take profit levels",
            inline=False
        )

        embed.set_footer(text="For more detailed help, visit our documentation or contact the bot administrator.")

        await ctx.send(embed=embed)

    @commands.command(name='analyze')
    async def prefix_analyze(self, ctx):
        if not ctx.message.attachments:
            await ctx.send('Please attach an image to analyze.')
            return

        attachment = ctx.message.attachments[0]
        image_path = f"/tmp/{attachment.filename}"
        await attachment.save(image_path)

        # Use user-specific config if available
        user_id = str(ctx.author.id)
        config_path = "src/config/chart_config.json"

        if user_id in self.user_configs:

            result = process_chart_with_gpt4o(image_path, config_path, user_config=self.user_configs[user_id])
        else:

            result = process_chart_with_gpt4o(image_path, config_path)

        await ctx.send(f"Analysis Result: {result}")

    @commands.command(name='resync')
    @commands.is_owner()
    async def prefix_resync(self, ctx):
        """Resynchronizes application commands with Discord."""
        await ctx.send("Resyncing application commands...")

        try:
            if guild_ids:
                for guild_id in guild_ids:
                    guild = Object(id=guild_id)
                    await self.bot.tree.sync(guild=guild)
                    await ctx.send(f"Command sync complete for guild {guild_id}")
            else:
                await self.bot.tree.sync()
                await ctx.send("Global command sync complete")

            await ctx.send("✅ All commands resynced successfully!")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            await ctx.send(f"❌ Error during resync: {e}")


@bot.event
async def on_ready():
    """Called when the bot successfully connects to Discord"""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    logger.info('------')
    bot_ready.set()


async def setup_bot():
    """Set up the bot with cogs."""
    logger.info("Setting up bot cogs...")

    await bot.add_cog(ChartSayerCog(bot))

    # Load position commands
    try:
        from src.bots.commands.position_commands import PositionCommands
        await bot.add_cog(PositionCommands(bot))
        logger.info("Position commands loaded successfully")
    except Exception as e:
        logger.error(f"Error loading position commands: {e}")

    # Load price commands
    try:
        from src.bots.commands.price_commands import PriceCommands
        await bot.add_cog(PriceCommands(bot))
        logger.info("Price commands loaded successfully")
    except Exception as e:
        logger.error(f"Error loading price commands: {e}")

    logger.info("Bot cogs setup complete")


async def sync_commands():
    """Sync commands after the bot is ready."""
    try:
        logger.info("Waiting for bot to be ready...")

        await asyncio.wait_for(bot_ready.wait(), timeout=30.0)

        if shutdown_event.is_set():
            logger.info("Shutdown requested before commands could be synced")
            return

        logger.info("Syncing commands with Discord...")

        if guild_ids:
            for guild_id in guild_ids:
                guild = Object(id=guild_id)
                await bot.tree.sync(guild=guild)
                logger.info(f"Command sync complete for guild {guild_id}")
        else:

            await bot.tree.sync()
            logger.info("Global command sync complete")

    except asyncio.TimeoutError:
        logger.error("Bot failed to become ready within timeout period")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")


async def run_discord_bot():
    """Run the Discord bot with proper shutdown handling."""
    try:
        logger.info("Starting Discord bot...")

        await bot.start(discord_token)
    except Exception as e:
        logger.error(f"Error in Discord bot: {e}")
    finally:

        logger.info("Discord bot connection closed")


async def start_bot():
    """Start the bot and track all tasks."""
    bot_ready.clear()

    bot_task = create_tracked_task(run_discord_bot())

    sync_task = create_tracked_task(sync_commands())

    return bot_task, sync_task


async def shutdown_bot():
    """Properly shut down the Discord bot."""
    logger.info("Shutting down Discord bot...")

    shutdown_event.set()

    if bot.is_ready():
        logger.info("Closing Discord connection...")
        await bot.close()

    pending_tasks = [t for t in running_tasks if not t.done()]
    if pending_tasks:
        logger.info(f"Waiting for {len(pending_tasks)} tasks to complete...")
        done, pending = await asyncio.wait(pending_tasks, timeout=5.0)

        for task in pending:
            logger.warning(f"Cancelling task that didn't complete: {task}")
            task.cancel()

    logger.info("Discord bot shutdown complete")


async def setup_discord_webhook(public_key):
    """Set up configuration for Discord webhook interactions."""
    logger.info("Initializing Discord for webhook interactions")

    global bot

    if not bot:
        intents = Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='/', intents=intents)

        await setup_bot()

    bot.public_key = public_key

    return bot


async def verify_discord_signature(request: Request, public_key: str):
    """Verify that the request came from Discord."""
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')

    if not signature or not timestamp:
        return False

    body = await request.body()

    try:
        signature_bytes = bytes.fromhex(signature)

        message = timestamp.encode() + body

        public_key_bytes = bytes.fromhex(public_key)

        import nacl.signing
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
        verify_key.verify(message, signature_bytes)
        return True
    except Exception as e:
        logger.error(f"Discord signature verification failed: {e}")
        return False


async def process_discord_interaction(interaction_data):
    """Process a Discord interaction from a webhook."""
    # Handle PING interactions (required for webhook verification)
    if interaction_data['type'] == 1:  # PING
        return {"type": 1}  # PONG

    # Handle application commands (slash commands)
    elif interaction_data['type'] == 2:  # APPLICATION_COMMAND
        command_name = interaction_data['data']['name']
        logger.info(f"Received command: {command_name}")

        # Defer the response to give us time to process
        response = {
            "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "flags": 64  # EPHEMERAL (only visible to the user)
            }
        }

        asyncio.create_task(handle_command(interaction_data))

        return response

    else:
        logger.warning(f"Unhandled interaction type: {interaction_data['type']}")
        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "content": "This interaction type is not supported yet.",
                "flags": 64  # EPHEMERAL
            }
        }


async def handle_command(interaction_data):
    """Handle a Discord command in a background task."""
    try:
        command_name = interaction_data['data']['name']
        interaction_id = interaction_data['id']
        interaction_token = interaction_data['token']

        if command_name == "start":
            content = "Hello! I am your Chart Sayer bot."
        elif command_name == "chart_help":
            content = "Send me a chart image to analyze."
        elif command_name == "analyze":
            content = "Please upload your chart image in a follow-up message."
        else:
            content = f"Unknown command: {command_name}"

        # Send a followup message using Discord's REST API
        webhook_url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original"

        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "content": content
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch(webhook_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error sending Discord response: {error_text}")

    except Exception as e:
        logger.error(f"Error handling command: {e}")


if __name__ == "__main__":
    async def main():
        await setup_bot()
        bot_task, sync_task = await start_bot()
        try:

            await asyncio.Future()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Bot interrupted, shutting down...")
        finally:
            await shutdown_bot()


    asyncio.run(main())
