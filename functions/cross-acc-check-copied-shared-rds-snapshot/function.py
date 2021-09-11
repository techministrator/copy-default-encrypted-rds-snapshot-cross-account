import json, boto3, os
from botocore.exceptions import ClientError

BACKUP_ACCOUNT_ROLE_ARN = os.environ['BACKUP_ACCOUNT_ROLE_ARN']

sts = boto3.client('sts')

def lambda_handler(event, context):
    try:
        backup_acc_credential = sts.assume_role(RoleArn=BACKUP_ACCOUNT_ROLE_ARN, RoleSessionName='backup_acc_rds')

        backup_acc_access_key = backup_acc_credential['Credentials']['AccessKeyId']
        backup_acc_secret_key = backup_acc_credential['Credentials']['SecretAccessKey']
        backup_acc_session_token = backup_acc_credential['Credentials']['SessionToken']

        backup_acc_rds = boto3.client(
            'rds',
            aws_access_key_id=backup_acc_access_key,
            aws_secret_access_key=backup_acc_secret_key,
            aws_session_token=backup_acc_session_token,
        )

        shared_rds_snapshot_identifier = event['DBSnapshot']['DBSnapshotIdentifier']
        
        resp = backup_acc_rds.describe_db_snapshots(DBSnapshotIdentifier=shared_rds_snapshot_identifier)
        backup_acc_rds_snapshot_status = resp['DBSnapshots'][0]['Status']

        return_data = {
            "DBSnapshot": {
                "DBSnapshotIdentifier": event['DBSnapshot']['DBSnapshotIdentifier'],
                "Status": backup_acc_rds_snapshot_status
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