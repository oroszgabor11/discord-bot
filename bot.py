import discord
from discord.ext import commands
import json
from datetime import datetime
import pandas as pd
import random
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load the bot token from config.txt
with open('config.txt', 'r') as file:
    TOKEN = file.read().strip()

# Load configuration from a JSON file
with open('config.json', 'r') as file:
    config = json.load(file)

value_name = config['value_name']
increment_channels = config['increment_channels']
command_channels = config['command_channels']
admin_role = config['admin_role']
super_admin_role = config['super_admin_role']
custom_message = config['custom_message']

# Define the intents
intents = discord.Intents.default()
intents.members = True  # Enable the members intent
intents.message_content = True  # Enable the message content intent

# Define the bot and the command prefix
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store user values
user_values = {}

# Load user values from a JSON file (if it exists)
try:
    with open('user_values.json', 'r') as file:
        user_values = json.load(file)
except FileNotFoundError:
    pass

# Save configuration to a JSON file
def save_config():
    global config
    config['value_name'] = value_name
    config['increment_channels'] = increment_channels
    config['command_channels'] = command_channels
    config['admin_role'] = admin_role
    config['super_admin_role'] = super_admin_role
    config['custom_message'] = custom_message
    with open('config.json', 'w') as file:
        json.dump(config, file)

# Get the guild ID from the context
def get_guild_id(ctx):
    return ctx.guild.id

# Check if the user has the required role
def has_role(ctx, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    return role in ctx.author.roles

# Command to set the admin role
@bot.command()
@commands.has_role(super_admin_role)
async def set_admin_role(ctx, role_name: str):
    global admin_role
    admin_role = role_name
    save_config()
    await ctx.send(f'Admin role set to {role_name}.')

# Check if the user has either the admin role or the super admin role
def is_admin_or_super_admin():
    def predicate(ctx):
        admin_role_obj = discord.utils.get(ctx.guild.roles, name=admin_role)
        super_admin_role_obj = discord.utils.get(ctx.guild.roles, name=super_admin_role)
        return admin_role_obj in ctx.author.roles or super_admin_role_obj in ctx.author.roles
    return commands.check(predicate)

# Command to add a user with a base value of 0
@bot.command()
@is_admin_or_super_admin()
async def add_user(ctx, user: discord.Member):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) not in user_values:
        user_values[str(user.id)] = {value_name: 0, 'last_changed': str(datetime.now())}
        save_user_values()
        await ctx.send(f'User {user.display_name} added with a base {value_name} of 0.')
        print(f'User {user.display_name} added with a base {value_name} of 0.')
    else:
        await ctx.send(f'User {user.display_name} already exists.')

# Command to change a user's value
@bot.command()
@is_admin_or_super_admin()
async def change_value(ctx, amount: int, *users: discord.Member):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    for user in users:
        if str(user.id) in user_values:
            new_value = user_values[str(user.id)][value_name] + amount
            if new_value < 0:
                await ctx.send(f'Error: {user.display_name}\'s {value_name} cannot go below zero.')
            else:
                user_values[str(user.id)][value_name] = new_value
                user_values[str(user.id)]['last_changed'] = str(datetime.now())
                save_user_values()
                await ctx.send(f'User {user.display_name}\'s {value_name} changed by {amount}.')
                print(f'User {user.display_name}\'s {value_name} changed by {amount}.')
        else:
            await ctx.send(f'User {user.display_name} does not exist.')

# Command to delete a user
@bot.command()
@is_admin_or_super_admin()
async def delete_user(ctx, user: discord.Member):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) in user_values:
        del user_values[str(user.id)]
        save_user_values()
        await ctx.send(f'User {user.display_name} deleted.')
        print(f'User {user.display_name} deleted.')
    else:
        await ctx.send(f'User {user.display_name} does not exist.')

# Set the custom message
@bot.command()
@commands.has_role(super_admin_role)
async def set_custom_message(ctx, *, message: str):
    global custom_message
    custom_message = message
    save_config()
    await ctx.send(f'Custom message set to: {message}')
    print(f'Custom message set to: {message}')

