import json, boto3, os
from botocore.exceptions import ClientError

rds = boto3.client('rds')

BACKUP_ACCOUNT_ID = os.environ['BACKUP_ACCOUNT_ID']

def lambda_handler(event, context):
    try: 
        print("Sharing Snapshot to Account B")
        rds_snapshot_identifier = event['DBSnapshot']['DBSnapshotIdentifier']
        
        # Share the snapshot to Backup Account
        resp = rds.modify_db_snapshot_attribute(
            DBSnapshotIdentifier=rds_snapshot_identifier,
            AttributeName='restore',
            ValuesToAdd=[
                BACKUP_ACCOUNT_ID,
            ]
        )
        
        event['Share Status'] = 'Done'
        print(event)
        return event
    
    except ClientError as err:
        print(err)
        return err

    except Exception as err:
        print(err)
        return err
