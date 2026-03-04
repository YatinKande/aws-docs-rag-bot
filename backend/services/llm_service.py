import litellm
import asyncio
import logging
import os
import json
import base64
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.core.config import settings
from backend.utils.source_validator import validate_source, get_valid_sources

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # LiteLLM configuration
        self.text_model = f"ollama/{settings.OLLAMA_TEXT_MODEL}"
        self.vision_model = f"ollama/{settings.OLLAMA_VISION_MODEL}"
        self.base_url = settings.OLLAMA_BASE_URL
        
        # Fallback list
        self.fallbacks = [
            f"ollama/llama3",
            f"ollama/mistral"
        ]
        
        self._valid_sources = []
        
        # Verify Ollama connection and detect models (optional but good for log)
        logger.info(f"LLM initialized. Primary Text: {self.text_model}, Vision: {self.vision_model}")

    async def _call_llm(self, messages: List[Dict[str, str]], model: Optional[str] = None, json_mode: bool = False) -> str:
        """Unified LLM call via LiteLLM with fallback logic."""
        target_model = model or self.text_model
        
        try:
            response = await litellm.acompletion(
                model=target_model,
                messages=messages,
                api_base=self.base_url,
                temperature=0,
                response_format={"type": "json_object"} if json_mode else None,
                timeout=60
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error with primary model {target_model}: {e}. Trying fallbacks...")
            for fb in self.fallbacks:
                try:
                    response = await litellm.acompletion(
                        model=fb,
                        messages=messages,
                        api_base=self.base_url,
                        temperature=0,
                        timeout=30
                    )
                    return response.choices[0].message.content
                except:
                    continue
            
            raise e

    async def describe_image(self, image_path: str) -> str:
        """Describes an image using Ollama Vision via LiteLLM."""
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image for a technical Knowledge Base. Describe text, components, and workflows shown."},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_data}"
                        }
                    ]
                }
            ]
            
            return await self._call_llm(messages, model=self.vision_model)
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            return f"Error describing image: {str(e)}"

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classifies question intent and identifies target document/topic."""
        prompt = f"""Analyze the user query and identify the specific AWS topic, document type, or intent.
Query: "{query}"

Return a JSON object:
{{
  "topic": "service or topic name (e.g. s3, ec2, lambda)",
  "intent": "fact_check | how_to | troubleshooting | pricing",
  "keywords": ["list", "of", "relevant", "keywords"]
}}"""
        
        try:
            res = await self._call_llm([{"role": "user", "content": prompt}], json_mode=True)
            return json.loads(res)
        except:
            return {"topic": None, "intent": "general", "keywords": []}

    async def evaluate_answer(self, query: str, context: str, answer: str) -> int:
        """LLM Judge: Evaluates if the answer is grounded in retrieved context (1-5)."""
        if not settings.ENABLE_LLM_JUDGE:
            return 5

        prompt = f"""You are a judge evaluating a RAG bot's response.
Query: {query}
Retrieved Context: {context}
Generated Answer: {answer}

Rules:
- Score 5: Answer perfectly grounded in context.
- Score 1: Answer has hallucinations or uses outside info not in context.

