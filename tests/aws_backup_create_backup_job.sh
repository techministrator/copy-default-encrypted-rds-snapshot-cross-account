#!/bin/bash -x

while true; do
  aws backup start-backup-job --backup-vault-name Default \
  --resource-arn arn:aws:rds:ap-southeast-1:xxxxxxxxxxxx:db:test-postgres \
  --iam-role-arn arn:aws:iam::xxxxxxxxxxxx:role/service-role/AWSBackupDefaultServiceRole \
  --start-window-minutes 60 --complete-window-minutes 10080 --lifecycle DeleteAfterDays=30

  aws backup start-backup-job --backup-vault-name Default \
  --resource-arn arn:aws:rds:ap-southeast-1:xxxxxxxxxxxx:db:test-mysql-db \
  --iam-role-arn arn:aws:iam::xxxxxxxxxxxx:role/service-role/AWSBackupDefaultServiceRole \
  --start-window-minutes 60 --complete-window-minutes 10080 --lifecycle DeleteAfterDays=30

  sleep 360
done
