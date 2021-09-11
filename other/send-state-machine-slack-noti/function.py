import urllib3
import json
import os
import boto3
from botocore.exceptions import ClientError

SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']

http = urllib3.PoolManager()

def send_slack_message(icon, message):
  slack_message = {'text': f'{icon} {message}'}
  encoded_slack_message = json.dumps(slack_message).encode('utf-8')
  resp = http.request('POST', SLACK_WEBHOOK_URL, body=encoded_slack_message, headers={'Content-Type': 'application/json'})
  print(str(resp.status) + " " + str(resp.data))

# Check newest receiving transactions
def lambda_handler(event, context):
  try:
    print(event)
    state_machine_uri = f"https://{event['region']}.console.aws.amazon.com/states/home?region={event['region']}#/executions/details/{event['detail']['executionArn']}"
    
    # SUCCEEDED
    if event['detail']['status'] == 'SUCCEEDED': 
      state_machine_last_step_output = json.loads(event['detail']['output'])
      if isinstance(state_machine_last_step_output, list): 
        state_machine_last_step_output = state_machine_last_step_output[0]
      state_machine_last_step_input = json.loads(event['detail']['input'])
      
      slack_icon = ':white_check_mark:'
      message = f"""{event['detail']['status']}
*Service*: Step Functions - State Machine
*Detail Type*: {event['detail-type']}
*Account ID*: {event['account']}
*Region*: {event['region']} 
*State Machine Name*: `{event['detail']['stateMachineArn'].split(':')[6]}`
*Execution Name*: `{event['detail']['name']}`
*RDS Snapshot Name* (both Accounts): `{state_machine_last_step_output['DBSnapshot']['DBSnapshotIdentifier']}`
*RDS Database ARN*: `{state_machine_last_step_input['detail']['resourceArn']}`
*AWS Backup Name*: `{state_machine_last_step_input['resources'][0]}` 
*Description*: The snapshot state machine has successfully shared, copied and deleted the snapshot after the desired retention period
*Detail Link*: <{state_machine_uri}|AWS Console - Step Functions - This Execution Link>"""

      send_slack_message(slack_icon, message)
    
    # FAILED 
    elif event['detail']['status'] == 'FAILED':
      slack_icon = ':x:'
      message = f"""{event['detail']['status']}
*Service*: Step Functions - State Machine
*Detail Type*: {event['detail-type']}
*Account ID*: {event['account']}
*Region*: {event['region']} 
*State Machine Name*: `{event['detail']['stateMachineArn'].split(':')[6]}`
*Execution Name*: `{event['detail']['name']}`
*Description*: The snapshot state machine has failed to perform full flow of sharing, copying or deleting the snapshot
*Detail Link*: <{state_machine_uri}|AWS Console - Step Functions - This Execution Link>"""

      send_slack_message(slack_icon, message)
    
    # OTHER
    else:
      slack_icon = ':warning:'
      message = f"""{event['detail']['status']}
*Service*: Step Functions - State Machine
*Detail Type*: {event['detail-type']}
*Account ID*: {event['account']}
*Region*: {event['region']} 
*State Machine Name*: `{event['detail']['stateMachineArn'].split(':')[6]}`
*Execution Name*: `{event['detail']['name']}`
*Description*: The snapshot state machine has been aborted or stopped by user or system
*Detail Link*: <{state_machine_uri}|AWS Console - Step Functions - This Execution Link>"""

      send_slack_message(slack_icon, message)

    return event

  except ClientError as err:
    print(err)
    return err

  except urllib3.exceptions.HTTPError as http_err:
    print("HTTP Error: " + http_err)
    return http_err
  
  except urllib3.exceptions.RequestError as req_err:
    print("Request Error: " + req_err)
    return req_err
