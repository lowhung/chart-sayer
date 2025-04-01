from fastapi import APIRouter
import discord
from discord.ext import commands
import os

router = APIRouter()

# Initialize Discord bot with slash commands
intents = discord.Intents.default()
intents.message_content = True

discord_token = os.getenv('DISCORD_TOKEN')

discord_bot = commands.Bot(command_prefix='/', intents=intents)

@discord_bot.event
async def on_ready():
    print(f'Logged on as {discord_bot.user}!')

@discord_bot.slash_command(name='start', description='Start the bot')
async def start(ctx):
    await ctx.respond('Hello! I am your Chart Sayer bot.')

@discord_bot.slash_command(name='help', description='Get help with the bot')
async def help_command(ctx):
    await ctx.respond('Send me a chart image to analyze.')

discord_bot.run(discord_token)

@router.post("/discord")
async def discord_webhook():
    return {"status": "Discord webhook received"}