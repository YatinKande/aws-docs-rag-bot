from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.retrieval.semantic_search import RetrievalService
from backend.services.api_key_manager import APIKeyManager
from backend.services.cloud_providers.factory import CloudProviderFactory
from backend.services.cloud_providers.aws.dynamic_aws_handler import DynamicAWSHandler
from backend.services.llm_service import LLMService

class QueryRouter:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.retrieval_service = RetrievalService()
        self.key_manager = APIKeyManager()
        self.llm_service = LLMService()

    async def route(self, query: str, selected_source: str = "auto", selected_db: str = "faiss") -> Dict[str, Any]:
        """Main routing logic for all providers and RAG."""
        query_l = query.lower()
        
        # 1. Handle Explicit Selections
        if selected_source == "docs":
            return await self._handle_rag(query, selected_db)
            
        if selected_source in ["aws", "gcp", "azure"]:
            keys = await self.key_manager.get_active_keys(self.db, "default-user", selected_source)
            if keys:
                return await self._handle_cloud_api(query, keys[0])
            else:
                return {"source_type": "error", "message": f"No active {selected_source.upper()} keys found."}

        # 2. Intelligent Auto-Routing
        is_cloud = any(k in query_l for k in ["cost", "bill", "usage", "ec2", "s3", "bucket", "buckets", "storage", "lambda", "rds", "iam", "instance", "function", "database", "gcp", "azure"])
        
        if is_cloud:
            # Detect provider from query or default to first available
            target_provider = "aws"
            if "gcp" in query_l: target_provider = "gcp"
            elif "azure" in query_l: target_provider = "azure"
            
            keys = await self.key_manager.get_active_keys(self.db, "default-user", target_provider)
            if keys:
                return await self._handle_cloud_api(query, keys[0])

        return await self._handle_rag(query)

    async def _handle_rag(self, query: str, database: str = "faiss"):
        results = await self.retrieval_service.semantic_search(query, database=database)
        return {
            "source_type": "docs",
            "data": results,
            "answer_preview": f"Retrieved {len(results)} relevant sections from knowledge base ({database})."
        }

    async def _handle_cloud_api(self, query: str, api_key_model):
        creds = await self.key_manager.get_decrypted_credentials(self.db, api_key_model.id)
        if not creds:
            return {"source_type": "error", "message": "Failed to decrypt credentials"}
            
        provider = CloudProviderFactory.get_provider(api_key_model.provider, creds)
        
        # Dynamic AWS query handling with LLM interpretation
        if api_key_model.provider == "aws":
            # Use LLM to interpret the query
            parsed_query = await self.llm_service.interpret_aws_query(query)
            
            # Execute dynamic AWS query
            handler = DynamicAWSHandler(provider)
            data = await handler.execute_query(parsed_query)
            
            # Format response based on result
            if data.get('status') == 'success':
                return {
                    "source_type": "api",
                    "provider": "aws",
                    "service": data.get('service'),
                    "data": data,
                    "answer_preview": self._format_aws_preview(data, parsed_query)
                }
            else:
                return {
                    "source_type": "error",
                    "message": data.get('message', 'Failed to execute AWS query')
                }
        
        # Generic cloud response for other providers (GCP, Azure)
        data = await provider.query("general", {"query": query})
        return {
            "source_type": "api",
            "provider": api_key_model.provider,
            "data": data,
            "answer_preview": f"Query processed via {api_key_model.provider.upper()} API."
        }
    
    def _format_aws_preview(self, data: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
        """Format AWS response preview based on query intent and service."""
        service = data.get('service', 'AWS')
        intent = parsed_query.get('intent', 'list')
        result_data = data.get('data', {})
        
        # Count intent
        if intent == 'count':
            if service == 's3' and 'object_count' in result_data:
                count = result_data['object_count']
                bucket = result_data.get('bucket', '')
                size_mb = result_data.get('total_size_mb', 0)
                return f"Found {count} objects in {bucket} ({size_mb} MB total)"
            elif 'count' in result_data:
                return f"Found {result_data['count']} {service.upper()} resources"
        
        # List intent
        if intent == 'list':
            count = result_data.get('count', 0)
            if service == 's3' and 'buckets' in result_data:
                return f"Retrieved {count} S3 bucket{'s' if count != 1 else ''}"
            elif service == 'ec2' and 'instances' in result_data:
                return f"Retrieved {count} EC2 instance{'s' if count != 1 else ''}"
            elif service == 'lambda' and 'functions' in result_data:
                return f"Retrieved {count} Lambda function{'s' if count != 1 else ''}"
            elif service == 'rds' and 'instances' in result_data:
                return f"Retrieved {count} RDS instance{'s' if count != 1 else ''}"
            elif service == 'iam':
                return f"Retrieved {count} IAM {result_data.get('users', result_data.get('roles', []))}"
            elif service == 'ce':
                total = result_data.get('total', 0)
                return f"Retrieved AWS billing data: Total ${total:.2f}"
        
        # Default preview
        return f"Retrieved {service.upper()} data successfully"
