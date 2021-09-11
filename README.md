# copy-default-encrypted-rds-snapshot-to-other-aws-account

This serverless application is purposedly made for the scenario when you have many RDS Databases are already **encrypted with the default KMS key** (`aws/kms`) and want to share/copy the RDS Snapshots (which also encrypted with `aws/kms`) to another AWS account. Using the default KMS key, you can't share the snapshot with another account. So this simple app is aiming to solve that problem. 

### Limitations

- Only support EventBridge events from AWS Backup service (Not native RDS Automated or Manual Snapshot because they're out of scope)
- Only RDS MySQL and PostgreSQL are tested as of this writing

### Workflow

![Workflow](https://user-images.githubusercontent.com/49804935/117529577-77b97c80-b002-11eb-9bc9-b9b48a7de928.png)

1. In **Main RDS Account**, AWS Backup service successfully run the Backup Job for a RDS Database based on schedule
2. EventBridge will capture the snapshot success event emitted from AWS Backup then trigger the Step Functions - State Machine
3. The State Machine orchestrates the following Lambda functions:
   1. Manual Copy the AWS Backup Snapshot to Native RDS Snapshot (in Main RDS Account) using the KMS Key shared by **Backup Account**
   2. Wait and Check the status of the RDS Snapshot.
   3. Share the newly created RDS Snapshot to **Backup Account**
   4. Assume a Backup Account's Cross Account IAM Role that has RDS & KMS permissions, then perform Copy the Shared RDS Snapshot to Local Backup Account's RDS service
   5. Wait and Assume the Backup Account's Cross Account IAM Role to Check the status of the Snapshot
   6. Wait for the desired retention period (1 day as of this writing)
   7. Delete the same snapshot both in Backup Account and Main RDS Account
4. Send a Success State Machine Event to an SNS Topic and Slack Channel. If any of the step above is failed, a Failed Event is sent instead. 

**Note!**: If you want the State Machine to delete both snapshots in Main RDS Account and Backup Account. Check out to the branch name `release/delete-snapshot-in-both-account`. The last step should delete snapshots in both accounts. 

---
## Requirements

- Install SAM CLI tool [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) 
- Make sure that you have the required permissions to work with AWS SAM. [Required permissions is here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-permissions.html) in case you don't have privileged permissions. 

---
## Backup Account 

Make sure that you have the following resources before creating the app in Main RDS Snapshot
- Create a **KMS Customer Master Key (CMK)** then Share it to Main RDS Account
- Create a **Cross Account IAM Role** that allows Main RDS Account to assume and perform RDS copy/delete snapshots with the above KMS Key

You can use the sample template I provide here to create them. Please make sure to check the yaml file before creating the stack if your system is tight in security. 

```sh
$ cd ./other/backup-account-resources
$ aws cloudformation create-stack --stack-name devops-shared-kms-and-cross-acc-iam-role \
--capabilities CAPABILITY_NAMED_IAM \
--template-body file://required_aws_resources_kms_and_iam_role.yml \
--parameters ParameterKey=KeyAdministratorIamUserName,ParameterValue='quangluong' \
ParameterKey=MainRdsAccountId,ParameterValue='xxxxxxxxxxxx' \
--profile backup-account

# Please change the parameter values appropriately for your AWS environment
```

After the CFN creation is successful, copy the Output ARNs of the KMS CMK and IAM Role for the next configuration step in Main RDS Account. 

---
## Main RDS Account

Begin to create the serverless application with AWS SAM. Make sure you are at the root directory where the `template.yml` file lies. Run the following command.

```sh
$ sam deploy --guided
```

Note! If this is the first time you run `sam`. SAM CLI tool will create an additional cloudformation with some required resources for the SAM to function. Thus you will wait a little bit before going next step. 

When the output show `Configuring SAM deploy` as the below, step by step fill in the information. Be sure to provide the correct Backup Account KMS and IAM Role ARNs. 

```
Configuring SAM deploy
======================

	Setting default arguments for 'sam deploy'
	=========================================
	Stack Name []: devops-copy-default-encrypted-rds-snapshot-to-backup-account
	AWS Region []: ap-southeast-1
	Parameter ResourcePrefix []: devops  # This will be the prefix for most of the resources
	Parameter BackupAccountId []: 668813846055
	Parameter BackupAccountKmsArn []: arn:aws:kms:ap-southeast-1:668813846055:key/53d1f257-d5c9-4c93-b694-219f60eb35ec
	Parameter BackupAccountRoleArn []: arn:aws:iam::668813846055:role/main-rds-account-iam-role
	Parameter SlackWebhookUrl: ##Omitted##

	#Shows you resources changes to be deployed and require a 'Y' to initiate deploy
	Confirm changes before deploy [Y/n]: Y

	#SAM needs permission to be able to create roles to connect to the resources in your template
	Allow SAM CLI IAM role creation [Y/n]: n
	Capabilities [['CAPABILITY_IAM']]: CAPABILITY_NAMED_IAM

	Save arguments to configuration file [Y/n]: Y
	SAM configuration file [samconfig.toml]:
	SAM configuration environment [default]:
```

Then confirm the deployment when the ChangeSet is created. You're supposed to see this message if there's no problem encountered along the way. 

```
Successfully created/updated stack - devops-copy-default-encrypted-rds-snapshot-to-backup-account in ap-southeast-1
```

It's done. 

### Update Stack

Use the below command to update the current stack instead of going through all the options via `sam deploy --guided` unless you add new parameters. 

```sh
$ sam deploy
```

---
## Notes

### Adjust Shared RDS Snapshot Retention Day

Open `./state-machine/state_machine_def.json` file > States.WaitToDeleteSharedSnapshot.Seconds

At the moment, AWS SAM doesn't support definition substitution for variable with number type. So we must edit the number directly in the file. This can't be parameterized. 

Link: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-stepfunctions-statemachine.html#cfn-stepfunctions-statemachine-definitionsubstitutions

### Perform Copy for Specific Databases Only

Open `./template.yaml` file > Go to `Resources:SnapshotStateMachine:Events:AwsBackupSnapshot` > Uncomment the `resourceArn` section I made there and specify only the desired databases that EventBridge should capture. 

---
## Problems Encountered

Take note that all of the listed problems below can be solved with Step Functions - State Machine.

### Problem 1

**Complication**: There is no currently supported EventBridge event when copying Snapshot from AWS Backup to Native RDS Snapshot. So using standalone Lambda function in this case won't be sufficient with the full snapshot flow we require. 

**Solution**: Use Step Function to orchestrate all the function for each AWS Backup Snapshot created. 

### Problem 2

**Complication**: RDS Automated Backups are not configurable for InnoDB type like MySQL. So there must be a Lambda function to trigger the Backup automatically. 

**Solution**: Use Step Functions also solve this problem. Now we only care about AWS Backup. 

### Problem 3 

**Complication**: Manual Snapshot Has no Retention Option

> "Unlike automated backups, manual snapshots aren't subject to the backup retention period. Snapshots don't expire."

Link: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_CreateSnapshot.html

**Solution**: Create 1 more lambda function to delete the snapshot after the desired retention period in Step Functions.

