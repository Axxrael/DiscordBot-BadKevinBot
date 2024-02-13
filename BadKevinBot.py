import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import mysql.connector
import asyncio
import concurrent.futures



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
bot = commands.Bot(command_prefix="/",intents=botIntents) # Sets the prefix for all commands moving forward

databaseDayLeaderboard = mysql.connector.connect( # DayLeaderboard Database connection
    host="gamesnj409.bisecthosting.com",
    port="3306",
    user="u82778_voWyKm3ryk",
    password=sqlPassword,
    database="s82778_DayLeaderboard"
)
cursorDayLeaderboard = databaseDayLeaderboard.cursor() # cursor object


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


# ---------- 24-hour Day Tracking Loop ----------
def query_database():
    cursorDayLeaderboard.execute("SELECT `Current Record` FROM `Day Tracker`") # Grabbing the int value of Current Record from Day Tracker
    print('SQL Table Connected!!')
    days = cursorDayLeaderboard.fetchone(); # Day counter
    print(f'SELECT `Current Record` FROM `Day Tracker` fetch = {days}')
    cursorDayLeaderboard.execute("SELECT `Personal best (longest streak)` FROM `Day Tracker`") # Grabbing the int value of Personal best from Day Tracker
    topDayCount = cursorDayLeaderboard.fetchone(); # Highest Recorded Day
    print(f'SELECT `Personal best (longest streak)` FROM `Day Tracker` = {topDayCount}')
    return days, topDayCount

@bot.loop(seconds=24) # Runs every 24 hours automatically
async def change_channel_name(resetCheck=1): # Does the name changing for the channel (multiplier is usually nothing except to reset, which is then set to 0)
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        days, topDayCount = await loop.run_in_executor(executor, query_database)
    if resetCheck == 0:
        if days > topDayCount:
            print(f'New Personal Best: {days}')
            '''cursorDayLeaderboard.execute(f"UPDATE `Day Tracker` SET `Personal best (longest streak)` = {days}")
            databaseDayLeaderboard.commit()
        
        cursorDayLeaderboard.execute("UPDATE `Day Tracker` SET `Current Record` = 0") # Resets Current Record to 0
        databaseDayLeaderboard.commit()'''
        print(f'Resetting Current record')
    else:
        '''cursorDayLeaderboard.execute("UPDATE `Day Tracker` SET `Current Record` = `Current Record` + 1") # New day
        databaseDayLeaderboard.commit()'''
        print(f'Another successful day with wack')

    '''new_name = (f'[{days}] Days since Kevin said some wacko shit')
    channel = bot.get_channel(named_channel_id) # Grabs the channel using the channelId (right click on the channel in discord) as an argument
    print(f"Change channel: {channel} to {new_name}")
    await channel.edit(name=new_name) # Does the editing
    print("Channel name changed!")'''


@bot.slash_command(name='wackoshit', description="Change the channel name") # Takes in /wacko shit as a command
async def change_channel(ctx): # Initiates channel change
    await change_channel_name()


@bot.event
async def on_ready():
    await bot.sync_commands() # Sync the commands to Discord
    print(f'Bot is ready. Logged in as {bot.user.name}')


bot.run(clientSecret)
