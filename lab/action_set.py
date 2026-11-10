"""Fixed Action Set: 100 actions across 12 AWS services.

Each entry: (action, category, resource_kind)
  category: READ | WRITE | DESTROY | ESCALATE
  resource_kind: key into RESOURCE_TEMPLATES (see resource_arn()).
Weights are fixed BEFORE the experiment: READ=1, WRITE=2, DESTROY=3, ESCALATE=4.
"""

WEIGHTS = {"READ": 1, "WRITE": 2, "DESTROY": 3, "ESCALATE": 4}

LAB_BUCKET = "blast-lab-bucket"
LAB_LOG_GROUP = "/blast-lab/app"

R, W, D, E = "READ", "WRITE", "DESTROY", "ESCALATE"

ACTIONS = [
    # ---- S3 (10) ----
    ("s3:ListAllMyBuckets", R, "any"),
    ("s3:ListBucket", R, "bucket"),
    ("s3:GetObject", R, "object"),
    ("s3:GetBucketPolicy", R, "bucket"),
    ("s3:GetBucketLocation", R, "bucket"),
    ("s3:PutObject", W, "object"),
    ("s3:PutBucketTagging", W, "bucket"),
    ("s3:DeleteObject", D, "object"),
    ("s3:DeleteBucket", D, "bucket"),
    ("s3:PutBucketPolicy", E, "bucket"),
    # ---- EC2 (10) ----
    ("ec2:DescribeInstances", R, "any"),
    ("ec2:DescribeSecurityGroups", R, "any"),
    ("ec2:DescribeVpcs", R, "any"),
    ("ec2:DescribeSnapshots", R, "any"),
    ("ec2:RunInstances", W, "any"),
    ("ec2:CreateSecurityGroup", W, "any"),
    ("ec2:AuthorizeSecurityGroupIngress", W, "any"),
    ("ec2:TerminateInstances", D, "any"),
    ("ec2:DeleteSecurityGroup", D, "any"),
    ("ec2:AssociateIamInstanceProfile", E, "any"),
    # ---- IAM (14) ----
    ("iam:ListUsers", R, "any"),
    ("iam:ListRoles", R, "any"),
    ("iam:GetUser", R, "any"),
    ("iam:ListAttachedUserPolicies", R, "any"),
    ("iam:GetAccountAuthorizationDetails", R, "any"),
    ("iam:CreateUser", W, "any"),
    ("iam:DeleteUser", D, "any"),
    ("iam:CreateAccessKey", E, "any"),
    ("iam:AttachUserPolicy", E, "any"),
    ("iam:PutUserPolicy", E, "any"),
    ("iam:CreatePolicyVersion", E, "any"),
    ("iam:UpdateAssumeRolePolicy", E, "any"),
    ("iam:PassRole", E, "any"),
    ("iam:CreateLoginProfile", E, "any"),
    # ---- STS (4) ----
    ("sts:GetCallerIdentity", R, "any"),
    ("sts:GetAccessKeyInfo", R, "any"),
    ("sts:TagSession", W, "any"),
    ("sts:AssumeRole", E, "any"),
    # ---- Lambda (9) ----
    ("lambda:ListFunctions", R, "any"),
    ("lambda:GetFunction", R, "any"),
    ("lambda:GetFunctionConfiguration", R, "any"),
    ("lambda:CreateFunction", W, "any"),
    ("lambda:UpdateFunctionCode", W, "any"),
    ("lambda:InvokeFunction", W, "any"),
    ("lambda:AddPermission", W, "any"),
    ("lambda:DeleteFunction", D, "any"),
    ("lambda:DeleteAlias", D, "any"),
    # ---- DynamoDB (8) ----
    ("dynamodb:ListTables", R, "any"),
    ("dynamodb:DescribeTable", R, "any"),
    ("dynamodb:Scan", R, "any"),
    ("dynamodb:PutItem", W, "any"),
    ("dynamodb:UpdateItem", W, "any"),
    ("dynamodb:DeleteItem", D, "any"),
    ("dynamodb:DeleteTable", D, "any"),
    ("dynamodb:DeleteBackup", D, "any"),
    # ---- KMS (8) ----
    ("kms:ListKeys", R, "any"),
    ("kms:DescribeKey", R, "any"),
    ("kms:Decrypt", R, "any"),
    ("kms:Encrypt", W, "any"),
    ("kms:CreateAlias", W, "any"),
    ("kms:ScheduleKeyDeletion", D, "any"),
    ("kms:DisableKey", D, "any"),
    ("kms:PutKeyPolicy", E, "any"),
    # ---- CloudTrail (6) ----
    ("cloudtrail:DescribeTrails", R, "any"),
    ("cloudtrail:GetTrailStatus", R, "any"),
    ("cloudtrail:LookupEvents", R, "any"),
    ("cloudtrail:PutEventSelectors", W, "any"),
    ("cloudtrail:StopLogging", D, "any"),
    ("cloudtrail:DeleteTrail", D, "any"),
    # ---- CloudWatch Logs (7) ----
    ("logs:DescribeLogGroups", R, "any"),
    ("logs:DescribeLogStreams", R, "loggroup"),
    ("logs:GetLogEvents", R, "logstream"),
    ("logs:CreateLogStream", W, "logstream"),
    ("logs:PutLogEvents", W, "logstream"),
    ("logs:DeleteLogGroup", D, "loggroup"),
    ("logs:DeleteLogStream", D, "logstream"),
    # ---- Secrets Manager (7) ----
    ("secretsmanager:ListSecrets", R, "any"),
    ("secretsmanager:DescribeSecret", R, "any"),
    ("secretsmanager:GetSecretValue", R, "any"),
    ("secretsmanager:CreateSecret", W, "any"),
    ("secretsmanager:PutSecretValue", W, "any"),
    ("secretsmanager:DeleteSecret", D, "any"),
    ("secretsmanager:PutResourcePolicy", E, "any"),
    # ---- SSM (9) ----
    ("ssm:DescribeInstanceInformation", R, "any"),
    ("ssm:GetParameter", R, "any"),
    ("ssm:GetParameters", R, "any"),
    ("ssm:DescribeParameters", R, "any"),
    ("ssm:PutParameter", W, "any"),
    ("ssm:AddTagsToResource", W, "any"),
    ("ssm:StartSession", W, "any"),
    ("ssm:DeleteParameter", D, "any"),
    ("ssm:SendCommand", E, "any"),
    # ---- RDS (8) ----
    ("rds:DescribeDBInstances", R, "any"),
    ("rds:DescribeDBSnapshots", R, "any"),
    ("rds:DescribeDBClusters", R, "any"),
    ("rds:CreateDBSnapshot", W, "any"),
    ("rds:ModifyDBInstance", W, "any"),
    ("rds:CreateDBInstance", W, "any"),
    ("rds:DeleteDBInstance", D, "any"),
    ("rds:DeleteDBSnapshot", D, "any"),
]


