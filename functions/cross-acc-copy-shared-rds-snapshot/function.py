import json, boto3, os
from botocore.exceptions import ClientError

BACKUP_ACCOUNT_ID = os.environ['BACKUP_ACCOUNT_ID']
BACKUP_ACCOUNT_KMS_ARN = os.environ['BACKUP_ACCOUNT_KMS_ARN']
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

        aws_region = os.environ['AWS_REGION']
        aws_main_rds_account_id = context.invoked_function_arn.split(":")[4]
        shared_rds_snapshot_identifier = event['DBSnapshot']['DBSnapshotIdentifier']
        
        shared_rds_snapshot_identifier_arn = f'arn:aws:rds:{aws_region}:{aws_main_rds_account_id}:snapshot:{shared_rds_snapshot_identifier}'
        
        print(f"Perform copying shared rds snapshot {shared_rds_snapshot_identifier_arn} to local")
        resp = backup_acc_rds.copy_db_snapshot(
            SourceDBSnapshotIdentifier=shared_rds_snapshot_identifier_arn,
            TargetDBSnapshotIdentifier=shared_rds_snapshot_identifier,
            KmsKeyId=BACKUP_ACCOUNT_KMS_ARN
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