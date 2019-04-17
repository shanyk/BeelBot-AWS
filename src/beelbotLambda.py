import boto3
import time 
import json
import requests
from datetime import datetime     

def lambda_handler(event, context):

    ssm = boto3.client('ssm')
    webhook_parameter = ssm.get_parameter(Name='testChannelWebhook')
    webhook = webhook_parameter['Parameter']['Value']

    ddb = boto3.client('dynamodb')

    print(webhook)
    
    body = event['Records'][0]['body']
    print(body)
    bodyDict = json.loads(body)
    print(type(bodyDict))

    put_medals(ddb, bodyDict)

    data = {
        "content": body
    }

    requests.post(webhook, data)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

'''
    input an entry about medals and KL in to db

    ddb = database client
    data = dictionary of data

    data needs to be converted to strings because dynamodb says so
'''
def put_medals(ddb, data):

    # pull out medals data for slicing purposes
    medal = data['medals']

    # building the item (refer to boto3 documentation)
    item = {            
        'id': {
            'N': str(data['id']) + str(data['time'])        # partition key is id + timestamp
            },
        'timestamp': {
            'N': str(data['time'])
            },
        'server_id': {
            'N': str(data['serverID'])
            },
        'channel_id': {
            'N': str(data['channelID'])
            },
        'medals': {
            'S': medal
            },
        'medals_num': {
            'N': medal[:-1]                 # split off the numbers from the medals string
            },
        'medals_char_num': {
            'N': str(ord(medal[-1:]))       # split off the char from medals string
            },                              # will be used for table sorting
        'kl': {
            'N': str(data['kl'])
            }
    }

    # place item in beelbot database
    response = ddb.put_item(
        Item = item,
        TableName = 'beelbot'
    )

    print('PutItem Successful')


