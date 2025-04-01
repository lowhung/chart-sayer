import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from src.image_processing.openai_integration import process_chart_with_gpt4o

# Configure logging
logger = logging.getLogger(__name__)

# Global variables for coordination
bot_ready = asyncio.Event()
shutdown_event = asyncio.Event()
running_tasks = set()

# Load environment variables
load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
test_guild_id = os.getenv('DISCORD_TEST_GUILD_ID')

# Optional: Convert test_guild_id to int for guild-specific commands
guild_ids = [int(test_guild_id)] if test_guild_id else None

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


# Helper function to track tasks
def create_tracked_task(coro):
    """Create a task and add it to our set of tracked tasks."""
    task = asyncio.create_task(coro)
    running_tasks.add(task)
    task.add_done_callback(running_tasks.discard)
    return task


class ChartSayerCog(commands.Cog, name="Chart Sayer"):
    def __init__(self, bot):
        self.bot = bot

        # Create a command group for all chart-related commands
        self.chart_group = app_commands.Group(
            name="chart",
            description="Chart analysis commands",
            guild_ids=guild_ids  # For faster testing in specific guilds
        )

        # Add the group to the bot's command tree
        self.bot.tree.add_command(self.chart_group)

        # Register the commands within the group
        # Note: We do this inside __init__ to keep everything together
        self.setup_commands()

    def setup_commands(self):
        """Register all commands to the command group"""

        # Define commands within the group
        @self.chart_group.command(name="start", description="Start the Chart Sayer bot")
        async def start(interaction: discord.Interaction):
            await interaction.response.send_message('Hello! I am your Chart Sayer bot.')

        @self.chart_group.command(name="help", description="Get help with chart analysis")
        async def help(interaction: discord.Interaction):
            await interaction.response.send_message(
                'Send me a chart image to analyze using `/chart analyze` command.'
            )

        @self.chart_group.command(name="analyze", description="Analyze a chart image")
        async def analyze(interaction: discord.Interaction, file: discord.Attachment):
            # Verify it's an image file
            if not file.content_type or not file.content_type.startswith('image/'):
                await interaction.response.send_message(
                    "Please upload an image file. This doesn't appear to be an image."
                )
                return

            # Tell Discord we're working on it (prevents timeout)
            await interaction.response.defer(thinking=True)

            try:
                # Download the image
                image_path = f"/tmp/{file.filename}"
                await file.save(image_path)

                # Process the image
                config_path = "src/config/chart_config.json"
                result = process_chart_with_gpt4o(image_path, config_path)

                # Send the analysis result
                await interaction.followup.send(f"Analysis Result: {result}")

            except Exception as e:
                logger.error(f"Error processing image: {e}")
                await interaction.followup.send(
                    "Sorry, I encountered an error analyzing your chart. Please try again."
                )

    # Traditional prefix commands (as a complementary approach)
    @commands.command(name='start')
    async def prefix_start(self, ctx):
        await ctx.send('Hello! I am your Chart Sayer bot.')

    @commands.command(name='chart_help')
    async def prefix_chart_help(self, ctx):
        await ctx.send('Send me a chart image to analyze.')

    @commands.command(name='analyze')
    async def prefix_analyze(self, ctx):
        if not ctx.message.attachments:
            await ctx.send('Please attach an image to analyze.')
            return

        # Download the image
        attachment = ctx.message.attachments[0]
        image_path = f"/tmp/{attachment.filename}"
        await attachment.save(image_path)

        # Process the image
        config_path = "src/config/chart_config.json"
        result = process_chart_with_gpt4o(image_path, config_path)

        # Send the analysis result
        await ctx.send(f"Analysis Result: {result}")


@bot.event
async def on_ready():
    """Called when the bot successfully connects to Discord"""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    logger.info('------')
    bot_ready.set()  # Signal that the bot is ready


async def setup_bot():
    """Set up the bot with cogs."""
    logger.info("Setting up bot cogs...")

    # Add the ChartSayer cog
    await bot.add_cog(ChartSayerCog(bot))

    logger.info("Bot cogs setup complete")


async def sync_commands():
    """Sync commands after the bot is ready."""
    try:
        logger.info("Waiting for bot to be ready...")
        # Wait with a timeout to avoid hanging forever
        await asyncio.wait_for(bot_ready.wait(), timeout=30.0)

        if shutdown_event.is_set():
            logger.info("Shutdown requested before commands could be synced")
            return

        logger.info("Syncing commands with Discord...")

        # For development, sync to specific guilds (faster)
        if guild_ids:
            for guild_id in guild_ids:
                guild = discord.Object(id=guild_id)
                await bot.tree.sync(guild=guild)
                logger.info(f"Command sync complete for guild {guild_id}")
        else:
            # Sync globally (can take up to an hour to appear)
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
        # Use start instead of run to maintain control
        await bot.start(discord_token)
    except Exception as e:
        logger.error(f"Error in Discord bot: {e}")
    finally:
        # This point is reached when bot.close() is called
        logger.info("Discord bot connection closed")


async def start_bot():
    """Start the bot and track all tasks."""
    bot_ready.clear()  # Reset the ready flag

    # Start the bot in a tracked task
    bot_task = create_tracked_task(run_discord_bot())

    # Start command syncing in a tracked task
    sync_task = create_tracked_task(sync_commands())

    return bot_task, sync_task


async def shutdown_bot():
    """Properly shut down the Discord bot."""
    logger.info("Shutting down Discord bot...")

    # Signal that we're shutting down
    shutdown_event.set()

    # Close the bot connection if it's running
    if bot.is_ready():
        logger.info("Closing Discord connection...")
        await bot.close()

    # Wait for all tasks to finish with a timeout
    pending_tasks = [t for t in running_tasks if not t.done()]
    if pending_tasks:
        logger.info(f"Waiting for {len(pending_tasks)} tasks to complete...")
        done, pending = await asyncio.wait(pending_tasks, timeout=5.0)

        # Cancel any tasks that are still pending
        for task in pending:
            logger.warning(f"Cancelling task that didn't complete: {task}")
            task.cancel()

    logger.info("Discord bot shutdown complete")


# Add this if you want to run the bot standalone (not through FastAPI)
if __name__ == "__main__":
    async def main():
        await setup_bot()
        bot_task, sync_task = await start_bot()
        try:
            # Keep the bot running until interrupted
            await asyncio.Future()  # This future never completes
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Bot interrupted, shutting down...")
        finally:
            await shutdown_bot()


    asyncio.run(main())
