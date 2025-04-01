import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content.startswith('!start'):
            await message.channel.send('Hello! I am your Chart Sayer bot.')

        if message.content.startswith('!help'):
            await message.channel.send('Send me a chart image to analyze.')

intents = discord.Intents.default()
intents.message_content = True

# Replace 'YOUR_TOKEN' with your bot's token
client = MyClient(intents=intents)
client.run('YOUR_TOKEN')