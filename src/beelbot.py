import discord
import asyncio
import boto3
import time
import json
from datetime import datetime
from discord.ext import commands 

# create discord bot 
prefix = "$"
bot = commands.Bot(command_prefix=prefix)

# get bot token from config.txt
botToken = None 
arn = None
with open('config.txt', 'r') as f:
    botToken = f.readline().strip()
    id = f.readline().strip()
    secret = f.readline().strip()

# setting up sqs client connection
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id = id,
    aws_secret_access_key = secret,
    region_name = 'us-east-1'
)

# get the url of the queue to be used 
queue_info = sqs_client.get_queue_url(QueueName = 'BeelBot-Queue')
queue_url = queue_info['QueueUrl']

@bot.event 
async def on_ready():
    print('Beel is online.')

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

@bot.command()
async def send_test(ctx, arg):
    response = sqs_client.send_message(
        QueueUrl = queue_url,
        MessageBody = arg,
    )
    await ctx.send(response)

@bot.command()
async def var_test(ctx):
    # await ctx.send(ctx.author.id)
    # await ctx.send(type(ctx.author.id))
    await ctx.send(time.time())
    await ctx.send(type(time.time()))
    await ctx.send(
        datetime.utcfromtimestamp(time.time())
    )

@bot.command()
async def medalsKL(ctx, medals, kl = -1):

    recordTime = time.time()            # snapshot time of entry in unix time

    # convert data to json to retain data structures later
    body = json.dumps({
        "cmd": "medalsKL",              # command arg identifier for later
        "id": ctx.author.id,            # author's discord id (int)
        "serverID": ctx.guild.id,       # server id of the message (int)
        "channelID": ctx.channel.id,    # channel message was sent (int)
        "medals": medals,               # medals (string)
        "kl": kl,                       # kl (int)
        "time": recordTime              # unix time (float)
    })

    # send the message to sqs beelbot queue
    response = sqs_client.send_message(
        QueueUrl = queue_url,
        MessageBody = body
    )

@bot.command()
async def recordSR(ctx, mpm, runTime = -1, stage = -1):

    recordTime = time.time()            # snapshot time of entry in unix time 

    # convert data to json to retain data structures later 
    body = json.dumps({
        "cmd": "recordSR",              # command arg identifier for later
        "id": ctx.author.id,            # author's discord id (int)
        "serverID": ctx.guild.id,       # server id (int)
        "channelID": ctx.channel.id,    # channel id (int)
        "mpm": mpm,                     # mpm (string)
        "runTime": runTime,             # time of run (int)
        "stage": stage,                 # ending stage (int)
        "time": recordTime              # time of recording (float)
    })

    # send the message to sqs 
    response = sqs_client.send_message(
        QueueUrl = queue_url,
        MessageBody = body
    )
    

# start the bot
bot.run(botToken)