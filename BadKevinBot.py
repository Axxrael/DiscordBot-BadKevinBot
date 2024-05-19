import os
import discord
import mysql.connector
from dotenv import load_dotenv
from discord.ext import tasks


# ---------- VARIABLES AND INFORMATION ----------
# Load the environment file for protected Discord Bot information.
load_dotenv()
publicKey = (os.environ.get('PUBLICKEY'))
clientID = (os.environ.get('CLIENTID'))
clientSecret = (os.environ.get('CLIENTSECRET'))
sqlPassword = (os.environ.get('SQLPASSWORD'))
BadKevinBotID = [1205001660145995776]

intents = discord.Intents.default()
bot = discord.Bot()

databaseConnection = mysql.connector.connect(
    host='gamesnj409.bisecthosting.com',
    port='3306',
    user='u82778_voWyKm3ryk',
    password=sqlPassword,
    database='s82778_DayLeaderboard'
)
databaseCursor = databaseConnection.cursor()


# Database-based logic
def query_database(input_table):  # Queries values from the SQL databse to return to the bot.
    try:
        databaseCursor.execute(fr'SELECT current_record FROM {input_table}')
        current_record_value = databaseCursor.fetchone()[0]  # fetchone returns tuple
        if current_record_value is None:
            current_record_value = 0

        databaseCursor.execute(fr'SELECT best_record FROM {input_table}')
        best_record_value = databaseCursor.fetchone()[0]
        if best_record_value is None:
            best_record_value = 0

        databaseCursor.execute(fr'SELECT last_wacko_message FROM {input_table}')
        last_wacko_message_value = databaseCursor.fetchone()[0]
        if last_wacko_message_value is None:
            last_wacko_message_value = 'none'

        databaseCursor.execute(fr'SELECT streak_average FROM {input_table}')
        streak_average_value = databaseCursor.fetchone()[0]
        if streak_average_value is None:
            streak_average_value = 0

        databaseCursor.execute(fr'SELECT total_reset_amount FROM {input_table}')
        total_reset_amount_value = databaseCursor.fetchone()[0]
        if total_reset_amount_value is None:
            total_reset_amount_value = 0

        databaseCursor.execute(fr'SELECT channel_id FROM {input_table}')
        channel_id_value = databaseCursor.fetchone()[0]

        return best_record_value, current_record_value, last_wacko_message_value, streak_average_value, total_reset_amount_value, channel_id_value

    except Exception as error:
        print(f'An error occured: {error}')
        return fr'There was an error while querying the database.'


def update_current_record(input_table):
    try:
        databaseCursor.execute(fr'UPDATE {input_table} SET current_record = current_record + 1')
        databaseConnection.commit()
        print(f'Added 1 to current_record in {input_table}')
        return fr'Added 1 to Kevin\'s current record. Way to go!'

    except Exception as error:
        print(f'An error occured during an SQL update adding to current_record in {input_table}: {error}')
        return fr'There was an error updating the current record. There may be an issue with the database.'


def update_channel_id(input_table, input_channel_id):
    try:
        databaseCursor.execute(fr'UPDATE {input_table} SET channel_id = {input_channel_id}')
        databaseConnection.commit()
        print(f'Changed channel_id in {input_table} to {input_channel_id}')
        return fr'Changed channel_id in {input_table} to {input_channel_id}'

    except Exception as error:
        print(f'An error occured during an SQL update changing channel_id in {input_table} to {input_channel_id}: {error}')
        return fr'An error occured during an SQL update changing channel_id in {input_table} to {input_channel_id}.'


def reset_current_record(input_table):
    try:
        databaseCursor.execute(fr'UPDATE {input_table} SET current_record = 0')
        databaseConnection.commit()
        print(f'Reset current record in {input_table}.')
        return fr'Reset Kevin\'s current record to zero. Not upset, just disappointed.'

    except Exception as error:
        print(f"An error occured during an SQL update: {error}")
        return fr'There was an error resetting the current record. There may be an issue with the database.'


# Slash command groups: These don't appear to work based on the documentation...
setCommandGroup = discord.SlashCommandGroup('set', 'Administratively set options for your server.')