def resource_arn(kind, account="123456789012", region="us-east-1"):
    """Concrete target resource for each action, so scoped policies (Policy A) are evaluated fairly."""
    return {
        "any": "*",
        "bucket": f"arn:aws:s3:::{LAB_BUCKET}",
        "object": f"arn:aws:s3:::{LAB_BUCKET}/data.txt",
        "loggroup": f"arn:aws:logs:{region}:{account}:log-group:{LAB_LOG_GROUP}",
        "logstream": f"arn:aws:logs:{region}:{account}:log-group:{LAB_LOG_GROUP}:log-stream:s1",
    }[kind]


def service_of(action):
    return action.split(":")[0]


def _self_check():
    from collections import Counter
    assert len(ACTIONS) == 100, len(ACTIONS)
    assert len({a for a, _, _ in ACTIONS}) == 100, "duplicate action"
    cats = Counter(c for _, c, _ in ACTIONS)
    assert cats == {"READ": 41, "WRITE": 26, "DESTROY": 20, "ESCALATE": 13}, cats
    assert sum(WEIGHTS[c] for _, c, _ in ACTIONS) == 205
    assert len({service_of(a) for a, _, _ in ACTIONS}) == 12


_self_check()

if __name__ == "__main__":
    from collections import Counter
    print("services:", dict(Counter(service_of(a) for a, _, _ in ACTIONS)))
    print("categories:", dict(Counter(c for _, c, _ in ACTIONS)))
    print("total weight:", sum(WEIGHTS[c] for _, c, _ in ACTIONS))
