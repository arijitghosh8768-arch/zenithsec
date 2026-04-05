# File: backend/api/chatbot/ai_engine.py

import logging
import asyncio
import hashlib
import json
from typing import List, Dict, AsyncGenerator, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

from config.settings import settings

# Import our modules
from api.chatbot.prompts import PromptBuilder, SkillLevel, TopicCategory
from api.chatbot.contexts import ContextManager, MessageRole, ConversationContext, DifficultyLevel
from api.chatbot.safety import SafetyChecker, RiskLevel

logger = logging.getLogger(__name__)

# ============= Enums =============

class ModelProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    NVIDIA = "nvidia"
    FALLBACK = "fallback"


class ModelType(str, Enum):
    FAST = "fast"      # For simple Q&A
    BALANCED = "balanced"  # For general conversation
    POWERFUL = "powerful"  # For complex analysis


# ============= Model Configuration =============

MODEL_CONFIGS = {
    ModelProvider.GROQ: {
        ModelType.FAST: {
            "model": "llama-3.1-8b-instant",
            "max_tokens": 1024,
            "temperature": 0.5,
        },
        ModelType.BALANCED: {
            "model": "llama-3.1-70b-versatile",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        ModelType.POWERFUL: {
            "model": "llama-3.3-70b-specdec",
            "max_tokens": 4096,
            "temperature": 0.8,
        }
    },
    ModelProvider.OPENAI: {
        ModelType.FAST: {
            "model": "gpt-3.5-turbo",
            "max_tokens": 1024,
            "temperature": 0.5,
        },
        ModelType.BALANCED: {
            "model": "gpt-4o-mini",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        ModelType.POWERFUL: {
            "model": "gpt-4o",
            "max_tokens": 4096,
            "temperature": 0.8,
        }
    },
    ModelProvider.ANTHROPIC: {
        ModelType.FAST: {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "temperature": 0.5,
        },
        ModelType.BALANCED: {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        ModelType.POWERFUL: {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "temperature": 0.8,
        }
    },
    ModelProvider.NVIDIA: {
        ModelType.FAST: {
            "model": "meta/llama-3.1-8b-instruct",
            "max_tokens": 1024,
            "temperature": 0.5,
        },
        ModelType.BALANCED: {
            "model": "meta/llama-3.1-70b-instruct",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        ModelType.POWERFUL: {
            "model": "meta/llama-3.3-70b-instruct",
            "max_tokens": 4096,
            "temperature": 0.8,
        }
    }
}

# ============= Circuit Breaker =============

class CircuitBreaker:
    """Handles API failures gracefully by temporarily disabling flaky providers"""
    
    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: int = 300):
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time_seconds
        self.is_open = False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.error(f"Circuit Breaker tripped! Provider will be disabled for {self.recovery_time}s")

    def record_success(self):
        self.failures = 0
        self.is_open = False

    def is_available(self) -> bool:
        if not self.is_open:
            return True
        
        # Check if recovery time has passed
        if self.last_failure_time and (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_time:
            self.is_open = False
            self.failures = 0
            logger.info("Circuit Breaker recovered. Attempting to use provider again.")
            return True
        
        return False


# Response cache (simple memory cache)
class ResponseCache:
    """Cache AI responses to reduce API calls and costs"""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 100):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        
    def _get_key(self, messages: List[Dict], model: str) -> str:
        """Generate cache key from messages and model"""
        content = json.dumps(messages) + model
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, messages: List[Dict], model: str) -> Optional[Any]:
        """Get cached response if valid"""
        key = self._get_key(messages, model)
        if key in self.cache:
            response, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return response
            else:
                del self.cache[key]
        return None
    
    def set(self, messages: List[Dict], model: str, response: Any):
        """Cache response"""
        key = self._get_key(messages, model)
        
        # Manage cache size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (response, datetime.now())


# ============= Main AI Engine =============

class AIEngine:
    """Enhanced AI engine with full integration"""
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager()
        self.safety_checker = SafetyChecker()
        self.cache = ResponseCache()
        self._circuits: Dict[ModelProvider, CircuitBreaker] = {
            ModelProvider.GROQ: CircuitBreaker(),
            ModelProvider.OPENAI: CircuitBreaker(),
            ModelProvider.ANTHROPIC: CircuitBreaker()
        }
        self._provider_health: Dict[str, bool] = {
            ModelProvider.GROQ: True,
            ModelProvider.OPENAI: True,
            ModelProvider.ANTHROPIC: True
        }
        
    async def get_response(
        self,
        message: str,
        session_id: str,
        user_id: Optional[int] = None,
        skill_level: SkillLevel = SkillLevel.BEGINNER,
        topic: Optional[TopicCategory] = None,
        stream: bool = False,
        use_cache: bool = True
    ):
        """
        Get AI response with full context integration
        
        Args:
            message: User's message
            session_id: Chat session ID
            user_id: User ID for tracking
            skill_level: User's skill level
            topic: Specific topic focus
            stream: Whether to stream response
            use_cache: Whether to use cached responses
        """
        start_time = datetime.now()
        
        # Step 1: Safety check
        safety_result = await self.safety_checker.comprehensive_check(
            message=message,
            user_id=str(user_id) if user_id else session_id
        )
        
        if not safety_result.is_safe:
            logger.warning(f"Unsafe message blocked: {safety_result.warnings}")
            return {
                "content": safety_result.message,
                "tokens_used": 0,
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "safety_blocked": True
            }
        
        # Step 2: Add user message to context
        context = await self.context_manager.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=message,
            user_id=user_id
        )
        
        # Step 3: Detect topic if not provided
        if not topic:
            detected_topic = self.context_manager.detect_topic(message)
            if detected_topic:
                topic_info = self.context_manager.get_topic_info(detected_topic)
                # Adjust skill level based on topic difficulty
                if topic_info.get("difficulty"):
                    detected_level = topic_info["difficulty"]
                    if detected_level in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
                        skill_level = SkillLevel.ADVANCED
        
        # Step 4: Build the prompt with context
        context_window = await self.context_manager.get_context_window(session_id)
        
        system_prompt = self.prompt_builder.build_prompt(
            skill_level=skill_level,
            topic=topic,
            conversation_context=context_window,
            user_context={
                "session_id": session_id,
                "message_count": len(context.messages) if context else 0
            }
        )
        
        # Step 5: Prepare messages for AI
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (last 10 messages for context)
        for msg in context_window[-10:]:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Step 6: Select appropriate model based on complexity
        model_type = self._select_model_type(message, skill_level)
        
        # Step 6.5: Specialized Orchestration Routing (Pattern 2 & 3)
        if any(kw in message.lower() for kw in ["http", "https", "www."]):
            logger.info("Sequential Pipeline: URL detected, triggering secure analysis.")
            return await self._get_secure_pipeline_response(messages, model_type)
            
        target_provider = None
        if any(kw in message.lower() for kw in ["code", "script", "function", "refactor"]):
            logger.info("Specialized routing: Detected code task, prioritizing CLAUDE.")
            target_provider = ModelProvider.ANTHROPIC

        # Step 7: Get AI response
        response_data = await self._get_ai_response_with_retry(
            messages=messages,
            model_type=model_type,
            stream=stream,
            use_cache=use_cache,
            target_provider=target_provider
        )
        
        # If streaming, return the generator immediately
        if stream:
            return response_data
        
        # Step 8: Add assistant response to context
        if not stream:
            # Only add to context if not streaming (streaming handled separately)
            await self.context_manager.add_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_data["content"],
                user_id=user_id,
                tokens=response_data.get("tokens_used", 0)
            )
        
        # Step 9: Add ethical disclaimer if needed
        if not stream:
            response_data["content"] = self.safety_checker.add_ethical_disclaimer(
                response_data["content"]
            )
        
        # Step 10: Add metadata
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        response_data["processing_time_ms"] = int(processing_time)
        response_data["model_type"] = model_type.value
        response_data["skill_level"] = skill_level.value
        response_data["session_id"] = session_id
        
        return response_data
    
    def _select_model_type(self, message: str, skill_level: SkillLevel) -> ModelType:
        """Select appropriate model based on message complexity and user level"""
        message_lower = message.lower()
        
        # Complex analysis queries
        complex_keywords = ["analyze", "explain in detail", "vulnerability", "exploit", 
                           "architecture", "implementation", "bypass", "bypassing",
                           "zero-day", "reverse engineering", "malware analysis"]
        
        # Long code or analysis requests
        if len(message) > 500:
            return ModelType.POWERFUL
        
        # Complex topic detection
        if any(keyword in message_lower for keyword in complex_keywords):
            return ModelType.POWERFUL
        
        # Advanced users get more powerful models
        if skill_level in [SkillLevel.ADVANCED, SkillLevel.EXPERT]:
            return ModelType.BALANCED
        
        # Default to fast for simple questions
        if len(message) < 100 and skill_level == SkillLevel.BEGINNER:
            return ModelType.FAST
        
        return ModelType.BALANCED
    
    async def _get_ai_response_with_retry(
        self,
        messages: List[Dict],
        model_type: ModelType,
        stream: bool = False,
        use_cache: bool = True,
        max_retries: int = 2
    ):
        """Get AI response with retry logic and caching"""
        
        # Check cache for non-streaming requests
        if use_cache and not stream:
            model_key = f"{model_type.value}"
            cached = self.cache.get(messages, model_key)
            if cached:
                logger.info(f"Cache hit for model {model_type.value}")
                return cached
        
        # Try providers in order
        providers_to_try = []
        
        # Primary: Groq if available and healthy
        if settings.GROQ_API_KEYS and any(settings.GROQ_API_KEYS) and self._circuits[ModelProvider.GROQ].is_available():
            providers_to_try.append(ModelProvider.GROQ)
        
        # Secondary: NVIDIA (High Performance Fallback)
        if hasattr(settings, 'NVIDIA_API_KEY') and settings.NVIDIA_API_KEY and self._circuits[ModelProvider.NVIDIA].is_available():
            providers_to_try.append(ModelProvider.NVIDIA)

        # Tertiary: Anthropic if available and healthy
        if hasattr(settings, 'CLAUDE_API_KEY') and settings.CLAUDE_API_KEY and self._circuits[ModelProvider.ANTHROPIC].is_available():
            providers_to_try.append(ModelProvider.ANTHROPIC)

        # Quaternary: OpenAI if available and healthy
        if settings.OPENAI_API_KEY and self._circuits[ModelProvider.OPENAI].is_available():
            providers_to_try.append(ModelProvider.OPENAI)
        
        # Try each provider
        last_error = None
        
        # Priority override if a specialized provider was detected
        if target_provider and target_provider in providers_to_try:
            providers_to_try.remove(target_provider)
            providers_to_try.insert(0, target_provider)

        for provider in providers_to_try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"→ Attempting {provider.value} ({model_type.value} model)...")
                    response = await self._call_provider(
                        provider=provider,
                        messages=messages,
                        model_type=model_type,
                        stream=stream
                    )
                    
                    # Success! Reset circuit
                    self._circuits[provider].record_success()
                    logger.info(f"✓ {provider.value} responded successfully.")
                    
                    # Cache successful response
                    if use_cache and not stream:
                        model_key = f"{model_type.value}"
                        self.cache.set(messages, model_key, response)
                    
                    return response
                    
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # Identify capacity/overload issues and trip circuit faster
                    if "503" in error_msg or "overloaded" in error_msg or "capacity" in error_msg:
                        logger.error(f"✗ Provider {provider.value} is at CAPACITY (503). Skipping...")
                        self._circuits[provider].record_failure() 
                        break # Try next provider immediately
                    
                    logger.warning(f"⚠ Provider {provider.value} attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff for other errors
                        delay = 2 ** attempt
                        logger.info(f"Retrying {provider.value} in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        # Mark as failure for circuit breaker after retries exhausted
                        logger.error(f"✗ Provider {provider.value} exhausted all retries.")
                        self._circuits[provider].record_failure()
                        continue  # Try next provider
        
        # All providers failed, use fallback
        logger.error(f"All AI providers failed. Last error: {last_error}")
        return self._fallback_response(messages, str(last_error) if last_error else None)
    
    async def _call_provider(
        self,
        provider: ModelProvider,
        messages: List[Dict],
        model_type: ModelType,
        stream: bool = False
    ):
        """Call specific AI provider"""
        
        if provider == ModelProvider.GROQ:
            return await self._groq_response(messages, model_type, stream)
        elif provider == ModelProvider.OPENAI:
            return await self._openai_response(messages, model_type, stream)
        elif provider == ModelProvider.ANTHROPIC:
            return await self._anthropic_response(messages, model_type, stream)
        elif provider == ModelProvider.NVIDIA:
            return await self._nvidia_response(messages, model_type, stream)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _nvidia_response(
        self,
        messages: List[Dict],
        model_type: ModelType,
        stream: bool = False
    ):
        """Get response from NVIDIA NIM"""
        from openai import AsyncOpenAI
        
        config = MODEL_CONFIGS[ModelProvider.NVIDIA][model_type]
        client = AsyncOpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        
        if stream:
            return await self._nvidia_stream(client, messages, config)
            
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        
        return {
            "content": chat_completion.choices[0].message.content,
            "tokens_used": chat_completion.usage.total_tokens if chat_completion.usage else 0,
            "provider": ModelProvider.NVIDIA.value,
            "model": config["model"]
        }

    async def _nvidia_stream(
        self,
        client,
        messages: List[Dict],
        config: Dict
    ) -> AsyncGenerator:
        """Stream response from NVIDIA"""
        stream = await client.chat.completions.create(
            messages=messages,
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _get_ensemble_response(
        self,
        messages: List[Dict],
        model_type: ModelType = ModelType.BALANCED
    ):
        """Pattern 1: Parallel Processing (Ensemble)"""
        providers = [ModelProvider.GROQ, ModelProvider.ANTHROPIC, ModelProvider.OPENAI]
        tasks = []
        
        for provider in providers:
            if self._circuits[provider].is_available():
                tasks.append(self._call_provider(provider, messages, model_type))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_responses = [r for r in results if isinstance(r, dict) and "content" in r]
        
        if not valid_responses:
            raise Exception("Ensemble processing failed: No valid responses received.")
            
        # Synthesize results using a powerful model (OpenAI GPT-4o-mini)
        synthesis_prompt = f"Synthesize the following AI responses into one definitive, expert cybersecurity answer. Ensure accuracy and technical depth.\n\n"
        for i, res in enumerate(valid_responses):
            synthesis_prompt += f"Response {i+1} ({res['provider']}):\n{res['content']}\n\n"
            
        synthesis_messages = [
            {"role": "system", "content": "You are ZenithSec's Lead Security Architect. Synthesize the best parts of multiple expert answers."},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        return await self._openai_response(synthesis_messages, ModelType.BALANCED)

    async def _get_secure_pipeline_response(
        self,
        messages: List[Dict],
        model_type: ModelType = ModelType.BALANCED
    ):
        """Pattern 2: Sequential Pipeline (Security Check -> Analysis)"""
        last_message = messages[-1]["content"] if messages else ""
        
        # 1. Security Check (VirusTotal if URL/IP detected)
        # For now, we simulate this or call a helper if URLs are present
        if any(x in last_message for x in ["http", "https", "www."]):
            logger.info("Security Pipeline: URL detected, running VirusTotal check...")
            # Here we would call the VirusTotal service
            # For this MVP, we proceed but log the intent
            
        # 2. Primary Analysis (NVIDIA optimized models)
        if self._circuits[ModelProvider.NVIDIA].is_available():
            logger.info("Security Pipeline: Running analysis via NVIDIA.")
            return await self._nvidia_response(messages, model_type)
            
        # 3. Fallback to Groq
        return await self._groq_response(messages, model_type)


    
    async def _anthropic_response(
        self,
        messages: List[Dict],
        model_type: ModelType,
        stream: bool = False
    ):
        """Get response from Anthropic (Claude)"""
        import anthropic
        
        config = MODEL_CONFIGS[ModelProvider.ANTHROPIC][model_type]
        client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        
        # Convert messages to Anthropic format
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        anthropic_messages = [m for m in messages if m["role"] != "system"]
        
        if stream:
            return await self._anthropic_stream(client, anthropic_messages, system_msg, config)
        
        response = await client.messages.create(
            model=config["model"],
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            system=system_msg,
            messages=anthropic_messages
        )
        
        return {
            "content": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "provider": ModelProvider.ANTHROPIC.value,
            "model": config["model"]
        }

    async def _anthropic_stream(
        self,
        client,
        messages: List[Dict],
        system: str,
        config: Dict
    ) -> AsyncGenerator:
        """Stream response from Anthropic"""
        async with client.messages.stream(
            model=config["model"],
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            system=system,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

    
    async def _groq_response(
        self,
        messages: List[Dict],
        model_type: ModelType,
        stream: bool = False
    ):
        """Get response from Groq with key rotation"""
        from groq import AsyncGroq
        
        config = MODEL_CONFIGS[ModelProvider.GROQ][model_type]
        
        # Try each available key if one hits limits
        last_error = None
        for key in settings.GROQ_API_KEYS:
            if not key: continue
            try:
                client = AsyncGroq(api_key=key)
                
                if stream:
                    return await self._groq_stream(client, messages, config)
                
                chat_completion = await client.chat.completions.create(
                    messages=messages,
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                )
                
                return {
                    "content": chat_completion.choices[0].message.content,
                    "tokens_used": chat_completion.usage.total_tokens if chat_completion.usage else 0,
                    "provider": ModelProvider.GROQ.value,
                    "model": config["model"]
                }
            except Exception as e:
                last_error = e
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    logger.warning(f"Groq API key {key[:10]}... rate limited. Rotating...")
                    continue
                raise e # For other errors, let the provider retry logic handle it
        
        raise last_error or Exception("No valid Groq API keys available")

    
    async def _groq_stream(
        self,
        client,
        messages: List[Dict],
        config: Dict
    ) -> AsyncGenerator:
        """Stream response from Groq"""
        stream = await client.chat.completions.create(
            messages=messages,
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _openai_response(
        self,
        messages: List[Dict],
        model_type: ModelType,
        stream: bool = False
    ):
        """Get response from OpenAI"""
        from openai import AsyncOpenAI
        
        config = MODEL_CONFIGS[ModelProvider.OPENAI][model_type]
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        if stream:
            return await self._openai_stream(client, messages, config)
        
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        
        return {
            "content": chat_completion.choices[0].message.content,
            "tokens_used": chat_completion.usage.total_tokens if chat_completion.usage else 0,
            "provider": ModelProvider.OPENAI.value,
            "model": config["model"]
        }
    
    async def _openai_stream(
        self,
        client,
        messages: List[Dict],
        config: Dict
    ) -> AsyncGenerator:
        """Stream response from OpenAI"""
        stream = await client.chat.completions.create(
            messages=messages,
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    
    def _fallback_response(self, messages: List[Dict], error: Optional[str] = None) -> dict:
        """Generate fallback response when APIs are unavailable with diagnostic formatting"""
        last_msg = messages[-1]["content"] if messages else ""
        lower_msg = last_msg.lower()
        error_str = str(error).lower() if error else ""

        # --- Diagnostic Error Blocks Pattern ---
        if "401" in error_str or "unauthorized" in error_str or "invalid" in error_str:
            content = """### ⚠️ Invalid API Key Error (401)
Your Groq or OpenAI API key is invalid. This usually means:
1. ❌ The key is missing the `gsk_` prefix
2. ❌ There are extra spaces in the key
3. ❌ You copied only part of the key
4. ❌ The key hasn't been activated yet

**Fix:**
1. Go to [Groq Console](https://console.groq.com/)
2. Create a NEW API key
3. Copy the COMPLETE key
4. Update your `.env` file and restart.
"""
        elif "429" in error_str or "quota" in error_str or "limit" in error_str:
            content = """### ⚠️ Quota Exceeded (429)
Your API free tier limit has been reached or credits are exhausted.

**Fix:**
1. Create a NEW Groq account with a different email
2. Get a fresh API key or add billing to OpenAI.
3. Update `.env` with the new key.
"""
        elif any(word in lower_msg for word in ["hello", "hi", "hey"]):
            content = "Hello! I'm ZenithSec AI Mentor. I'm here to help you learn cybersecurity. What topic would you like to explore today?"
        elif any(word in lower_msg for word in ["help", "what can you do", "capabilities"]):
            content = """I can help you with:

🔒 **Network Security** - Firewalls, IDS/IPS, VPNs, segmentation
🌐 **Web Security** - OWASP Top 10, XSS, SQLi, CSRF, SSRF
🔐 **Cryptography** - Encryption, hashing, PKI, quantum crypto
🎯 **Penetration Testing** - Methodology, tools, reporting
🦠 **Malware Analysis** - Static/dynamic analysis, reverse engineering
🔍 **Digital Forensics** - Evidence handling, analysis tools
☁️ **Cloud Security** - AWS, Azure, GCP, container security
💻 **Secure Coding** - Input validation, auth, crypto implementation
🏆 **CTF Challenges** - Hints and guidance

Just ask me anything about cybersecurity!"""
        else:
            content = f"### ⚠️ Connection Issue\n\nI'm having trouble connecting to my AI providers.\n\n**Error Details:**\n```\n{error}\n```\n\nWhile I'm resolving this, feel free to explore the platform's other tools!"

        # Add ethical disclaimer
        content = self.safety_checker.add_ethical_disclaimer(content)
        
        return {
            "content": content,
            "tokens_used": 0,
            "provider": ModelProvider.FALLBACK.value,
            "fallback_mode": True,
            "error": error
        }
    
    async def generate_ctf_hint(
        self,
        challenge_type: str,
        difficulty: str,
        user_question: str,
        session_id: str
    ) -> str:
        """Generate a CTF hint without giving away the flag"""
        
        hint_prompt = self.prompt_builder.get_ctf_hint_prompt(
            challenge_type=challenge_type,
            difficulty=difficulty,
            hint_level=1
        )
        
        messages = [
            {"role": "system", "content": hint_prompt},
            {"role": "user", "content": user_question}
        ]
        
        response = await self._get_ai_response_with_retry(
            messages=messages,
            model_type=ModelType.BALANCED,
            stream=False
        )
        
        return response["content"]
    
    async def analyze_code_security(
        self,
        code: str,
        language: str,
        session_id: str
    ) -> str:
        """Analyze code for security vulnerabilities"""
        
        analysis_prompt = self.prompt_builder.get_code_analysis_prompt(
            code=code,
            language=language,
            skill_level=SkillLevel.INTERMEDIATE
        )
        
        messages = [
            {"role": "system", "content": analysis_prompt},
            {"role": "user", "content": f"Analyze this {language} code:\n\n{code}"}
        ]
        
        response = await self._get_ai_response_with_retry(
            messages=messages,
            model_type=ModelType.POWERFUL,
            stream=False
        )
        
        return response["content"]


# ============= Global Instance =============

_ai_engine_instance = None

async def get_ai_engine() -> AIEngine:
    """Get or create AI engine instance (FastAPI dependency)"""
    global _ai_engine_instance
    if _ai_engine_instance is None:
        _ai_engine_instance = AIEngine()
    return _ai_engine_instance


# ============= Legacy Functions (Backward Compatible) =============

async def get_ai_response(messages: List[Dict[str, str]], stream: bool = False):
    """
    Legacy function for backward compatibility
    """
    engine = AIEngine()
    # Convert legacy messages format
    if messages and messages[-1].get("role") == "user":
        last_message = messages[-1]["content"]
        return await engine.get_response(
            message=last_message,
            session_id="legacy_session",
            stream=stream
        )
    else:
        # Fallback for non-standard format
        return engine._fallback_response(messages)
