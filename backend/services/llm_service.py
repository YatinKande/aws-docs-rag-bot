from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from backend.core.config import settings
from typing import List, Dict, Any
import os

class LLMService:
    def __init__(self):
        # Primary: Local Ollama (Free)
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            self.llm = ChatOllama(
                model=ollama_model,
                base_url=ollama_base_url,
                temperature=0
            )
            # We don't verify connection here to keep init fast, 
            # but if it fails during invoke we can fallback
        except Exception:
            self.llm = None

        # Optional Fallbacks: Google Gemini or OpenAI
        if not self.llm:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if google_api_key:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=google_api_key,
                    temperature=0,
                    max_output_tokens=2048
                )
            else:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    from langchain_openai import ChatOpenAI
                    self.llm = ChatOpenAI(temperature=0, model="gpt-4o")

    async def interpret_aws_query(self, query: str) -> Dict[str, Any]:
        """
        Interprets a natural language AWS query and extracts structured information.
        
        Args:
            query: Natural language AWS query (e.g., "How many objects are in my chatbot-yatin bucket?")
            
        Returns:
            Dict containing:
                - service: AWS service name (s3, ec2, lambda, etc.)
                - operation: API operation (list, describe, get, count)
                - resources: Dict of resource identifiers (bucket_name, instance_id, etc.)
                - filters: Dict of filtering criteria (region, state, etc.)
                - intent: High-level intent (count, list, describe)
                - confidence: Confidence score (0-1)
                - fallback: Whether fallback parsing was used
        """
        if not self.llm:
            # Fallback to keyword-based parsing
            return self._fallback_parse_aws_query(query)
        
        from langchain_core.messages import HumanMessage, SystemMessage
        import json
        
        system_prompt = """You are an AWS query parser. Analyze AWS-related questions and extract structured information.

SUPPORTED AWS SERVICES:
- s3: S3 buckets and objects
- ec2: EC2 instances, regions, VPCs, security groups
- lambda: Lambda functions
- rds: RDS database instances
- iam: IAM users and roles (read-only)
- ce: Cost Explorer (billing data)

COMMON OPERATIONS:
- list: List resources (list_buckets, list_functions, describe_instances)
- describe: Get details about resources
- get: Retrieve specific resource information
- count: Count resources

Extract and return ONLY a JSON object with these fields:
{
  "service": "service_name",
  "operation": "operation_type",
  "resources": {"key": "value"},
  "filters": {"key": "value"},
  "intent": "count|list|describe|get",
  "confidence": 0.0-1.0
}

EXAMPLES:

Query: "How many objects are in my chatbot-yatin bucket?"
Response: {"service": "s3", "operation": "list_objects", "resources": {"bucket_name": "chatbot-yatin"}, "filters": {}, "intent": "count", "confidence": 0.95}

Query: "List all my S3 buckets"
Response: {"service": "s3", "operation": "list_buckets", "resources": {}, "filters": {}, "intent": "list", "confidence": 0.98}

Query: "What EC2 instances are running?"
Response: {"service": "ec2", "operation": "describe_instances", "resources": {}, "filters": {"state": "running"}, "intent": "list", "confidence": 0.92}

Query: "Show me Lambda functions in us-east-1"
Response: {"service": "lambda", "operation": "list_functions", "resources": {}, "filters": {"region": "us-east-1"}, "intent": "list", "confidence": 0.90}

Return ONLY the JSON object, no additional text."""

        try:
            prompt = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Query: {query}")
            ]
            
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            parsed['fallback'] = False
            
            # Validate required fields
            required = ['service', 'operation', 'intent']
            if not all(k in parsed for k in required):
                raise ValueError("Missing required fields in LLM response")
            
            return parsed
            
        except Exception as e:
            # Fallback to keyword-based parsing
            import logging
            logging.warning(f"LLM query interpretation failed: {e}. Using fallback parser.")
            return self._fallback_parse_aws_query(query)
    
    def _fallback_parse_aws_query(self, query: str) -> Dict[str, Any]:
        """Fallback keyword-based AWS query parser when LLM is unavailable."""
        query_lower = query.lower()
        
        # Service detection
        service = None
        if any(k in query_lower for k in ['s3', 'bucket']):
            service = 's3'
        elif any(k in query_lower for k in ['ec2', 'instance']):
            service = 'ec2'
        elif any(k in query_lower for k in ['lambda', 'function']):
            service = 'lambda'
        elif any(k in query_lower for k in ['rds', 'database']):
            service = 'rds'
        elif any(k in query_lower for k in ['iam', 'user', 'role']):
            service = 'iam'
        elif any(k in query_lower for k in ['cost', 'bill', 'spending']):
            service = 'ce'
        
        # Intent detection
        intent = 'list'
        if any(k in query_lower for k in ['how many', 'count', 'number of']):
            intent = 'count'
        elif any(k in query_lower for k in ['describe', 'details', 'info about']):
            intent = 'describe'
        
        # Resource extraction (simple pattern matching)
        resources = {}
        if service == 's3':
            # Try to extract bucket name
            import re
            bucket_match = re.search(r'bucket[:\s]+([a-z0-9\-]+)', query_lower)
            if bucket_match:
                resources['bucket_name'] = bucket_match.group(1)
        
        # Filter extraction
        filters = {}
        if 'running' in query_lower:
            filters['state'] = 'running'
        if 'stopped' in query_lower:
            filters['state'] = 'stopped'
        
        # Region extraction
        import re
        region_match = re.search(r'(us|eu|ap|ca|sa|me|af)-(east|west|north|south|central|northeast|southeast)-\d', query_lower)
        if region_match:
            filters['region'] = region_match.group(0)
        
        return {
            'service': service or 's3',  # Default to S3
            'operation': 'list',
            'resources': resources,
            'filters': filters,
            'intent': intent,
            'confidence': 0.6,  # Lower confidence for fallback
            'fallback': True
        }

    async def generate_response(self, query: str, context: str, source_info: str) -> str:
        """Generates a final response based on query, context, and source info."""
        if not self.llm:
            return f"LLM not configured. Please add GOOGLE_API_KEY to your .env file.\n\nRaw context: {context[:200]}..."
        
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import HumanMessage, SystemMessage

        # Refined RAG prompt for less hallucination
        system_prompt = f"""You are a professional, accurate Cloud Intelligence Assistant. 
        Your goal is to provide precise answers based ONLY on the provided context and source information.

        STRICT RULES:
        1. If the answer is not contained within the Context, state: "I'm sorry, I don't have enough information in the uploaded documents to answer that."
        2. Do NOT use outside knowledge or hallucinate details.
        3. Be concise but comprehensive.
        4. Cite the source information provided (e.g., "Based on the knowledge base (FAISS)...").

        CONTEXT:
        {context}

        SOURCE INFORMATION:
        {source_info}
        """

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            error_msg = str(e)
            if "11434" in error_msg or "Connection refused" in error_msg:
                return "Error: Ollama connection failed. Please ensure Ollama is running (`ollama serve`)."
            return f"Error generating response: {error_msg}"