Return ONLY a single integer (1, 2, 3, 4, 5)."""
        
        try:
            res = await self._call_llm([{"role": "user", "content": prompt}])
            score = int(''.join(filter(str.isdigit, res[:5])))
            return score
        except:
            return 3 # Neutral fallback

    def update_valid_sources(self, sources: list):
        """Called automatically when new doc is uploaded."""
        self._valid_sources = sources
        logger.info(f"[LLM] Valid sources updated: {sources}")

    def preprocess_query(self, query: str) -> str:
        """Fix typos in query before processing"""
        from backend.utils.service_detection import fuzzy_match_service
        
        words = query.split()
        corrected = []
        
        for word in words:
            # Clean symbols for better matching
            clean_word = re.sub(r'[^\w\s]', '', word)
            matched = fuzzy_match_service(clean_word)
            if matched and matched != clean_word.lower():
                logger.info(f"Query correction: '{word}' -> '{matched}'")
                corrected.append(matched)
            else:
                corrected.append(word)
        
        return " ".join(corrected)

    async def generate_response(self, query: str, context: str, sources: List[str], service: str = "general", learned_insights: str = "") -> str:
        """Generates a final response with LLM Judge evaluation and regeneration."""
        
        # 0. Preprocess query to fix typos
        original_query = query
        query = self.preprocess_query(query)
        system_prompt = self.build_rag_prompt(query, context, sources, service)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nInsights: {learned_insights}"}
        ]
        
        answer = await self._call_llm(messages)
        
        # Validate and correct the source citation
        valid_sources = get_valid_sources()
        validated_source = validate_source(
            cited_source=answer,
            valid_sources=valid_sources,
            service=service
        )

        # Force replace any fake source in the answer
        fake_sources = [
            "aws_lambda.md", "lambda-limits.md", 
            "aws-docs.pdf", "documentation.pdf",
            "aws_s3.md", "aws_ec2.md", "unknown"
        ]
        for fake in fake_sources:
            if fake in answer:
                answer = answer.replace(fake, validated_source)

        # Ensure Source is present and validated
        if "Source:" not in answer:
            answer = f"{answer}\n\nSource: {validated_source}"
        
        # 2. LLM Judge Check
        if settings.ENABLE_LLM_JUDGE:
            score = await self.evaluate_answer(query, context, answer)
            logger.info(f"LLM Judge Score: {score}")
            
            if score < 3:
                logger.info("Answer score too low. Regenerating with stricter constraints...")
                strict_prompt = "STRICT: Your previous answer was ungrounded. Use ONLY the provided context snippets. Be precise. No hallucinations."
                messages.append({"role": "assistant", "content": answer})
                messages.append({"role": "user", "content": strict_prompt})
                answer = await self._call_llm(messages)
                
                # Re-validate after regeneration
                validated_source = validate_source(cited_source=answer, valid_sources=valid_sources, service=service)
                for fake in fake_sources:
                    if fake in answer:
                        answer = answer.replace(fake, validated_source)
                if "Source:" not in answer:
                    answer = f"{answer}\n\nSource: {validated_source}"
        
        return answer

    def build_rag_prompt(self, question: str, context: str, sources: List[str], service: str) -> str:
        """Constructs the structured RAG prompt with dynamic sources and enhanced facts."""
        from backend.utils.source_validator import get_valid_sources
        from backend.utils.service_detection import get_display_name
        
        # Always get fresh list from registry
        all_valid_sources = get_valid_sources()
        
        sources_str = ", ".join(sources) if sources else f"{service}-docs.pdf"
        primary_source = sources[0] if sources else f"{service}-dg.pdf"
        
        valid_list = "\n".join([f"  - {s}" for s in all_valid_sources])
        
        return f"""You are an expert AWS Cloud Assistant.
Answer using ONLY the retrieved context below.

RETRIEVED CONTEXT:
{context}

DETECTED SERVICE: {get_display_name(service)}

CRITICAL FACTS — NEVER contradict these:
LAMBDA:
- /tmp default = 512 MB
- /tmp maximum = 10,240 MB
- /tmp and memory(RAM) are COMPLETELY SEPARATE
- Max timeout = 900 seconds (15 minutes)
- Default timeout = 3 seconds
- Max memory = 10,240 MB
- NEVER suggest timeout fix for storage errors

S3:
- Max object size = 5 TB
- Max single PUT = 5 GB
- Multipart required above 5 GB

EC2:
- Default Elastic IPs per region = 5
- IMDSv2 protects against SSRF
- Instance store data lost on stop/terminate

IAM:
- Explicit Deny ALWAYS wins over Allow
- Max managed policies per role = 10

VPC:
- Max VPCs per region = 5 (soft limit)
- VPC peering does NOT support transitive routing

VALID SOURCE FILES — ONLY cite these:
{valid_list}

RULES:
1. ONLY cite filenames from the VALID SOURCE FILES list
2. NEVER invent filenames like aws_lambda.md
3. NEVER cite .md files unless user uploaded one
4. Source must match the service being discussed
5. If answer not in context say: 
   "This topic needs more documentation. 
    Upload {service}-dg.pdf for detailed answers."
6. End every answer with:
   📄 Source: {primary_source}

QUESTION: {question}

ANSWER:"""

# Global instance for easy access
llm_service = LLMService()
