from rapidfuzz import process, fuzz
import logging

logger = logging.getLogger(__name__)

AWS_SERVICES = [
    "lambda", "s3", "ec2", "iam", "vpc",
    "rds", "dynamodb", "sagemaker", "bedrock",
    "cloudformation", "cloudwatch", "ecs", "eks",
    "sns", "sqs", "api gateway", "cognito",
    "route53", "cloudfront", "elasticache",
    "redshift", "glue", "athena", "kinesis",
    "step functions", "eventbridge", "secrets manager"
]

def fuzzy_match_service(query: str) -> str:
    """
    Match typos to correct AWS service names.
    Examples:
      slmabda -> lambda
      dynmodb -> dynamodb  
      clodwatch -> cloudwatch
    """
    query_lower = query.lower()
    words = query_lower.split()
    
    best_service = None
    best_score = 0
    
    for word in words:
        # Skip short words to avoid false matches
        if len(word) < 3:
            continue
            
        match = process.extractOne(
            word,
            AWS_SERVICES,
            scorer=fuzz.ratio,
            score_cutoff=65  # 65% similarity threshold
        )
        
        if match and match[1] > best_score:
            best_score = match[1]
            best_service = match[0]
    
    return best_service  # Returns None if no match found

FILENAME_TO_SERVICE = {
    # Compute
    "lambda":           "lambda",
    "ec2":              "ec2",
    "ecs":              "ecs",
    "eks":              "eks",
    "fargate":          "ecs",
    "batch":            "batch",
    "lightsail":        "lightsail",
    
    # Storage
    "s3":               "s3",
    "ebs":              "ec2",
    "efs":              "efs",
    "fsx":              "fsx",
    "glacier":          "s3",
    "backup":           "backup",
    "storagegateway":   "storagegateway",
    
    # Database
    "rds":              "rds",
    "aurora":           "rds",
    "dynamodb":         "dynamodb",
    "elasticache":      "elasticache",
    "redshift":         "redshift",
    "neptune":          "neptune",
    "documentdb":       "documentdb",
    "keyspaces":        "keyspaces",
    "timestream":       "timestream",
    "memorydb":         "memorydb",
    
    # Networking
    "vpc":              "vpc",
    "route53":          "route53",
    "cloudfront":       "cloudfront",
    "apigateway":       "apigateway",
    "api-gateway":      "apigateway",
    "elb":              "elb",
    "alb":              "elb",
    "nlb":              "elb",
    "directconnect":    "directconnect",
    "globalaccelerator":"globalaccelerator",
    "transitgateway":   "vpc",
    
    # Security & Identity
    "iam":              "iam",
    "kms":              "kms",
    "secretsmanager":   "secretsmanager",
    "secrets-manager":  "secretsmanager",
    "waf":              "waf",
    "shield":           "shield",
    "guardduty":        "guardduty",
    "inspector":        "inspector",
    "macie":            "macie",
    "securityhub":      "securityhub",
    "cognito":          "cognito",
    "sso":              "sso",
    "acm":              "acm",
    "artifact":         "artifact",
    "detective":        "detective",
    
    # Developer Tools
    "codepipeline":     "codepipeline",
    "codebuild":        "codebuild",
    "codecommit":       "codecommit",
    "codedeploy":       "codedeploy",
    "codeartifact":     "codeartifact",
    "codestar":         "codestar",
    "cloud9":           "cloud9",
    "xray":             "xray",
    
    # Management & Monitoring  
    "cloudwatch":       "cloudwatch",
    "cloudtrail":       "cloudtrail",
    "cloudformation":   "cloudformation",
    "cfn":              "cloudformation",
    "config":           "config",
    "systemsmanager":   "systemsmanager",
    "systems-manager":  "systemsmanager",
    "ssm":              "systemsmanager",
    "trustedadvisor":   "trustedadvisor",
    "controlplane":     "controltower",
    "controltower":     "controltower",
    "organizations":    "organizations",
    "servicecatalog":   "servicecatalog",
    "opsworks":         "opsworks",
    "proton":           "proton",
    
    # Messaging & Integration
    "sns":              "sns",
    "sqs":              "sqs",
    "eventbridge":      "eventbridge",
    "mq":               "mq",
    "stepfunctions":    "stepfunctions",
    "step-functions":   "stepfunctions",
    "appflow":          "appflow",
    "b2bi":             "b2bi",
    
    # Analytics & Big Data
    "athena":           "athena",
    "glue":             "glue",
    "emr":              "emr",
    "kinesis":          "kinesis",
    "opensearch":       "opensearch",
    "elasticsearch":    "opensearch",
    "quicksight":       "quicksight",
    "lakeformation":    "lakeformation",
    "lake-formation":   "lakeformation",
    "dataexchange":     "dataexchange",
    "datapipeline":     "datapipeline",
    "msk":              "msk",
    "kafka":            "msk",
    
    # ML & AI
    "sagemaker":        "sagemaker",
    "bedrock":          "bedrock",
    "rekognition":      "rekognition",
    "textract":         "textract",
    "comprehend":       "comprehend",
    "translate":        "translate",
    "polly":            "polly",
    "transcribe":       "transcribe",
    "lex":              "lex",
    "forecast":         "forecast",
    "personalize":      "personalize",
    "lookout":          "lookout",
    "panorama":         "panorama",
    "deeplens":         "deeplens",
    
    # Migration & Transfer
    "dms":              "dms",
    "datasync":         "datasync",
    "transferfamily":   "transferfamily",
    "transfer-family":  "transferfamily",
    "migrationhub":     "migrationhub",
    "snowball":         "snowball",
    "snowcone":         "snowball",
    "snowmobile":       "snowball",
    "applicationmigration": "mgn",
    
    # IoT
    "iot":              "iot",
    "iotcore":          "iot",
    "greengrass":       "greengrass",
    "iotanalytics":     "iotanalytics",
    "iotsitewise":      "iotsitewise",
    
    # Cost Management
    "costexplorer":     "costmanagement",
    "budgets":          "costmanagement",
    "billing":          "costmanagement",
    "savingsplans":     "costmanagement",
    
    # Media Services
    "mediaconvert":     "mediaservices",
    "medialive":        "mediaservices",
    "mediapackage":     "mediaservices",
    "ivs":              "mediaservices",
    "chime":            "chime",
    "connect":          "connect",
    
    # General fallback
    "well-architected": "wellarchitected",
    "wellarchitected":  "wellarchitected",
    "general":          "general",
    "overview":         "general",
    "whitepaper":       "general",
    "faq":              "general",
}

