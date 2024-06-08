import os
import re
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

kevin_author_id = 200696839639531523

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
        print(
            f'An error occured during an SQL update changing channel_id in {input_table} to {input_channel_id}: {error}')
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
    embed.add_field(name='Best Record', value=fr'{stat_query[0]}', inline=False)
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
        print(f'Channel {voice_channel} was not found. Unable to update.')
        await interaction.response.send_message(f'Channel {voice_channel} wasn\'t not found. Unable to update.',
                                                ephemeral=True)


@bot.slash_command(description='Reset the clock!', guild_ids=BadKevinBotID)
async def reset(context: discord.ApplicationContext):
    update_reset = reset_current_record('global_stats')
    await reset_channel_name()
    await context.respond(f'{update_reset}')


# Reporting:
@bot.slash_command(description='Report Kevin:', guild_ids=BadKevinBotID)
async def report(context: discord.ApplicationContext):
    report_embed = discord.Embed(
        title='Report',
        description='You are currently reporting Kevin for some wacko shit. Please select a recent message from below to start the reporting process.',
        color=discord.Color.red()
    )

    select_options = []
    messages_channel = bot.get_channel(context.channel_id)
    messages = await messages_channel.history(limit=100).flatten()
    for message in messages:
        if message.author.id == kevin_author_id:
            message_label = message.author.display_name[:24]
            message_content_preview = message.content[:99]
            message_id = message.id
            select_options.append(
                discord.SelectOption(
                    label=f'{message_label}',
                    value=f'{message_id}',
                    description=f'{message_content_preview}'
                )
            )

    report_view = discord.ui.View()

    message_selection = discord.ui.Select(custom_id='Message Selection',
                                          placeholder='The last few of Kevin\'s chat in this channel are below.',
                                          options=select_options,
                                          min_values=1,
                                          max_values=1
                                          )

    async def message_selection_callback(interaction: discord.Interaction):
        for child in report_view.children:
            if isinstance(child, discord.ui.Button) and child.label == 'Report':
                child.disabled = False
                break

        for index, option in enumerate(message_selection.options):
            if option.value == message_selection.values[0]:
                message_selection.options[index].default = True
            else:
                message_selection.options[index].default = False
        await interaction.response.edit_message(view=report_view)

    message_selection.callback = message_selection_callback
    report_view.add_item(message_selection)

    cancel_button = discord.ui.Button(label='Cancel', style=discord.ButtonStyle.grey, custom_id='Cancel Button')

    async def cancel_button_callback(interaction: discord.Interaction):
        report_view.disable_all_items()
        cancel_embed = discord.Embed(
            title='Report Cancelled',
            description='User cancelled or timed out. No report was submitted.',
            color=discord.Color.blue()
        )
        cancel_embed.set_footer(text='This message will disappear soon or can be dismissed.')
        await interaction.response.edit_message(embed=cancel_embed, view=report_view)

    cancel_button.callback = cancel_button_callback
    report_view.add_item(cancel_button)

    report_button = discord.ui.Button(label='Report', style=discord.ButtonStyle.red, custom_id='Report Button',
                                      disabled=True)

    async def report_button_callback(interaction: discord.Interaction):
        report_view.disable_all_items()
        embed_report = discord.Embed(
            title='Report Submitted',
            description='Your report should be visible below for all guild members to vote on below. Thank you for your service to this good Christian Discord.',
            color=discord.Color.green(),
        )
        embed_report.set_footer(text='This message will disappear soon or can be dismissed.')
        await interaction.response.edit_message(embed=embed_report, view=report_view)

        vote_embed = discord.Embed(
            title='Wacko Alert!',
            description='Kevin has been reported for saying some wacko shit. Information regarding the offense is below.',
            color=discord.Color.red()
        )
        message_content = await context.fetch_message(int(message_selection.values[0]))
        vote_embed.set_thumbnail(url='https://i.imgflip.com/5kv6v1.png')
        vote_embed.add_field(name='', value=' ', inline=False)
        vote_embed.add_field(name=f'Message: {message_content.jump_url}', value=f'> {message_content.content}', inline=False)
        vote_embed.add_field(name='', value=' ', inline=False)
        vote_embed.add_field(name='', value='**Five wacko votes will result in a Kevin\'s counter being reset.**', inline=False)
        vote_embed.add_field(name='Passes:', value='`0`', inline=True)
        vote_embed.add_field(name='Wacko:', value='`0`', inline=True)

        vote_view = discord.ui.View()

        upvote_voter_array = []
        downvote_voter_array = []

        upvote_button = discord.ui.Button(label='Acceptable...', style=discord.ButtonStyle.green, emoji='🆗', custom_id='Upvote Button')

        async def upvote_button_callback(interaction: discord.Interaction):
            voter = interaction.message.author.id
            if voter in upvote_voter_array:
                upvote_voter_array.remove(voter)
                new_upvote_value = int(vote_embed.fields[4].value.replace('`', '')) - 1
            else:
                upvote_voter_array.append(voter)
                new_upvote_value = int(vote_embed.fields[4].value.replace('`', '')) + 1

            vote_embed.set_field_at(index=4, name='Passes:', value=f'`{new_upvote_value}`', inline=True)

            await interaction.response.edit_message(embed=vote_embed, view=vote_view)

        upvote_button.callback = upvote_button_callback
        vote_view.add_item(upvote_button)

        downvote_button = discord.ui.Button(label='Wacko!', style=discord.ButtonStyle.red, emoji='😬', custom_id='Downvote Button')

        async def downvote_button_callback(interaction: discord.Interaction):
            voter = interaction.message.author.id
            if voter in downvote_voter_array:
                downvote_voter_array.remove(voter)
                new_downvote_value = int(vote_embed.fields[5].value.replace('`', '')) - 1
            else:
                downvote_voter_array.append(voter)
                new_downvote_value = int(vote_embed.fields[5].value.replace('`', '')) + 1
                if new_downvote_value == 1:
                    await reset_channel_name()
                else:
                    pass

            vote_embed.set_field_at(index=5, name='Wacko:', value=f'`{new_downvote_value}`', inline=True)

            await interaction.response.edit_message(embed=vote_embed, view=vote_view)

        downvote_button.callback = downvote_button_callback
        vote_view.add_item(downvote_button)

        await context.respond(embed=vote_embed, view=vote_view, ephemeral=True)
        pass

    report_button.callback = report_button_callback
    report_view.add_item(report_button)

    await context.respond(embed=report_embed, ephemeral=True, view=report_view)