# Command to change a user's name
@bot.command()
@is_admin_or_super_admin()
async def change_name(ctx, user: discord.Member, new_name: str):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) in user_values:
        user_values[str(user.id)]['name'] = new_name
        save_user_values()
        await ctx.send(f'User {user.display_name}\'s name changed to {new_name}.')
        print(f'User {user.display_name}\'s name changed to {new_name}.')
    else:
        await ctx.send(f'User {user.display_name} does not exist.')

# Command to show all users' values
@bot.command()
@is_admin_or_super_admin()
async def show_all(ctx):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    guild = ctx.guild
    members = await guild.fetch_members(limit=None).flatten()

    user_messages = []
    for member in members:
        user_id = str(member.id)
        if user_id in user_values:
            data = user_values[user_id]
            user_messages.append(f'{member.display_name}: {data[value_name]} (Last changed: {data["last_changed"]})')

    if user_messages:
        message = 'User values:\n' + '\n'.join(user_messages)
    else:
        message = 'No user values found.'

    await ctx.send(message)
    print('Displayed all user values.')

# Command to show a specific user's value to an admin
@bot.command()
@is_admin_or_super_admin()
async def show_value(ctx, user: discord.Member):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    user_id = str(user.id)
    if user_id in user_values:
        data = user_values[user_id]
        custom_message = f'{user.display_name} has {data[value_name]} {value_name}. Last changed: {data["last_changed"]}'
        await ctx.send(custom_message)
        print(f'Displayed value for user {user.display_name}.')
    else:
        await ctx.send(f'{user.display_name} does not have a value yet.')

# Command to change the value name (e.g., points, score)
@bot.command()
@commands.has_role(super_admin_role)
async def change_value_name(ctx, new_name: str):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    global value_name
    value_name = new_name
    save_config()
    await ctx.send(f'Value name changed to {new_name}.')
    print(f'Value name changed to {new_name}.')

# Command to show a user's value and DM them
@bot.command()
async def myvalue(ctx):
    user_id = str(ctx.author.id)
    if user_id in user_values:
        data = user_values[user_id]
        try:
            # Use the custom message format and include custom emojis
            message = custom_message.format(value=data[value_name], value_name=value_name, last_changed=data["last_changed"])
            await ctx.author.send(message)
            await ctx.send('I have sent you a DM with your value.')
            print(f'Sent value to user {ctx.author.display_name} via DM.')
        except discord.Forbidden:
            await ctx.send('I could not send you a DM. Please check your privacy settings.')
    else:
        await ctx.send('You do not have a value yet.')

# Command to set increment channels
@bot.command()
@commands.has_role(super_admin_role)
async def set_increment_channels(ctx, *channels: str):
    global increment_channels
    increment_channels = list(channels)
    save_config()
    await ctx.send(f'Increment channels set to: {", ".join(increment_channels)}')
    print(f'Increment channels set to: {", ".join(increment_channels)}')

# Command to set command channels
@bot.command()
@commands.has_role(super_admin_role)
async def set_command_channels(ctx, *channels: str):
    global command_channels
    command_channels = list(channels)
    save_config()
    await ctx.send(f'Command channels set to: {", ".join(command_channels)}')
    print(f'Command channels set to: {", ".join(command_channels)}')

# Command to upload an Excel file with nicknames
@bot.command()
@commands.has_role(super_admin_role)
async def upload_excel(ctx):
    if len(ctx.message.attachments) != 1:
        await ctx.send("Please attach one Excel file.")
        return

    attachment = ctx.message.attachments[0]
    await attachment.save('user_values.xlsx')
    print('Excel file uploaded.')

    df = pd.read_excel('user_values.xlsx')
    for index, row in df.iterrows():
        nickname = row['Nickname']
        value = row['Value']
        member = discord.utils.get(ctx.guild.members, nick=nickname)
        if member:
            user_id = str(member.id)
            user_values[user_id] = {
                value_name: value,
                'last_changed': str(datetime.now())
            }
    save_user_values()
    await ctx.send("User values updated from Excel file.")
    print('User values updated from Excel file.')

