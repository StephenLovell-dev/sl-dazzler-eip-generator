import os
import json
from dazzler.api import handleApiCall

def lambda_handler(event, context):
    print(json.dumps(event))
    if 'DYNAMO_DB' not in os.environ:
        print('missing DYNAMO_DB in environment')
        return
    table_name = os.environ['DYNAMO_DB']
    if 'requestContext' in event:
        return handleApiCall(event, table_name)