# Discord-based embeds and logic
async def update_channel_name(current_record_value):
    channel_id = query_database('global_stats')[5]
    voice_channel = bot.get_channel(channel_id)
    print(voice_channel.name)
    print(voice_channel.name)
    new_name = f'[{current_record_value}] days since Kevin said something wacko.'

    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
        try:
            await voice_channel.edit(name=new_name)
            print(f'Successfully renamed channel {voice_channel.id} to {voice_channel.name}.')
            return f'Successfully renamed channel {voice_channel.id} to {voice_channel.name}.'

        except Exception as error:
            print(f'Failed to rename channel: {error}')
            return f'Failed to rename channel: {error}'
    else:
        print(f'Channel ID: {voice_channel.id}: was not found. Unable to update.')
        return f'Channel ID: {voice_channel.id}: was not found. Unable to update.'


async def reset_channel_name():
    channel_id = query_database('global_stats')[5]
    voice_channel = bot.get_channel(channel_id)

    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
        try:
            await voice_channel.edit(name=f'[0] days since Kevin said something wacko.')
            print(f'Successfully renamed channel {voice_channel}.')
            return f'Successfully renamed channel {voice_channel}.'

        except Exception as error:
            print(f'Failed to rename channel: {error}')
            return f'Failed to rename channel: {error}'
    else:
        print(f'Channel {voice_channel} was not found. Unable to update.')
        return f'Channel {voice_channel} was not found. Unable to update.'


# Simplified loop, eventually will use DateTime objects that can keep track of other changes such as reports.
@tasks.loop(hours=24)
async def daily_update():
    update_current_record('global_stats')
    print(f'Updated daily stats.')


@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user.name}')


bot.run(clientSecret)
