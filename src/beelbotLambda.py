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
    
    print(event)
    body = event['Records'][0]['body']
    print(body)
    bodyDict = json.loads(body)
    print(type(bodyDict))

    # medals = get_medals(ddb, bodyDict['id'], bodyDict['cmd'])
    put_medals(ddb, bodyDict, webhook)
    
    # print(medals)

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
            },
        'cmd': {
            'S': data['cmd']                # command used to filter results later
        }
    }
    
    
    # last kl variable for scope
    last_kl = None
    last_medals = get_medals(ddb, data['id'], data['cmd'])

    # if there is no previous medals entry then there are no returned items
    if last_medals == None:
        pass 
    else:
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
    
    if last_medals == None:
        requests.post(webhook, {'content': 'Your first medals record has been made!'})
    else:
        requests.post(webhook, {'content': last_medals})

'''
    gets the most recent medal data from the database

    returns tuple of floats (medals_prefix_number, medals_character_number) if there is data
    returns None if there is no medals data
'''
def get_medals(ddb, id, cmd):

    # variable to be returned
    last_medals = None

    # query to the database for medals prefix number and char code
    recent_medals_entries = ddb.query(
        TableName = 'beelbot',
        ScanIndexForward = False,   # sort query by timestamp descending, most recent on top
        ExpressionAttributeValues = {
            ':id': {'N': str(id)},
            ':cmd': {'S': cmd}
        },
        KeyConditionExpression = 'id = :id',
        FilterExpression = 'cmd = :cmd',
        ProjectionExpression = 'medals_num, medals_char_num'
    )

    # if no items are returned from the query then there is no medals
    # data on record, return None
    # else proceed with extracting medals data
    if not recent_medals_entries['Items']:
        return last_medals
    else:
        most_recent_entry = recent_medals_entries['Items'][0]   # most recent entry at 0 position

        medals_prefix_num = most_recent_entry['medals_num']['N']
        medals_char_num = most_recent_entry['medals_char_num']['N']

        return (float(medals_prefix_num), float(medals_char_num))




