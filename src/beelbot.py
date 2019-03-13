import discord
import asyncio
from discord.ext import commands 

# create discord bot 
bot = commands.Bot(command_prefix="$")

# get bot token from config.txt
botToken = None 
with open('config.txt', 'r') as f:
    botToken = f.readline().strip()

@bot.event 
async def on_ready():
    print('Beel is online.')

bot.run(botToken)