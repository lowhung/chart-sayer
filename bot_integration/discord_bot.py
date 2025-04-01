import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')

# Initialize Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

class ChartSayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='start')
    async def start(self, ctx):
        await ctx.send('Hello! I am your Chart Sayer bot.')

    @commands.command(name='chart_help')
    async def chart_help(self, ctx):
        await ctx.send('Send me a chart image to analyze.')

    @commands.command(name='analyze')
    async def analyze(self, ctx):
        if not ctx.message.attachments:
            await ctx.send('Please attach an image to analyze.')
            return

        # Download the image
        attachment = ctx.message.attachments[0]
        image_path = f"/tmp/{attachment.filename}"
        await attachment.save(image_path)

        # Process the image
        config_path = "/workspace/chart-sayer/config/chart_config.json"
        result = process_chart_with_gpt4o(image_path, config_path)

        # Send the analysis result
        await ctx.send(f"Analysis Result: {result}")
logger.info('Adding ChartSayerCog to the bot')


# Add the cog to the bot
async def if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_bot()):
    await bot.add_cog(ChartSayerCog(bot))