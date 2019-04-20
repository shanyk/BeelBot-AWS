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

    put_medals(ddb, bodyDict, webhook)

    data = {
        "content": body
    }
    
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
def put_medals(ddb, data, webhook):

    # pull out medals data for slicing purposes
    medal = data['medals']

    # building the new item (refer to boto3 documentation)
    item = {            
        'id': {
            'N': str(data['id'])      # partition key is id + timestamp
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
    
    # query the last medals entry
    last_medals_entry = ddb.query(
        TableName = 'beelbot',
        Limit = 1,
        ScanIndexForward = False,
        ExpressionAttributeValues = {
            ':id': {'N' :str(data['id'])}
        },
        KeyConditionExpression = 'id = :id',
        ProjectionExpression = 'medals_num, medals_char_num'
    )
    
    # last kl variable for scope
    last_kl = None
    last_medals = None

    # if there is no previous medals entry then there are no returned items
    if not last_medals_entry['Items']:
        pass 
    else:
        # get the last medals
        last_medals = last_medals_entry['Items'][0]
        # query the last kl entry
        last_kl_entry = ddb.query(
            TableName = 'beelbot',
            Limit = 1,
            ScanIndexForward = False,
            ExpressionAttributeValues = {
                ':id': {'N': str(data['id'])},
                ':noKL': {'N': str(-1)}
            },
            KeyConditionExpression = 'id = :id',
            FilterExpression = 'kl > :noKL',
            ProjectionExpression = 'kl'
        )
        
        # if there is no previous entry by the id then ScannedCount == 0
        # skip querying for kl if there is no preivous entry
        if last_kl_entry['ScannedCount'] == 0:
            pass   
        else:
            # get the last evaluated key for use just in case no kl was returned
            last_evaluated_key = last_kl_entry['LastEvaluatedKey']
            
            while not last_kl_entry['Items']:
                print(last_evaluated_key)
                last_kl_entry = ddb.query(
                    TableName = 'beelbot',
                    Limit = 1,
                    ScanIndexForward = False,
                    ExpressionAttributeValues = {
                        ':id': {'N': str(data['id'])},
                        ':noKL': {'N': str(-1)}
                    },
                    KeyConditionExpression = 'id = :id',
                    FilterExpression = 'kl > :noKL',
                    ProjectionExpression = 'kl',
                    ExclusiveStartKey = last_evaluated_key
                )
                
                # if there are no more entries to check break the loop
                if last_kl_entry['ScannedCount'] == 0:
                    break
                else:   # set new last evaluated key
                    last_evaluated_key = last_kl_entry['LastEvaluatedKey']
            
            # get the last kl if it exists
            if last_kl_entry['Items']:
                last_kl = last_kl_entry['Items'][0]['kl']['N']
            else:
                pass

    # place the new item in beelbot database
    put_response = ddb.put_item(
        Item = item,
        TableName = 'beelbot'
    )
    
    print(last_medals)
    print(last_kl)
    
    if not last_medals_entry['Items']:
        requests.post(webhook, {'content': 'Your first medals record has been made!'})
    else:
        requests.post(webhook, {'content': last_medals})