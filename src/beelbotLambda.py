import discord
import asyncio
import boto3
import time 
from datetime import datetime 

def lambda_handler(event, context):
    # TODO implement
    print(event)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

