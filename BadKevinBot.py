import os
import re
import pymysql.cursors
from dotenv import load_dotenv
import discord
from discord.ext import tasks

# ---------- VARIABLES AND INFORMATION ----------
# Load the environment file for protected Discord Bot information.
load_dotenv()
publicKey = os.environ.get('PUBLICKEY')
clientID = os.environ.get('CLIENTID')
clientSecret = os.environ.get('CLIENTSECRET')
sqlPassword = os.environ.get('SQLPASSWORD')
BadKevinBotID = [1205001660145995776]
kevin_author_id = 200696839639531523

intents = discord.Intents.default()
bot = discord.Bot()

database_connection = pymysql.connect(
    host='gamesnj409.bisecthosting.com',
    user='u82778_voWyKm3ryk',
    passwd=sqlPassword,
    database='s82778_DayLeaderboard',
    port=3306,
    # cursorclass=pymysql.cursors.DictCursor
)
database_cursor = database_connection.cursor()


# Database-based logic
def check_for_server_entry(input_server_id):  # This is a common function that ensures a server already has an entry with settings. If not it creates one with default settings.
    database_cursor.execute(fr'SELECT server_id FROM global_stats WHERE server_id = {input_server_id}')
    if database_cursor.fetchone() is None:
        try:
            database_cursor.execute(fr'INSERT INTO global_stats (server_id, total_reset_amount, best_record, streak_average, last_wacko_message) VALUES ({input_server_id}, 0, 0, 0, "No messages found.")')
            database_connection.commit()

        except Exception as error:
            raise fr'This server wasn\'t found in the database, and an error adding this server to the database occured: {error}'
    else:
        pass


def query_database(input_table, input_server_id):
    try:
        database_cursor.execute(fr'SELECT channel_id FROM {input_table} WHERE server_id = {input_server_id}')
        channel_id_value = database_cursor.fetchone()[0]
        database_cursor.execute(fr'SELECT total_reset_amount FROM {input_table} WHERE server_id = {input_server_id}')
        total_reset_amount_value = database_cursor.fetchone()[0]
        database_cursor.execute(fr'SELECT best_record FROM {input_table} WHERE server_id = {input_server_id}')
        best_record_value = database_cursor.fetchone()[0]
        database_cursor.execute(fr'SELECT streak_average FROM {input_table} WHERE server_id = {input_server_id}')
        streak_average_value = database_cursor.fetchone()[0]
        database_cursor.execute(fr'SELECT last_wacko_message FROM {input_table} WHERE server_id = {input_server_id}')
        last_wacko_message_value = database_cursor.fetchone()[0]

        return channel_id_value, total_reset_amount_value, best_record_value, streak_average_value, last_wacko_message_value

    except Exception as error:
        print(fr'An error occured where querying from table {input_table} for server {input_server_id}: {error}')
        return fr'There was an error while querying the database.'


def update_channel_id(input_table, input_server_id, input_channel_id):
    try:
        database_cursor.execute(fr'UPDATE {input_table} SET channel_id = {input_channel_id} WHERE server_id = {input_server_id}')
        database_connection.commit()

        print(fr'Changed channel_id in {input_table} to {input_channel_id} for server: {input_server_id}')
        return fr'Updated the tracking channel to ID:{input_channel_id} for this server.'

    except Exception as error:
        print(fr'An error occured during an SQL update changing channel_id in {input_table} to {input_channel_id} in server: {input_server_id}: {error}')
        return fr'An error occured during an SQL update changing channel_id to {input_channel_id}: {error}'


