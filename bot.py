import os 
import discord
from dotenv import load_dotenv

# ----------Bot Connection & Variable setups----------
load_dotenv()
TOKEN = os.getenv('Discord_Token') # Connect the bot's connection to the variable in .env file
bot = discord.Client(intents = discord.Intents.default())

# ----------Bot Events----------
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.run(TOKEN)