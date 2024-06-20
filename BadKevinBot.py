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
def check_for_server_entry(input_server_id):
    databaseCursor.execute(fr'SELECT server_id FROM global_stats WHERE server_id={input_server_id}')
    if databaseCursor.fetchone() is None:
        try:
            databaseCursor.execute(fr'INSERT INTO global_stats (server_id, total_reset_amount, best_record, streak_average, last_wacko_message) VALUES ({input_server_id}, 0, 0, 0, "No messages found.")')
            databaseConnection.commit()
        except Exception as error:
            raise fr'This server wasn\'t found in the database, and an error adding this server to the database occured: {error}'
    else:
        pass


def query_database(input_table, input_server_id):

    try:
        databaseCursor.execute(fr'SELECT channel_id FROM {input_table} WHERE server_id={input_server_id}')
        channel_id_value = databaseCursor.fetchone()[0]
        databaseCursor.execute(fr'SELECT total_reset_amount FROM {input_table} WHERE server_id={input_server_id}')
        total_reset_amount_value = databaseCursor.fetchone()[0]
        databaseCursor.execute(fr'SELECT best_record FROM {input_table} WHERE server_id={input_server_id}')
        best_record_value = databaseCursor.fetchone()[0]
        databaseCursor.execute(fr'SELECT streak_average FROM {input_table} WHERE server_id={input_server_id}')
        streak_average_value = databaseCursor.fetchone()[0]
        databaseCursor.execute(fr'SELECT last_wacko_message FROM {input_table} WHERE server_id={input_server_id}')
        last_wacko_message_value = databaseCursor.fetchone()[0]

        return channel_id_value, total_reset_amount_value, best_record_value, streak_average_value, last_wacko_message_value

    except Exception as error:
        print(f'An error occured where querying from table {input_table} for server {input_server_id}: {error}')
        return fr'There was an error while querying the database.'


def update_channel_id(input_table, input_server_id, input_channel_id):
    try:
        databaseCursor.execute(fr'UPDATE {input_table} SET channel_id = {input_channel_id} WHERE server_id={input_server_id}')
        databaseConnection.commit()
        print(f'Changed channel_id in {input_table} to {input_channel_id} for server: {input_server_id}')
        return fr'Updated the tracking channel to ID:{input_channel_id} for this server.'

    except Exception as error:
        print(f'An error occured during an SQL update changing channel_id in {input_table} to {input_channel_id} in server: {input_server_id}: {error}')
        return fr'An error occured during an SQL update changing channel_id to {input_channel_id}: {error}'


def reset_current_record(input_table, input_server_id, input_current_record_value):
    try:
        databaseCursor.execute(fr'UPDATE {input_table} SET total_reset_amount = total_reset_amount + 1 WHERE server_id={input_server_id}')
        print(input_current_record_value)
        # update streak_average and best_record here later with input_current_record_value and math
        databaseConnection.commit()
        print(fr'Updated total and average for server ({input_server_id}) in table {input_table}.')
        return fr'Reset Kevin\'s current record to zero. Not upset, just disappointed.'

    except Exception as error:
        print(fr'An error occured during an SQL update for total and average for server ({input_server_id}) in table {input_table}: {error}')
        return fr'There was an error resetting the records in the database: {error}'


# Built-in slash commands:
@bot.slash_command(description=fr'Get current Kevin stats.', guild_ids=BadKevinBotID)
async def stats(context: discord.ApplicationContext):
    server_id = context.guild.id
    check_for_server_entry(server_id)
    embed = discord.Embed(
        title=fr'Kevin\'s current stats:',
        color=discord.Color.purple()
    )
    stat_query = query_database('global_stats', server_id)
    embed.add_field(name='Best Record', value=fr'{stat_query[2]}', inline=False)
    embed.add_field(name='Streak Average:', value=fr'{stat_query[3]}', inline=False)
    embed.add_field(name='Total Resets:', value=fr'{stat_query[1]}', inline=False)
    embed.add_field(name='Last Wacko Message:', value=fr'{stat_query[4]}', inline=False)
    await context.respond(embed=embed)