# Built-in slash commands:
@bot.slash_command(description=fr'Information and commands/requirements for the bot.')
async def help(context: discord.ApplicationContext):
    help_embed = discord.Embed(
        title=fr'Kevin Bot information:',
        description=fr'This bot helps report Kevin for questionable content and allows server members to vote to decide if what he said is wacko or not. If a vote passes as wacko the bot will update a voice channel with a reset to his current record.',
        color=discord.Color.green()
    )
    help_embed.add_field(name='', value='', inline=False)
    help_embed.add_field(name='**General Information:**',
                         value=fr'This bot needs permissions to `read messages`, `post messages` with `embeds`, and the ability to `change channel names`. When a report is made it looks in the current channel only for recent messages hard coded for Kevin\'s user ID. The bot will also rename a designated channel every `24 hours`',
                         inline=False)
    help_embed.add_field(name='', value='', inline=False)
    help_embed.add_field(name='Commands:', value='', inline=False)
    help_embed.add_field(name='`/stats`',
                         value='This command will give the user a personel embed with the stats of Kevin based on the server. Keeps track of things like: Best Record, Streak Average, Total Resets.',
                         inline=False)
    help_embed.add_field(name='', value='', inline=False)
    help_embed.add_field(name='`/set_tracking_channel`',
                         value=fr'This is a command that allows users to set the channel in the server that will act as the tracker of Kevin\'s current record. The bot expects a number in the channel name as the day variable. If another number comes before it the bot may misinterpret where the variable is supposed to be. Only users that can control channels should have access to this command to avoid channel name manipulation.',
                         inline=False)
    help_embed.add_field(name='', value='', inline=False)
    help_embed.add_field(name='`/report`',
                         value=fr'This is the primary command that users should be able to have access to and start a report. Currently hard coded to 5 votes before a report is complete.',
                         inline=False)

    await context.respond(embed=help_embed, ephemeral=True)


@bot.slash_command(description=fr'Get current Kevin stats. [Work In Progress]')
async def stats(context: discord.ApplicationContext):
    if not database_connection.open:
        database_connection.ping(reconnect=True)

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

    await context.respond(embed=embed, ephemeral=True)


