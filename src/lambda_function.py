from src.dazzler_interstitials.main import main

def lambda_handler(event, context):
    region = 'eu-west-1'
    account = context.invoked_function_arn.split(':')[4]
    main(event, account)