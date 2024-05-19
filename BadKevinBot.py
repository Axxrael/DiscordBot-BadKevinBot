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
bot = commands.Bot(command_prefix='/',intents=botIntents) # Sets the prefix for all commands moving forward

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


def query_database(): # Connects the SQL Day Tracker database to the bot
    try:
        cursorDayLeaderboard.execute("SELECT `Current Record` FROM `Day Tracker`") # Grabbing the int value of Current Record from Day Tracker
        currentRecord = cursorDayLeaderboard.fetchone(); # Day counter
        if currentRecord == None:
            currentRecord = 0
        else:
            currentRecord = currentRecord[0] # Extract the first element (fetchone returns as a tuple)
        print(f'SELECT `Current Record` FROM `Day Tracker` fetch = {currentRecord}')

        cursorDayLeaderboard.execute("SELECT `Personal best (longest streak)` FROM `Day Tracker`") # Grabbing the int value of Personal best from Day Tracker
        personalBest = cursorDayLeaderboard.fetchone(); # Highest Recorded Day
        if personalBest == None:
            personalBest = 0
        else:
            personalBest = personalBest[0]
        print(f'SELECT `Personal best (longest streak)` FROM `Day Tracker` = {personalBest}')

        return currentRecord, personalBest
    except Exception as e: # Error catching
        print(f"An error occured: {e}")
        return None, None


def update_database(currentRecord, personalBest): # Updates the database's current record and personal best
    try:
        currentRecordStr = str(currentRecord)
        personalBestStr = str(personalBest)
        cursorDayLeaderboard.execute(f"UPDATE `Day Tracker` SET `Current Record`= {currentRecordStr} +  1 WHERE `Current Record` >  0")
        print("Updated Current Record SQL")
        print(f'Rows affected: {cursorDayLeaderboard.rowcount}')

        cursorDayLeaderboard.execute(f"UPDATE `Day Tracker` SET `Personal best (longest streak)`= {personalBestStr} + 1 WHERE `Personal best (longest streak)` > 0")
        print("Updated Personal best SQL")
        print(f'Rows affected: {cursorDayLeaderboard.rowcount}')

        databaseDayLeaderboard.commit()
    except Exception as e: # Error catching
        print(f"An error occured during update: {e}")


async def change_channel_name(bot, channelId, currRecord): # Changes the name of the channel
    Voice_Channel = bot.get_channel(channelId)
    new_name = (f"{currRecord} Days since Kevin said some wacko shit.")

    if Voice_Channel and isinstance(Voice_Channel, discord.VoiceChannel): # Checks if channel exists
        try:
            await Voice_Channel.edit(name=new_name)
            print(f"Successfully renamed channel")
        except Exception as e:
            print(f"Failed to rename channel: {e}")
    else:
        print("Channel not found")


# ---------- 24-hour Day Tracking Loop ----------
@tasks.loop(seconds=10) # Runs every 24 hours automatically
async def loopcheck():
    currRecord, perBest = query_database()
    update_database(currRecord, perBest)
    await change_channel_name(bot, named_channel_id, currRecord)

@bot.event
async def on_ready():
    await bot.sync_commands() # Sync the commands to Discord
    print(f'Bot is ready. Logged in as {bot.user.name}')
    loopcheck.start()


bot.run(clientSecret)