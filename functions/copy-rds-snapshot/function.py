import json, boto3, datetime, os
from botocore.exceptions import ClientError

rds = boto3.client('rds')

BACKUP_ACCOUNT_KMS_ARN = os.environ['BACKUP_ACCOUNT_KMS_ARN']

def lambda_handler(event, context):
    try:
        awsbackup_snapshot_arn = event['resources'][0]
        awsbackup_snapshot_db_name = event['detail']['resourceArn'].split(':')[6]

        # Because RDS CopyDBSnapshot method only allows hyphen (-), so the time format 
        # should be changed from %H:%M:%S to %Y-%M-%S. E.g. from 06:35:25 to 06-35-25
        awsbackup_snapshot_creation_date = datetime.datetime.strptime(event['detail']['creationDate'][0:19].strip(), "%Y-%m-%dT%H:%M:%S%f").strftime("%Y-%m-%dT%H-%M-%S")
        
        print("Perform copying snapshot " + awsbackup_snapshot_arn + " from " + awsbackup_snapshot_db_name + "created at " + awsbackup_snapshot_creation_date)
        resp = rds.copy_db_snapshot(
            SourceDBSnapshotIdentifier=awsbackup_snapshot_arn,
            TargetDBSnapshotIdentifier=awsbackup_snapshot_db_name + '-' + awsbackup_snapshot_creation_date ,
            KmsKeyId=BACKUP_ACCOUNT_KMS_ARN,
            CopyTags=True
        )
        
        print(resp)
        jsonified_resp = json.loads(json.dumps(resp, indent=4, default=str))
        return jsonified_resp

    except ClientError as err:
        print(err)
        return err

    except Exception as err:
        print(err)
        return err