# Command to download the JSON file into an Excel file with nicknames
@bot.command()
@commands.has_role(super_admin_role)
async def download_excel(ctx):
    try:
        data = []
        for user_id, values in user_values.items():
            user = await bot.fetch_user(user_id)
            member = ctx.guild.get_member(user.id)
            nickname = member.nick if member.nick else user.name
            data.append({
                'Nickname': nickname,
                'Value': values[value_name],
                'Last Changed': values['last_changed']
            })

        df = pd.DataFrame(data)
        df.to_excel('user_values.xlsx', index=False)

        await ctx.send(file=discord.File('user_values.xlsx'))
        print('User values downloaded to Excel file.')
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

# Custom help command
@bot.command(name="help_me")
async def custom_help(ctx):
    embed = discord.Embed(title="Help", description="List of available commands", color=0x00ff00)
    if has_role(ctx, super_admin_role):
        embed.add_field(name="!set_admin_role", value="Set the admin role", inline=False)
        embed.add_field(name="!set_increment_channels", value="Set the increment channels", inline=False)
        embed.add_field(name="!set_command_channels", value="Set the command channels", inline=False)
        embed.add_field(name="!change_value_name", value="Change the value name", inline=False)
        embed.add_field(name="!upload_excel", value="Upload an Excel file with nicknames", inline=False)
        embed.add_field(name="!download_excel", value="Download the JSON file into an Excel file with nicknames", inline=False)
        embed.add_field(name="!add_user", value="Add a user with a base value of 0", inline=False)
        embed.add_field(name="!change_value", value="Change a user's value", inline=False)
        embed.add_field(name="!delete_user", value="Delete a user", inline=False)
        embed.add_field(name="!change_name", value="Change a user's name", inline=False)
        embed.add_field(name="!show_value", value="Show a specific user's value", inline=False)
        embed.add_field(name="!set_custom_message", value="Set the custom message for showing values", inline=False)
    elif has_role(ctx, admin_role):
        embed.add_field(name="!add_user", value="Add a user with a base value of 0", inline=False)
        embed.add_field(name="!change_value", value="Change a user's value", inline=False)
        embed.add_field(name="!delete_user", value="Delete a user", inline=False)
        embed.add_field(name="!change_name", value="Change a user's name", inline=False)
        embed.add_field(name="!show_value", value="Show a specific user's value", inline=False)
    embed.add_field(name="!myvalue", value="Show your value", inline=False)
    
    try:
        await ctx.author.send(embed=embed)
        await ctx.send("I have sent you a DM with the help information.")
        print('Help information sent via DM.')
    except discord.Forbidden:
        await ctx.send("I couldn't send you a DM. Please check your privacy settings.")

# Event listener for new members
@bot.event
async def on_member_join(member):
    user_id = str(member.id)
    if user_id not in user_values:
        user_values[user_id] = {value_name: 0, 'last_changed': str(datetime.now())}
        save_user_values()
        print(f'New member {member.display_name} added with a base {value_name} of 0.')

# Event listener for member removal
@bot.event
async def on_member_remove(member):
    user_id = str(member.id)
    if user_id in user_values:
        del user_values[user_id]
        save_user_values()
        print(f'Member {member.display_name} removed.')

# Event listener for message commands
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Increment user value if the message is in an increment channel
    if message.channel.name in increment_channels:
        user_id = str(message.author.id)
        if user_id not in user_values:
            user_values[user_id] = {value_name: 0, 'last_changed': str(datetime.now())}
            print(f'User {message.author.display_name} added with a base {value_name} of 0.')
        user_values[user_id][value_name] += 1
        user_values[user_id]['last_changed'] = str(datetime.now())
        save_user_values()
        print(f'User {message.author.display_name}\'s {value_name} incremented by 1.')

    await bot.process_commands(message)

# Function to add all existing members to the user list upon startup
async def add_existing_members():
    await bot.wait_until_ready()
    for guild in bot.guilds:
        for member in guild.members:
            user_id = str(member.id)
            if user_id not in user_values:
                user_values[user_id] = {value_name: 0, 'last_changed': str(datetime.now())}
                print(f'Existing member {member.display_name} added with a base {value_name} of 0.')
    save_user_values()

# Run the bot
async def main():
    async with bot:
        bot.loop.create_task(add_existing_members())
        await bot.start(TOKEN)

asyncio.run(main())
