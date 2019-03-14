import discord
import asyncio
from discord.ext import commands 

# create discord bot 
prefix = "$"
bot = commands.Bot(command_prefix=prefix)

# get bot token from config.txt
botToken = None 
with open('config.txt', 'r') as f:
    botToken = f.readline().strip()

@bot.event 
async def on_ready():
    print('Beel is online.')

# @bot.command()
# async def test(ctx, arg1, arg2):
#     print(arg1, arg2)
#     await ctx.send(arg1, arg2)

@bot.command()
async def ping(ctx):
    '''
    This text will be shown in the help command
    '''

    # Get the latency of the bot
    latency = bot.latency  # Included in the Discord.py library
    # Send it to the user
    print(ctx)
    await ctx.send(latency)

@bot.command()
async def offline(ctx):	
	'''
		Admin command to take the bot offline

		Arguments:
		ctx -- message object read by the bot
	'''
	if 'Admin' in [role.name for role in ctx.author.roles]:	
		await ctx.send('Going offline...')
		await bot.close()
	else:
		await ctx.send('Nice try')
		return

bot.run(botToken)