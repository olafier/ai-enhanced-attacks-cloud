#!/usr/bin/env bash
# teardown_lab.sh — remove everything setup_lab.sh created. Safe to re-run.
set -uo pipefail
REGION="${AWS_REGION:-$(aws configure get region || echo ap-southeast-1)}"
PREFIX="blast-lab"
echo "Region: $REGION — tearing down $PREFIX"

# terminate instance(s)
IIDS=$(aws ec2 describe-instances --region "$REGION" \
  --filters Name=tag:project,Values=$PREFIX Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [ -n "$IIDS" ]; then
  echo "terminating: $IIDS"
  aws ec2 terminate-instances --instance-ids $IIDS --region "$REGION" >/dev/null
  aws ec2 wait instance-terminated --instance-ids $IIDS --region "$REGION"
fi

# security group (retry — ENI detach can lag)
SG=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters Name=group-name,Values=${PREFIX}-sg \
  --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
if [ "$SG" != "None" ] && [ -n "$SG" ]; then
  for i in 1 2 3 4 5; do
    aws ec2 delete-security-group --group-id "$SG" --region "$REGION" 2>/dev/null && { echo "deleted SG $SG"; break; } || { echo "SG busy, retry $i"; sleep 15; }
  done
fi

# key pair + local pem
aws ec2 delete-key-pair --key-name "${PREFIX}-key" --region "$REGION" >/dev/null 2>&1 && echo "deleted key pair"
rm -f "$HOME/${PREFIX}-key.pem"

# roles + instance profiles
for L in A B C; do
  ROLE="${PREFIX}-role-${L}"
  aws iam remove-role-from-instance-profile --instance-profile-name "$ROLE" --role-name "$ROLE" >/dev/null 2>&1 || true
  aws iam delete-instance-profile --instance-profile-name "$ROLE" >/dev/null 2>&1 && echo "deleted instance profile $ROLE" || true
  aws iam delete-role-policy --role-name "$ROLE" --policy-name "${PREFIX}-inline-${L}" >/dev/null 2>&1 || true
  aws iam delete-role --role-name "$ROLE" >/dev/null 2>&1 && echo "deleted role $ROLE" || true
done
echo "teardown complete."
