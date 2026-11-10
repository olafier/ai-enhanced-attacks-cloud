"""vm_live_read.py — run ON the EC2 instance (as the attached role).

Proves the instance role's credentials are live by making REAL read-only calls,
exactly the credentials an attacker would pull from Instance Metadata. It then does
ONE non-mutating EC2 DryRun check to test the write tier without creating anything.

It performs NO write, delete, or privilege-escalation action. Read-only + DryRun only.
boto3 reads the instance role automatically from IMDS (no keys on disk).
"""
import boto3
from botocore.exceptions import ClientError

# (label, client, method, kwargs) — every call here is List/Describe (non-mutating).
READ_CALLS = [
    ("sts:GetCallerIdentity",       "sts",            "get_caller_identity", {}),
    ("s3:ListAllMyBuckets",         "s3",             "list_buckets", {}),
    ("ec2:DescribeInstances",       "ec2",            "describe_instances", {"MaxResults": 5}),
    ("ec2:DescribeSecurityGroups",  "ec2",            "describe_security_groups", {"MaxResults": 5}),
    ("iam:ListUsers",               "iam",            "list_users", {"MaxItems": 1}),
    ("lambda:ListFunctions",        "lambda",         "list_functions", {"MaxItems": 1}),
    ("dynamodb:ListTables",         "dynamodb",       "list_tables", {"Limit": 1}),
    ("kms:ListKeys",                "kms",            "list_keys", {"Limit": 1}),
    ("cloudtrail:DescribeTrails",   "cloudtrail",     "describe_trails", {}),
    ("logs:DescribeLogGroups",      "logs",           "describe_log_groups", {"limit": 1}),
    ("secretsmanager:ListSecrets",  "secretsmanager", "list_secrets", {"MaxResults": 1}),
    ("ssm:DescribeParameters",      "ssm",            "describe_parameters", {"MaxResults": 1}),
    ("rds:DescribeDBInstances",     "rds",            "describe_db_instances", {"MaxRecords": 20}),
]


def classify(err):
    code = err.response["Error"]["Code"]
    if code in ("AccessDenied", "AccessDeniedException", "UnauthorizedOperation",
                "AuthorizationError", "NotAuthorized"):
        return "DENIED"
    return f"OTHER({code})"


def main():
    sess = boto3.session.Session()
    region = sess.region_name or "ap-southeast-1"
    print(f"region={region}")
    try:
        who = sess.client("sts").get_caller_identity()
        print(f"running as: {who['Arn']}\n")
    except ClientError as e:
        print(f"could not read identity: {e}\n")

    print(f"{'action':<30}{'live result':<12}")
    print("-" * 42)
    ok = 0
    for label, svc, method, kwargs in READ_CALLS:
        try:
            getattr(sess.client(svc, region_name=region), method)(**kwargs)
            print(f"{label:<30}{'ALLOWED':<12}")
            ok += 1
        except ClientError as e:
            print(f"{label:<30}{classify(e):<12}")
    print("-" * 42)
    print(f"READ tier: {ok}/{len(READ_CALLS)} live calls succeeded under this role\n")

    # write-tier probe, non-mutating: EC2 DryRun checks permission and creates nothing
    print("EC2 write-tier DryRun (creates nothing):")
    ec2 = sess.client("ec2", region_name=region)
    try:
        ec2.run_instances(ImageId="ami-00000000000000000", InstanceType="t3.micro",
                          MinCount=1, MaxCount=1, DryRun=True)
        verdict = "ALLOWED (would create)"
    except ClientError as e:
        code = e.response["Error"]["Code"]
        verdict = "ALLOWED (would create)" if code == "DryRunOperation" else classify(e)
    print(f"  ec2:RunInstances -> {verdict}")


if __name__ == "__main__":
    main()
