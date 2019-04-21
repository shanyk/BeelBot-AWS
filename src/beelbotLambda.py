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

    #put_medals(ddb, bodyDict, webhook)
    #kl = get_kl(ddb, bodyDict['id'], bodyDict['cmd'])
    
    message = None

    if bodyDict['cmd'] == 'medalsKL':
        message = medalsKL(ddb, bodyDict)
    
    requests.post(webhook, message)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
##########################################################################
'''
    message builder for the medalsKL command
    
    returns an object for a discord message
'''
def medalsKL(ddb, data):
    
    user_id = data['id']
    cmd = data['cmd']
    new_medals = data['medals']
    old_medals = get_medals(ddb, user_id, cmd)
    new_kl = data['kl']
    old_kl = get_kl(ddb, user_id, cmd)

    medals_content = None

    if old_medals == None:
        put_medals(ddb, data)
        medals_content = 'Your first entry has been made!'
    else:
        change = calc_progress(old_medals, new_medals)

        if change[0] == None:
            medals_content = 'Change was negative. Please check your data.'
        else:
            put_medals(ddb, data)
            
            info_str = f'{change[0]}, {change[1]}'

            medals_content = info_str
    
    kl_content = None
    
    if new_kl != -1 and old_kl != None:
        kl_content = new_kl - old_kl
    elif new_kl != -1 and old_kl == None:
        kl_content = 'New KL has been recorded'
    else:
        kl_content = 'No change in KL.'
    
    message_str = f'{medals_content}, {kl_content}'
    
    message = {
        'content': message_str
    }
    
    return message

##########################################################################
'''
    input an entry about medals and KL in to db

    ddb = database client
    data = dictionary of data

    data needs to be converted to strings because dynamodb says so
'''
def put_medals(ddb, data):

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

    # place the new item in beelbot database
    put_response = ddb.put_item(
        Item = item,
        TableName = 'beelbot'
    )

    print(put_response)


##########################################################################
'''
    gets the most recent medal data from the database

    returns tuple of floats (medals_prefix_number, medals_character_number) if there is data
    returns None if there is no medals data
'''
def get_medals(ddb, id, cmd):

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
        return None
    else:
        most_recent_entry = recent_medals_entries['Items'][0]   # most recent entry at 0 position

        medals_prefix_num = most_recent_entry['medals_num']['N']
        medals_char_num = most_recent_entry['medals_char_num']['N']

        return (float(medals_prefix_num), int(medals_char_num))


############################################################################
'''
    gets the most recent kl data from the database

    returns an int of the kl if data exists
    returns None is no data exists
'''
def get_kl(ddb, id, cmd):

    # query to database for valid kl info
    recent_kl_entries = ddb.query(
        TableName = 'beelbot',
        ScanIndexForward = False,
        ExpressionAttributeValues = {
            ':id': {'N': str(id)},
            ':cmd': {'S': cmd},
            ':valid': {'N': str(-1)} 
        },
        KeyConditionExpression = 'id = :id',
        FilterExpression = 'cmd = :cmd AND kl <> :valid',
        ProjectionExpression = 'kl'
    )

    # if no items are returned then there is no kl data
    # return None
    # else return the kl data
    if not recent_kl_entries['Items']:
        return None
    else:
        most_recent_kl_entry = recent_kl_entries['Items'][0]    # most recent entry with kl

        return int(most_recent_kl_entry['kl']['N'])


############################################################################
'''
    calculates the difference between new medals and old medals or new mpm and old mpm

    old = tuple(float, float)
    new = string of form ###.#S

    returns tuple (string of rep of increase, string rep of % change)
'''
def calc_progress(old, new):

    # unpack old data
    old_prefix, old_char_ascii = old
    old_char = chr(old_char_ascii)

    # unpack new data
    new_prefix = float(new[:-1])
    new_char_ascii = ord(new[-1:])
    new_char = new[-1:]

    # multiplier for use because the next letter represents a magnitude of 1000
    multiplier = (new_char_ascii  - old_char_ascii) * 1000

    # calculate the difference
    gain = None

    if multiplier == 0:
        gain = new_prefix - old_prefix
    else: 
        gain = (new_prefix * multiplier) - old_prefix

    # calculate the percent change
    gain_percent = (gain/old_prefix) * 100

    # building the string representations 
    gain_percent_str = f'{gain_percent:.2f}%'
    gain_str = ""

    if gain >= 1000:
        gain_str = f'{gain/1000:.1f}{new_char}'
    elif gain >= 0:
        gain_str = f'{gain:.1f}{old_char}'
    else:
        gain_str = None

    return (gain_str, gain_percent_str)
    


