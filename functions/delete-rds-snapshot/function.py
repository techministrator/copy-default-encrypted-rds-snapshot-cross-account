import json, boto3, os
from botocore.exceptions import ClientError

rds = boto3.client('rds')

def lambda_handler(event, context):
    try: 
        print(event)
        rds_snapshot_name = event['DBSnapshot']['DBSnapshotIdentifier']
        
        resp = rds.delete_db_snapshot(DBSnapshotIdentifier=rds_snapshot_name)

        print(event)
        return event
    
    except ClientError as err:
        print(err)
        return err

    except Exception as err:
        print(err)
        return err