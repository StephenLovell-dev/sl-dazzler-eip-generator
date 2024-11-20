import os
from dazzler.main import main

def lambda_handler(event, context):
    if 'DYNAMO_DB' not in os.environ:
        print('missing DYNAMO_DB in environment')
        return
    table_name = os.environ['DYNAMO_DB']
    return main(event, table_name)


