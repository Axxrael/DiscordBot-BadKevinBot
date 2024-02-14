import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
import mysql.connector


# ---------- VARIABLES AND INFORMATION ----------
# Load the environment file for protected Discord Bot information.
# Should include PUBLICKEY, CLIENTID, and CLIENTSECRET.
load_dotenv()
publicKey = (os.environ.get('PUBLICKEY'))
clientID = (os.environ.get('CLIENTID'))
clientSecret = (os.environ.get('CLIENTSECRET'))
sqlPassword = (os.environ.get('SQLPASSWORD'))
named_channel_id = 1205001660976603139 # You can right click on channels to copy their id's (The current Id for BadKevinBot General VC)

botIntents = discord.Intents().default()
bot_command = commands.Bot(command_prefix="/",intents=botIntents) # Sets the prefix for all commands moving forward

databaseDayLeaderboard = mysql.connector.connect( # DayLeaderboard Database connection
    host="gamesnj409.bisecthosting.com",
    port="3306",
    user="u82778_voWyKm3ryk",
    password=sqlPassword,
    database="s82778_DayLeaderboard"
)
cursorDayLeaderboard = databaseDayLeaderboard.cursor() # cursor object


# Built-in slash commands listed here.
@bot_command.slash_command(
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


def query_database(): # Connects the SQL Day Tracker database to the bot
    cursorDayLeaderboard.execute("SELECT `Current Record` FROM `Day Tracker`") # Grabbing the int value of Current Record from Day Tracker
    print('SQL Table Connected!!')
    currentRecord = cursorDayLeaderboard.fetchone(); # Day counter
    if currentRecord == None:
        currentRecord = 0
    print(f'SELECT `Current Record` FROM `Day Tracker` fetch = {currentRecord}')

    cursorDayLeaderboard.execute("SELECT `Personal best (longest streak)` FROM `Day Tracker`") # Grabbing the int value of Personal best from Day Tracker
    personalBest = cursorDayLeaderboard.fetchone(); # Highest Recorded Day
    if personalBest == None:
        personalBest = 0
    print(f'SELECT `Personal best (longest streak)` FROM `Day Tracker` = {personalBest}')
    return currentRecord, personalBest


# ---------- 24-hour Day Tracking Loop ----------
@tasks.loop(seconds=10) # Runs every 24 hours automatically
async def loopcheck():
    print("looping")


@bot_command.event
async def on_ready():
    await bot_command.sync_commands() # Sync the commands to Discord
    print(f'Bot is ready. Logged in as {bot_command.user.name}')
    query_database()
    'loopcheck.start()'


bot_command.run(clientSecret)
