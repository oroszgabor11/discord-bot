#To run the code: python bot.py
#To stop the bot: terminal Ctrl+C
#bot token is in config.txt
#Variable to store the value name
#List of channel names where the bot will increment user values
#List of channel names where the bot will accept commands
#Replace 'Admin' with the required role name


import discord
from discord.ext import commands
import json
from datetime import datetime

# Load the bot token from config.txt
with open('config.txt', 'r') as file:
    TOKEN = file.read().strip()

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

# Save user values to a JSON file
def save_user_values():
    with open('user_values.json', 'w') as file:
        json.dump(user_values, file)

# Check if the user has the required role
def has_role(ctx, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    return role in ctx.author.roles

# Variable to store the value name
value_name = "value"

# List of channel names where the bot will increment user values
increment_channels = ["general", "chat", "discussion"]  # Line with increment channels

# List of channel names where the bot will accept commands
command_channels = ["commands", "bot-commands"]  # Line with command channels

# Command to add a user with a base value of 0
@bot.command()
@commands.has_role('Admin')  # Replace 'Admin' with the required role name
async def add_user(ctx, user: discord.Member):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) not in user_values:
        user_values[str(user.id)] = {value_name: 0, 'last_changed': str(datetime.now())}
        save_user_values()
        await ctx.send(f'User {user.name} added with a base {value_name} of 0.')
    else:
        await ctx.send(f'User {user.name} already exists.')

# Command to change a user's value
@bot.command()
@commands.has_role('Admin')  # Replace 'Admin' with the required role name
async def change_value(ctx, user: discord.Member, amount: int):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) in user_values:
        new_value = user_values[str(user.id)][value_name] + amount
        if new_value < 0:
            await ctx.send(f'Error: {user.name}\'s {value_name} cannot go below zero.')
        else:
            user_values[str(user.id)][value_name] = new_value
            user_values[str(user.id)]['last_changed'] = str(datetime.now())
            save_user_values()
            await ctx.send(f'User {user.name}\'s {value_name} changed by {amount}.')
    else:
        await ctx.send(f'User {user.name} does not exist.')

# Command to delete a user
@bot.command()
@commands.has_role('Admin')  # Replace 'Admin' with the required role name
async def delete_user(ctx, user: discord.Member):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) in user_values:
        del user_values[str(user.id)]
        save_user_values()
        await ctx.send(f'User {user.name} deleted.')
    else:
        await ctx.send(f'User {user.name} does not exist.')

# Command to change a user's name
@bot.command()
@commands.has_role('Admin')  # Replace 'Admin' with the required role name
async def change_name(ctx, user: discord.Member, new_name: str):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    if str(user.id) in user_values:
        user_values[str(user.id)]['name'] = new_name
        save_user_values()
        await ctx.send(f'User {user.name}\'s name changed to {new_name}.')
    else:
        await ctx.send(f'User {user.name} does not exist.')

# Command to show all users' values
@bot.command()
@commands.has_role('Admin')  # Replace 'Admin' with the required role name
async def show_all(ctx):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    message = 'User values:\n'
    for user_id, data in user_values.items():
        user = await bot.fetch_user(user_id)
        message += f'{user.name}: {data[value_name]} (Last changed: {data["last_changed"]})\n'
    await ctx.send(message)

# Command to show a user's value and DM them
@bot.command()
async def show_value(ctx):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    user_id = str(ctx.author.id)
    if user_id in user_values:
        data = user_values[user_id]
        try:
            custom_message = f'You have {data[value_name]} {value_name}. Last changed: {data["last_changed"]}'
            await ctx.author.send(custom_message)
            await ctx.send('I have sent you a DM with your value.')
        except discord.Forbidden:
            await ctx.send('I could not send you a DM. Please check your privacy settings.')
    else:
        await ctx.send('You do not have a value yet.')

# Command to change the value name (e.g., points, score)
@bot.command()
@commands.has_role('Admin')  # Replace 'Admin' with the required role name
async def change_value_name(ctx, new_name: str):
    if ctx.channel.name not in command_channels:
        await ctx.send(f'Commands are not allowed in this channel.')
        return
    global value_name
    value_name = new_name
    await ctx.send(f'Value name changed to {new_name}.')

# Event to increment user's value when they send a message in specified channels
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message is in one of the specified channels
    if message.channel.name in increment_channels:
        user_id = str(message.author.id)
        if user_id in user_values:
            user_values[user_id][value_name] += 1
            user_values[user_id]['last_changed'] = str(datetime.now())
        else:
            user_values[user_id] = {value_name: 1, 'last_changed': str(datetime.now())}
        save_user_values()

    await bot.process_commands(message)

# Run the bot
bot.run(TOKEN)
