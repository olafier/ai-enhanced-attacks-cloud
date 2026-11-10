#!/usr/bin/env bash
# setup_lab.sh — run in AWS CloudShell.
# Creates 3 IAM roles (policy A/B/C) + instance profiles, and ONE t3.micro EC2
# that carries role A to start. SSH is OS-level, independent of the role, so you
# can log in regardless of which experiment role is attached.
# This script creates NOTHING destructive. Teardown with teardown_lab.sh.
set -euo pipefail

REGION="${AWS_REGION:-$(aws configure get region || echo ap-southeast-1)}"
PREFIX="blast-lab"
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "Region: $REGION"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "Account: $ACCOUNT"

# --- EC2 trust policy (role can be assumed by an EC2 instance) ---
cat > /tmp/trust-ec2.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
EOF

for L in A B C; do
  case $L in
    A) POL="$HERE/policies/policy_A_broad.json";;    # over-permissive
    B) POL="$HERE/policies/policy_B_moderate.json";; # moderate
    C) POL="$HERE/policies/policy_C_narrow.json";;   # least privilege
  esac
  ROLE="${PREFIX}-role-${L}"
  echo "== role $ROLE =="
  aws iam create-role --role-name "$ROLE" \
    --assume-role-policy-document file:///tmp/trust-ec2.json \
    --tags Key=project,Value=$PREFIX >/dev/null 2>&1 || echo "  role exists, reusing"
  aws iam put-role-policy --role-name "$ROLE" \
    --policy-name "${PREFIX}-inline-${L}" \
    --policy-document "file://$POL"
  aws iam create-instance-profile --instance-profile-name "$ROLE" >/dev/null 2>&1 \
    || echo "  instance profile exists, reusing"
  aws iam add-role-to-instance-profile --instance-profile-name "$ROLE" \
    --role-name "$ROLE" >/dev/null 2>&1 || true
done

# --- networking: default VPC + SSH SG limited to this CloudShell's IP ---
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
      --query 'Vpcs[0].VpcId' --output text --region "$REGION")
SUBNET=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC \
      --query 'Subnets[0].SubnetId' --output text --region "$REGION")
MYIP=$(curl -s https://checkip.amazonaws.com || true)
[ -z "$MYIP" ] && { echo "Could not detect IP; set MYIP manually"; exit 1; }
echo "VPC=$VPC Subnet=$SUBNET YourIP=$MYIP"

SG=$(aws ec2 create-security-group --group-name "${PREFIX}-sg" \
     --description "blast lab ssh" --vpc-id "$VPC" --region "$REGION" \
     --query GroupId --output text 2>/dev/null \
   || aws ec2 describe-security-groups --filters Name=group-name,Values=${PREFIX}-sg \
        --query 'SecurityGroups[0].GroupId' --output text --region "$REGION")
aws ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp \
  --port 22 --cidr "${MYIP}/32" --region "$REGION" >/dev/null 2>&1 || echo "  SSH rule exists"

# --- key pair ---
KEY="${PREFIX}-key"
if [ ! -f "$HOME/${KEY}.pem" ]; then
  aws ec2 create-key-pair --key-name "$KEY" --region "$REGION" \
    --query KeyMaterial --output text > "$HOME/${KEY}.pem"
  chmod 400 "$HOME/${KEY}.pem"
  echo "wrote $HOME/${KEY}.pem"
fi

# --- latest Amazon Linux 2023 AMI ---
AMI=$(aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameters[0].Value' --output text --region "$REGION")
echo "AMI=$AMI"

# user-data: install boto3 so the box is ready to run the measurement script
cat > /tmp/userdata.sh <<'EOF'
#!/bin/bash
dnf install -y python3-pip >/dev/null 2>&1 || yum install -y python3-pip >/dev/null 2>&1
python3 -m pip install --quiet boto3
EOF

echo "launching t3.micro (role A attached to start)..."
sleep 10  # let instance profile propagate
IID=$(aws ec2 run-instances --image-id "$AMI" --instance-type t3.micro \
  --key-name "$KEY" --security-group-ids "$SG" --subnet-id "$SUBNET" \
  --associate-public-ip-address \
  --iam-instance-profile Name=${PREFIX}-role-A \
  --user-data file:///tmp/userdata.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PREFIX}-ec2},{Key=project,Value=${PREFIX}}]" \
  --region "$REGION" --query 'Instances[0].InstanceId' --output text)
echo "instance: $IID"
aws ec2 wait instance-running --instance-ids "$IID" --region "$REGION"
PUBIP=$(aws ec2 describe-instances --instance-ids "$IID" --region "$REGION" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

cat <<EOF

================ lab ready ================
instance id : $IID
public ip   : $PUBIP
ssh         : ssh -i ~/${KEY}.pem ec2-user@$PUBIP
(wait ~60s for boto3 to finish installing via user-data)

Copy the VM script up and run it:
  scp -i ~/${KEY}.pem $HERE/vm_live_read.py ec2-user@$PUBIP:~
  ssh -i ~/${KEY}.pem ec2-user@$PUBIP 'python3 vm_live_read.py'

Measure effective permissions of each role from CloudShell:
  python3 $HERE/measure_principal.py

Switch the role attached to the instance (then re-run vm_live_read on the box):
  ASSOC=\$(aws ec2 describe-iam-instance-profile-associations \\
    --filters Name=instance-id,Values=$IID --query 'IamInstanceProfileAssociations[0].AssociationId' --output text --region $REGION)
  aws ec2 replace-iam-instance-profile-association --association-id \$ASSOC \\
    --iam-instance-profile Name=${PREFIX}-role-B --region $REGION

Tear everything down when done:
  bash $HERE/teardown_lab.sh
===========================================
EOF