@bot.slash_command(description=fr'Set the voice channel that will be renamed to keep track of Kevin\'s current record.')
async def set_tracking_channel(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    if not database_connection.open:
        database_connection.ping(reconnect=True)
    
    server_id = interaction.guild.id
    check_for_server_entry(server_id)
    channel_id = discord.utils.get(bot.get_all_channels(), name=f'{channel_name}').id
    update_channel = update_channel_id('global_stats', server_id, channel_id)

    await interaction.response.send_message(f'{update_channel}', ephemeral=True, delete_after=60)


@bot.slash_command(description='Report Kevin for crimes agains the server...')
async def report(context: discord.ApplicationContext):
    if not database_connection.open:
        database_connection.ping(reconnect=True)
    
    server_id = context.guild.id
    check_for_server_entry(server_id)
    database_cursor.execute(fr'SELECT channel_id FROM global_stats WHERE server_id = {server_id}')
    channel_id = database_cursor.fetchone()[0]

    if channel_id is None:
        await context.response.send_message(fr'The channel the bot needs to edit doesn\'t appear to be set. The bot can\'t report correctly with out it. You can set it with the `\\set_tracking_channel command`', ephemeral=True)

    else:
        voice_channel = bot.get_channel(channel_id)
        if len(re.findall(r'\d+', voice_channel.name)) <= 0:
            print(fr'The channel name: `{voice_channel.name}` doesn\'t appear to have a record (number) in it. Ensure there is a number to act as the record somewhere.')
            await context.response.send_message(fr'The channel name: `{voice_channel.name}` doesn\'t appear to have a record (number) in it. Ensure there is a number to act as the record somewhere before reporting.', ephemeral=True)

        else:
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
                    if len(message.attachments) > 0:
                        message_content_preview = fr'{message_content_preview} | {message.attachments[0].filename}'[:99]
                    message_id = message.id
                    select_options.append(
                        discord.SelectOption(
                            label=f'{message_label}',
                            value=f'{message_id}',
                            description=f'{message_content_preview}'
                        )
                    )

            if len(select_options) <= 0:
                await context.response.send_message(fr'No messages from Kevin were found. This bot will only search messages in this channel to report. Ensure you\'re using the report command in the same channel.', ephemeral=True)

            else:
                if len(select_options) > 25:
                    select_options = select_options[:24]

                report_view = discord.ui.View(timeout=None)

                message_selection = discord.ui.Select(custom_id='Message Selection',
                                                      placeholder='The last few of Kevin\'s chat in this channel are below.',
                                                      options=select_options,
                                                      min_values=0,
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

                report_button = discord.ui.Button(label='Report', style=discord.ButtonStyle.red, custom_id='Report Button', disabled=True)

                async def report_button_callback(interaction: discord.Interaction):
                    report_view.disable_all_items()
                    embed_report = discord.Embed(
                        title='Report Submitted',
                        description='Your report should be visible below for all guild members to vote on below. Thank you for your service to this good Christian Discord.',
                        color=discord.Color.green(),
                    )
                    embed_report.set_footer(text='This message will disappear soon or can be dismissed.')

                    await interaction.response.edit_message(embed=embed_report, view=report_view, delete_after=30)

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

                    vote_view = discord.ui.View(timeout=86400, disable_on_timeout=True)

                    upvote_button = discord.ui.Button(label='Acceptable...', style=discord.ButtonStyle.green, emoji='🆗', custom_id='Upvote Button')

                    upvote_voter_array = []
                    downvote_voter_array = []
                    report_complete_flag = False

                    async def upvote_button_callback(upvote_interaction: discord.Interaction):
                        voter = upvote_interaction.user.id
                        nonlocal upvote_voter_array

                        if voter in upvote_voter_array:
                            upvote_voter_array.remove(voter)
                            new_upvote_value = int(vote_embed.fields[4].value.replace('`', '')) - 1

                        else:
                            upvote_voter_array.append(voter)
                            new_upvote_value = int(vote_embed.fields[4].value.replace('`', '')) + 1

                        vote_embed.set_field_at(index=4, name='Passes:', value=f'`{new_upvote_value}`', inline=True)

                        await upvote_interaction.response.edit_message(embed=vote_embed, view=vote_view)

                    upvote_button.callback = upvote_button_callback
                    vote_view.add_item(upvote_button)

                    downvote_button = discord.ui.Button(label='Wacko!', style=discord.ButtonStyle.red, emoji='😬', custom_id='Downvote Button')

                    async def downvote_button_callback(downvote_interaction: discord.Interaction):
                        voter = downvote_interaction.user.id
                        nonlocal downvote_voter_array

                        if voter in downvote_voter_array:
                            downvote_voter_array.remove(voter)
                            new_downvote_value = int(vote_embed.fields[5].value.replace('`', '')) - 1

                        else:
                            downvote_voter_array.append(voter)
                            new_downvote_value = int(vote_embed.fields[5].value.replace('`', '')) + 1
                            nonlocal report_complete_flag

                            if new_downvote_value >= 5 and report_complete_flag is False:
                                report_complete_flag = True

                                current_record = re.findall(r'\d+', voice_channel.name)[0]
                                voice_channel_reset = voice_channel.name.replace(current_record, '0', 1)

                                database_cursor.execute(fr'UPDATE global_stats SET total_reset_amount = total_reset_amount + 1 WHERE server_id = {server_id}')
                                database_connection.commit()
                                database_cursor.execute(fr'SELECT total_reset_amount FROM global_stats WHERE server_id = {server_id}')
                                total_reset_amount = database_cursor.fetchone()[0]
                                database_cursor.execute(fr'SELECT best_record FROM global_stats WHERE server_id = {server_id}')
                                best_record = database_cursor.fetchone()[0]
                                database_cursor.execute(fr'SELECT streak_average FROM global_stats WHERE server_id = {server_id}')
                                streak_average = database_cursor.fetchone()[0]

                                new_streak_average = round((int(streak_average) + int(current_record)) / int(total_reset_amount))
                                database_cursor.execute(fr'UPDATE global_stats SET streak_average = {new_streak_average} WHERE server_id = {server_id}')
                                database_connection.commit()

                                database_cursor.execute(fr'UPDATE global_stats SET last_wacko_message = "{message_content.content}" WHERE server_id = {server_id}')
                                database_connection.commit()

                                if int(best_record) <= int(current_record):
                                    try:
                                        database_cursor.execute(fr'UPDATE global_stats SET best_record = {current_record} WHERE server_id = {server_id}')
                                        database_connection.commit()

                                        vote_embed.set_field_at(index=3, name='', value=f'''```ansi
[2;31m[1;31mThe server has spoken and Kevin has been found guilty![0m[2;31m[0m
```
Kevin\'s record has been reset. A graceful fall from `{current_record}`. At least he got a new record, we do believe you can do better though Kevin!''', inline=False)
                                        vote_embed.set_image(url='https://alanlclack.blob.core.windows.net/alice-exe/discord/wackosmacko.png')

                                        await voice_channel.edit(name=voice_channel_reset)
                                        print(fr'Successfully reset channel based on votes {voice_channel.id} to {voice_channel_reset}.')

                                    except Exception as error:
                                        print(fr'Failed to reset channel based on votes {voice_channel.id} to {voice_channel.name}: {error}')
                                        await downvote_interaction.response.send_message(fr'Failed to reset channel {voice_channel.id} to {voice_channel.name}: {error}', ephemeral=True)

                                else:
                                    await voice_channel.edit(name=voice_channel_reset)
                                    print(fr'Successfully reset channel {voice_channel.id} to {voice_channel_reset}.')

                                    vote_embed.set_field_at(index=3, name='', value=f'''```ansi
[2;31m[1;31mThe server has spoken and Kevin has been found guilty![0m[2;31m[0m
```
Kevin\'s record has been reset. A less than graceful fall from `{current_record}`. We\'re not upset, just disappointed.''', inline=False)
                                    vote_embed.set_image(url='https://alanlclack.blob.core.windows.net/alice-exe/discord/wackosmacko.png')

                            else:
                                pass

                        vote_embed.set_field_at(index=5, name='Wacko:', value=f'`{new_downvote_value}`', inline=True)

                        await downvote_interaction.response.edit_message(embed=vote_embed, view=vote_view)

                    downvote_button.callback = downvote_button_callback
                    vote_view.add_item(downvote_button)

                    await context.respond(embed=vote_embed, view=vote_view)

                report_button.callback = report_button_callback
                report_view.add_item(report_button)

                await context.respond(embed=report_embed, view=report_view, ephemeral=True)


# Simplified loop, eventually will use DateTime objects that can keep track of other changes such as reports.
@tasks.loop(hours=24)
async def daily_update():
    database_connection_update = pymysql.connect(
        host='gamesnj409.bisecthosting.com',
        user='u82778_voWyKm3ryk',
        passwd=sqlPassword,
        database='s82778_DayLeaderboard',
        port=3306,
        # cursorclass=pymysql.cursors.DictCursor
    )
    database_cursor_update = database_connection_update.cursor()
    
    if not database_connection.open:
        database_connection.ping(reconnect=True)

    database_cursor_update.execute(fr'SELECT server_id FROM global_stats')
    servers = database_cursor_update.fetchall()
    server_list = list(sum(servers, ()))

    for server in server_list:
        server_id = server
        database_cursor_update.execute(fr'SELECT channel_id FROM global_stats WHERE server_id = {server_id}')
        channel_id = database_cursor_update.fetchone()[0]

        if channel_id is None:
            pass
        else:
            voice_channel = bot.get_channel(channel_id)
            if len(re.findall(r'-?\d+', voice_channel.name)) <= 0:
                print(fr'Skipping {voice_channel} due to having no numbers.')
                pass
            else:
                current_record = re.findall(r'-?\d+', voice_channel.name)[0]
                new_record = str(int(current_record) + 1)
                voice_channel_update = voice_channel.name.replace(current_record, new_record, 1)

                try:
                    await voice_channel.edit(name=voice_channel_update)
                    print(fr'Successfully daily updated channel {voice_channel.id} to {voice_channel_update}.')
                    database_cursor_update.execute(fr'SELECT best_record FROM global_stats WHERE server_id = {server_id}')
                    best_record = database_cursor_update.fetchone()[0]
                    if int(best_record) < int(current_record):
                        database_cursor_update.execute(fr'UPDATE global_stats SET best_record = {new_record} WHERE server_id = {server_id}')
                        database_connection.commit()

                    else:
                        pass

                except Exception as error:
                    print(fr'Failed to daily update channel {voice_channel.id} to {voice_channel.name}: {error}')

    if database_connection_update.open:
        database_connection_update.close()


@bot.event
async def on_ready():
    print(f'successfully finished startup')
    print(f'Bot is ready. Logged in as {bot.user.name}.')

    daily_update.start()


bot.run(clientSecret)