def get_service_from_filename(filename: str) -> str:
    """
    Automatically detects AWS service from filename.
    Works for any filename format:
    - lambda-dg.pdf → lambda
    - s3-userguide.pdf → s3
    - AmazonEC2UserGuide.pdf → ec2
    - iam_user_guide.pdf → iam
    - NEW-service-docs.pdf → auto detected
    """
    import re
    
    # Clean filename: remove extension, 
    # lowercase, replace separators with spaces
    name = filename.lower()
    name = re.sub(r'\.(pdf|docx|txt|html|md|csv|pptx|xlsx)$', '', name)
    name = re.sub(r'[-_\.]', ' ', name)
    name = re.sub(r'\b(user|guide|developer|dg|ug|api|ref|reference|'
                  r'manual|doc|docs|documentation|amazon|aws|'
                  r'latest|v1|v2|2023|2024|2025|2026)\b', '', name)
    name = name.strip()
    
    # Score each service by keyword matches
    scores = {}
    for keyword, service in FILENAME_TO_SERVICE.items():
        if keyword.replace('-', ' ') in name or keyword in filename.lower():
            scores[service] = scores.get(service, 0) + len(keyword)
    
    if scores:
        return max(scores, key=scores.get)
    
    return "general"


def get_display_name(service: str) -> str:
    """Returns the full AWS service display name."""
    DISPLAY_NAMES = {
        "lambda":           "AWS Lambda",
        "s3":               "Amazon S3",
        "ec2":              "Amazon EC2",
        "iam":              "AWS IAM",
        "vpc":              "Amazon VPC",
        "rds":              "Amazon RDS",
        "dynamodb":         "Amazon DynamoDB",
        "cloudformation":   "AWS CloudFormation",
        "cloudwatch":       "Amazon CloudWatch",
        "ecs":              "Amazon ECS",
        "eks":              "Amazon EKS",
        "sagemaker":        "Amazon SageMaker",
        "bedrock":          "Amazon Bedrock",
        "glue":             "AWS Glue",
        "athena":           "Amazon Athena",
        "redshift":         "Amazon Redshift",
        "kinesis":          "Amazon Kinesis",
        "sns":              "Amazon SNS",
        "sqs":              "Amazon SQS",
        "cloudfront":       "Amazon CloudFront",
        "route53":          "Amazon Route 53",
        "elb":              "Elastic Load Balancing",
        "codepipeline":     "AWS CodePipeline",
        "codebuild":        "AWS CodeBuild",
        "codecommit":       "AWS CodeCommit",
        "codedeploy":       "AWS CodeDeploy",
        "secretsmanager":   "AWS Secrets Manager",
        "kms":              "AWS KMS",
        "cloudtrail":       "AWS CloudTrail",
        "waf":              "AWS WAF",
        "stepfunctions":    "AWS Step Functions",
        "apigateway":       "Amazon API Gateway",
        "elasticache":      "Amazon ElastiCache",
        "systemsmanager":   "AWS Systems Manager",
        "general":          "AWS General Documentation",
    }
    return DISPLAY_NAMES.get(service, f"AWS {service.upper()}")

def detect_service(query: str) -> str:
    """
    Detects AWS service from query using exact matching and fuzzy fallback.
    """
    # 1. First try exact keyword matching
    scores = {}
    query_lower = query.lower()
    for keyword, service in FILENAME_TO_SERVICE.items():
        if keyword in query_lower:
            scores[service] = scores.get(service, 0) + 1
    
    service = max(scores, key=scores.get) if scores else None
    
    # 2. If no exact match found, try fuzzy matching
    if not service:
        service = fuzzy_match_service(query)
        if service:
            logger.info(f"Fuzzy matched '{query}' -> '{service}'")
    
    return service or "general"