# Built-in slash commands:
@bot.slash_command(description='Set the channel that receives name updates.', guild_ids=BadKevinBotID)
async def set_channel_id(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    channel_id = discord.utils.get(bot.get_all_channels(), name=f'{channel_name}').id
    update_channel = update_channel_id('global_stats', channel_id)
    await interaction.response.send_message(f'{update_channel}', ephemeral=True)


@bot.slash_command(description='Get current Kevin stats.', guild_ids=BadKevinBotID)
async def stats(context: discord.ApplicationContext):
    embed = discord.Embed(
        title='Kevin\'s current stats:',
        color=discord.Color.purple()
    )
    stat_query = query_database('global_stats')
    embed.add_field(name='Best Record', value=fr'{stat_query[0]}',  inline=False)
    embed.add_field(name='Current Record:', value=fr'{stat_query[1]}', inline=False)
    embed.add_field(name='Streak Average:', value=fr'{stat_query[3]}', inline=False)
    embed.add_field(name='Total Resets:', value=fr'{stat_query[4]}', inline=False)
    embed.add_field(name='Last Wacko Message:', value=fr'{stat_query[2]}', inline=False)
    await context.respond(embed=embed)


@bot.slash_command(description='Advance Kevin 1 day.', guild_ids=BadKevinBotID)
async def advance(interaction: discord.Interaction):
    update_advance = update_current_record('global_stats')
    await interaction.response.send_message(f'{update_advance}', ephemeral=True)


@bot.slash_command(description='Advance channel name.', guild_ids=BadKevinBotID)
async def channel(interaction: discord.Interaction):
    current_record_value = query_database('global_stats')[1]
    current_channel_id = query_database('global_stats')[5]
    voice_channel = discord.utils.get(bot.get_all_channels(), id=current_channel_id)

    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):  # Checks if channel exists
        try:
            await update_channel_name(current_record_value)
            await interaction.response.send_message(f'Updated count on channel.', ephemeral=True)

        except Exception as error:
            print(f'Failed to rename channel {voice_channel}: {error}')
            await interaction.response.send_message(f'Failed to rename channel {voice_channel}.', ephemeral=True)
    else:
        print(f'Channel {voice_channel} wasn\'t not found. Unable to update.')
        await interaction.response.send_message(f'Channel {voice_channel} wasn\'t not found. Unable to update.', ephemeral=True)


@bot.slash_command(description='Reset the clock!', guild_ids=BadKevinBotID)
async def reset(context: discord.ApplicationContext):
    update_reset = reset_current_record('global_stats')
    await reset_channel_name()
    await context.respond(f'{update_reset}')


# Discord-based logic
async def update_channel_name(current_record_value):
    channel_id = query_database('global_stats')[5]
    voice_channel = bot.get_channel(channel_id)
    new_name = f'[{current_record_value}] days since Kevin said something wacko.'

    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):  # Checks if channel exists
        try:
            await voice_channel.edit(name=new_name)
            print(f'Successfully renamed channel {voice_channel}.')
            return f'Successfully renamed channel {voice_channel}.'

        except Exception as error:
            print(f'Failed to rename channel: {error}')
            return f'Failed to rename channel: {error}'
    else:
        print(f'Channel {voice_channel} wasn\'t not found. Unable to update.')
        return f'Channel {voice_channel} wasn\'t not found. Unable to update.'


async def reset_channel_name():
    channel_id = query_database('global_stats')[5]
    voice_channel = bot.get_channel(channel_id)

    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):  # Checks if channel exists
        try:
            await voice_channel.edit(name=f'[0] days since Kevin said something wacko.')
            print(f'Successfully renamed channel {voice_channel}.')
            return f'Successfully renamed channel {voice_channel}.'

        except Exception as error:
            print(f'Failed to rename channel: {error}')
            return f'Failed to rename channel: {error}'
    else:
        print(f'Channel {voice_channel} wasn\'t not found. Unable to update.')
        return f'Channel {voice_channel} wasn\'t not found. Unable to update.'


# Simplified loop, eventually will use DateTime objects that can keep track of other changes such as reports.
@tasks.loop(hours=1)
async def daily_update():
    update_current_record('global_stats')
    print(f'Updated daily stats.')


@bot.event
async def on_ready():
    daily_update.start()
    print(f'Bot is ready. Logged in as {bot.user.name}')

bot.run(clientSecret)
