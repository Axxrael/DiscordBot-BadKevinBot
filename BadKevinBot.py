import os
from dotenv import load_dotenv
import discord
from discord.ext import commands


# Load the environment file for protected Discord Bot information.
# Should include PUBLICKEY, CLIENTID, and CLIENTSECRET.
load_dotenv()
publicKey = (os.environ.get('PUBLICKEY'))
clientID = (os.environ.get('CLIENTID'))
clientSecret = (os.environ.get('CLIENTSECRET'))

botIntents = discord.Intents().default()
bot = commands.Bot(command_prefix='/', intents=botIntents)


# Built-in slash commands listed here.
@bot.slash_command(
    name='ping',
    description="A pong for your ping."
)


async def ping(context):  # the function name should match the @bot.slash_command name.
    embed = discord.Embed(
        description=(
            f'Pong!'
        ),
        color=discord.Color.purple()
    )
    await context.respond(embed=embed)
    print(f'Sending ping-pong...')


@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user.name}')


bot.run(clientSecret)
