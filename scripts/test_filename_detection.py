import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.service_detection import get_service_from_filename

test_files = [
    "lambda-dg.pdf",
    "s3-userguide.pdf",
    "ec2-ug.pdf",
    "iam-ug.pdf",
    "AmazonVPC_UserGuide.pdf",
    "cloudformation-userguide.pdf",
    "sagemaker-dg.pdf",
    "amazon-bedrock-ug.pdf",
    "codepipeline-user.pdf",
    "secretsmanager-userguide.pdf",
    "cloudwatch-ug.pdf",
    "dynamodb-developer-guide.pdf",
    "redshift-mgmt.pdf",
    "eks-userguide.pdf",
    "route53-developer-guide.pdf"
]

print(f"{'FILENAME':45} | {'DETECTED SERVICE'}")
print("-" * 65)
for f in test_files:
    service = get_service_from_filename(f)
    print(f"{f:45} | {service}")
