import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

REGISTRY_FILE = "data/uploaded_docs_registry.json"

HARDCODED_FALLBACKS = {
    "lambda": "lambda-dg.pdf",
    "s3": "s3-userguide.pdf",
    "ec2": "ec2-ug.pdf",
    "iam": "iam-ug.pdf",
    "vpc": "vpc-ug.pdf",
    "rds": "rds-ug.pdf",
    "dynamodb": "dynamodb-dg.pdf",
    "cloudformation": "cloudformation-ug.pdf",
    "cloudwatch": "cloudwatch-ug.pdf",
    "ecs": "ecs-dg.pdf",
    "eks": "eks-ug.pdf",
    "sagemaker": "sagemaker-dg.pdf",
    "bedrock": "bedrock-ug.pdf",
}

FAKE_SOURCE_PATTERNS = [
    "aws_lambda.md", "lambda-limits.md",
    "aws_s3.md", "aws_ec2.md", "aws_iam.md",
    "aws-docs.pdf", "documentation.pdf",
    "aws_documentation.md", "unknown",
    "source unknown", "not available"
]

PERMANENTLY_BLOCKED = [
    "aws_lambda.md",
    "aws_s3.md",
    "aws_ec2.md", 
    "aws_iam.md",
    "aws_vpc.md",
    "aws_rds.md",
    "aws_dynamodb.md",
    "aws_cloudwatch.md",
    "aws_cloudformation.md",
    "aws_ecs.md",
    "aws_eks.md",
    "aws_sagemaker.md",
    "aws_bedrock.md",
    "aws_glue.md",
    "aws_athena.md",
    "aws_redshift.md",
    "aws_kinesis.md",
    "aws_sns.md",
    "aws_sqs.md",
    "aws_cloudfront.md",
    "aws_route53.md",
    "aws_waf.md",
    "aws_kms.md",
    "aws_cloudtrail.md",
    "aws_codepipeline.md",
    "aws_codebuild.md",
    "aws_codecommit.md",
    "aws_codedeploy.md",
    "aws_stepfunctions.md",
    "aws_apigateway.md",
    "aws_elasticache.md",
    "aws_ssm.md",
    "aws_secretsmanager.md",
    "lambda-limits.md",
    "aws-docs.pdf",
    "documentation.pdf",
    "unknown",
]

def load_registry() -> dict:
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            try:
                data = json.load(f)
                return data
            except:
                return {"documents": []}
    return {"documents": []}

def save_registry(registry: dict):
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)

def register_document(filename: str, service: str):
    # Block permanently — no exceptions
    if filename in PERMANENTLY_BLOCKED or any(fake in filename.lower() for fake in FAKE_SOURCE_PATTERNS):
        logger.warning(f"BLOCKED fake source: {filename}")
        return None

    # Block any .md file that was not explicitly 
    # uploaded by the user
    if filename.endswith(".md"):
        logger.warning(f"BLOCKED .md file: {filename}")
        return None

    registry = load_registry()
    existing = [d["filename"] for d in registry["documents"]]
    if filename not in existing:
        registry["documents"].append({
            "filename": filename,
            "service": service,
            "uploaded": datetime.now().strftime("%Y-%m-%d"),
            "active": True
        })
        save_registry(registry)
        logger.info(f"[REGISTRY] Registered: {filename} → {service}")

def get_valid_sources() -> list:
    registry = load_registry()
    registered = [
        d["filename"] for d in registry["documents"]
        if d.get("active", True)
    ]
    # Always include hardcoded fallbacks
    hardcoded = list(HARDCODED_FALLBACKS.values())
    all_valid = list(set(registered + hardcoded))
    
    # FILTER: Remove any fake patterns even if they somehow got in
    clean_valid = [s for s in all_valid if s not in PERMANENTLY_BLOCKED and not any(fake in s.lower() for fake in FAKE_SOURCE_PATTERNS)]
    return clean_valid

def get_correct_source_for_service(service: str) -> str:
    # First check hardcoded mapping
    if service in HARDCODED_FALLBACKS:
        return HARDCODED_FALLBACKS[service]
    
    # Fallback to registry (filtering fakes)
    registry = load_registry()
    for doc in registry["documents"]:
        fname = doc.get("filename", "")
        if doc.get("service") == service and doc.get("active", True):
            if fname not in PERMANENTLY_BLOCKED and not any(fake in fname.lower() for fake in FAKE_SOURCE_PATTERNS):
                return fname
                
    return HARDCODED_FALLBACKS.get(service, f"{service}-dg.pdf")

def is_fake_source(source: str) -> bool:
    source_lower = source.lower()
    if source in PERMANENTLY_BLOCKED:
        return True
    for fake in FAKE_SOURCE_PATTERNS:
        if fake.lower() in source_lower:
            return True
    return False

def validate_source(
    cited_source: str,
    valid_sources: list = None,
    service: str = None,
    chunks: list = None
) -> str:
    if valid_sources is None:
        valid_sources = get_valid_sources()

    # Check if cited source is already valid
    for valid in valid_sources:
        if valid.lower() in cited_source.lower():
            if valid not in PERMANENTLY_BLOCKED:
                return valid

    # Use service-based lookup as priority fallback
    if service:
        return get_correct_source_for_service(service)

    # Last resort
    return "lambda-dg.pdf"
