import json, boto3
from botocore.exceptions import ClientError

rds = boto3.client('rds')

def lambda_handler(event, context):
    try: 
        print(event)
        resp = rds.describe_db_snapshots(DBSnapshotIdentifier=event['DBSnapshot']['DBSnapshotIdentifier'])
        rds_snapshot_status = resp['DBSnapshots'][0]['Status']
        
        return_data = {
            "DBSnapshot": {
                "DBSnapshotIdentifier": event['DBSnapshot']['DBSnapshotIdentifier'],
                "Status": rds_snapshot_status
            }
        }

        print(return_data)
        return return_data
    
    except ClientError as err:
        print(err)
        return err

    except Exception as err:
        print(err)
        return err