@bot.slash_command(description=fr'Set the voice channel that will be renamed to keep track of Kevin\'s current record.', guild_ids=BadKevinBotID)
async def set_tracking_channel(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    server_id = interaction.guild.id
    check_for_server_entry(server_id)
    channel_id = discord.utils.get(bot.get_all_channels(), name=f'{channel_name}').id
    update_channel = update_channel_id('global_stats', server_id, channel_id)
    await interaction.response.send_message(f'{update_channel}', ephemeral=True)


@bot.slash_command(description='Advance Kevin 1 day.', guild_ids=BadKevinBotID)
async def advance(interaction: discord.Interaction):
    server_id = interaction.guild.id
    check_for_server_entry(server_id)
    databaseCursor.execute(fr'SELECT channel_id FROM global_stats WHERE server_id={server_id}')
    channel_id = databaseCursor.fetchone()[0]

    if channel_id is None:
        await interaction.response.send_message(fr'The channel the bot needs to edit doesn\'t appear to be set. You can set it with the **\\set_tracking_channel command**', ephemeral=True)
    else:
        voice_channel = bot.get_channel(channel_id)
        voice_channel_number = re.findall(r'\d+', voice_channel.name)[0]
        voice_channel_update = voice_channel.name.replace(voice_channel_number, str(int(voice_channel_number)+1), 1)

        try:
            await voice_channel.edit(name=voice_channel_update)
            print(fr'Successfully renamed channel {voice_channel.id} to {voice_channel_update}.')
            await interaction.response.send_message(fr'Added 1 to Kevin\'s current record. Currently at {voice_channel_number} Way to go!', ephemeral=True)

        except Exception as error:
            print(fr'Failed to rename channel {voice_channel.id} to {voice_channel.name}: {error}')
            await interaction.response.send_message(
                fr'Failed to rename channel {voice_channel.id} to {voice_channel.name}: {error}', ephemeral=True)


@bot.slash_command(description='Reset the clock!', guild_ids=BadKevinBotID)
async def reset(context: discord.ApplicationContext):
    server_id = context.guild.id
    databaseCursor.execute(fr'SELECT channel_id FROM global_stats WHERE server_id={server_id}')
    channel_id = databaseCursor.fetchone()[0]

    if channel_id is None:
        await context.response.send_message(fr'The channel the bot needs to edit doesn\'t appear to be set. You can set it with the `\\set_tracking_channel command`', ephemeral=True)
    else:
        voice_channel = bot.get_channel(channel_id)
        voice_channel_number = re.findall(r'\d+', voice_channel.name)[0]
        voice_channel_reset = voice_channel.name.replace(voice_channel_number, '0', 1)

        try:
            await voice_channel.edit(name=voice_channel_reset)
            print(fr'Successfully reset channel {voice_channel.id} to {voice_channel_reset}.')
            await context.response.send_message(fr'Reset Kevin\'s current record. A graceful fall from {voice_channel_number}. We\'re not upset, just disappointed.', ephemeral=True)

        except Exception as error:
            print(fr'Failed to reset channel {voice_channel.id} to {voice_channel.name}: {error}')
            await context.response.send_message(fr'Failed to reset channel {voice_channel.id} to {voice_channel.name}: {error}', ephemeral=True)

        reset_current_record('global_stats', server_id, voice_channel_number)
        # Probably move this function logic in here to later edit the reponse based on new records and such.


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
                    server_id = interaction.guild.id
                    databaseCursor.execute(fr'SELECT channel_id FROM global_stats WHERE server_id={server_id}')
                    channel_id = databaseCursor.fetchone()[0]

                    voice_channel = bot.get_channel(channel_id)
                    voice_channel_number = re.findall(r'\d+', voice_channel.name)[0]
                    voice_channel_reset = voice_channel.name.replace(voice_channel_number, '0', 1)

                    try:
                        await voice_channel.edit(name=voice_channel_reset)
                        print(fr'Successfully reset channel {voice_channel.id} to {voice_channel_reset}.')
                        await context.response.send_message(
                            fr'Reset Kevin\'s current record. A graceful fall from {voice_channel_number}. We\'re not upset, just disappointed.',
                            ephemeral=True)

                    except Exception as error:
                        print(fr'Failed to reset channel {voice_channel.id} to {voice_channel.name}: {error}')
                        await context.response.send_message(
                            fr'Failed to reset channel {voice_channel.id} to {voice_channel.name}: {error}',
                            ephemeral=True)
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


# Simplified loop, eventually will use DateTime objects that can keep track of other changes such as reports.
@tasks.loop(hours=24)
async def daily_update():
    databaseCursor.execute(fr'SELECT server_id FROM global_stats')
    servers = databaseCursor.fetchall()
    server_list = list(sum(servers, ()))
    for server in server_list:
        server_id = server
        databaseCursor.execute(fr'SELECT channel_id FROM global_stats WHERE server_id={server_id}')
        channel_id = databaseCursor.fetchone()[0]

        if channel_id is None:
            pass
        else:
            voice_channel = bot.get_channel(channel_id)
            voice_channel_number = re.findall(r'\d+', voice_channel.name)[0]
            voice_channel_update = voice_channel.name.replace(voice_channel_number, str(int(voice_channel_number)+1), 1)

            try:
                await voice_channel.edit(name=voice_channel_update)
                print(fr'Successfully renamed channel {voice_channel.id} to {voice_channel_update}.')

            except Exception as error:
                print(fr'Failed to rename channel {voice_channel.id} to {voice_channel.name}: {error}')


@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user.name}')
    daily_update.start()


bot.run(clientSecret)
