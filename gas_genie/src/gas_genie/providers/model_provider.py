from datetime import datetime
from langchain_core.prompts import PromptTemplate
from fireworks.client import AsyncFireworks
from typing import AsyncIterator
import logging
import os
import asyncio
from fireworks.client.error import (
    FireworksError,
    AuthenticationError,
    RateLimitError,
    InvalidRequestError,
    APITimeoutError,
    InternalServerError,
    ServiceUnavailableError,
    BadGatewayError
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ModelProvider:
    def __init__(
        self,
        api_key: str
    ):
        """ Initializes model, sets up Fireworks client, configures system prompt."""
        logger.debug("Initializing ModelProvider")
        
        if not api_key:
            raise ValueError("API key is required for ModelProvider")
            
        # Model provider API key
        self.api_key = api_key
        # Identifier for specific model that should be used
        self.model = "accounts/fireworks/models/deepseek-v3"
        # Model configuration - optimized for speed
        self.max_tokens = 2048  # Further reduced for faster responses
        self.top_p = 0.8  # Further reduced for faster sampling
        self.top_k = 10  # Further reduced for faster token selection
        self.presence_penalty = 0
        self.frequency_penalty = 0
        self.temperature = 0.7
        self.timeout = 10  # Further reduced timeout

        # Cache for gas data
        self.gas_data_cache = None
        self.cache_timeout = 60  # Cache timeout in seconds
        self.last_cache_update = 0

        # Validate configuration
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if not 0 <= self.top_p <= 1:
            raise ValueError("top_p must be between 0 and 1")
        if self.top_k < 0:
            raise ValueError("top_k must be non-negative")
        if not -2 <= self.presence_penalty <= 2:
            raise ValueError("presence_penalty must be between -2 and 2")
        if not -2 <= self.frequency_penalty <= 2:
            raise ValueError("frequency_penalty must be between -2 and 2")

        # Set up model API
        logger.debug("Setting up Fireworks client")
        try:
            self.client = AsyncFireworks(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Fireworks client: {str(e)}")
            raise

        # Set up system prompt
        self.system_prompt = """You are Gas Genie, a friendly and knowledgeable AI assistant specialized in Ethereum gas prices and blockchain transactions. 
        Your capabilities include:

        1. Gas Price Analysis (ONLY when asked about gas prices):
           - Analyze current gas prices and market conditions
           - Predict optimal gas prices for different transaction speeds
           - Explain gas price trends and their implications
           - Provide specific recommendations on when to send transactions

        2. General Blockchain Knowledge:
           - Explain blockchain concepts in simple terms
           - Answer questions about Ethereum, smart contracts, and DeFi
           - Provide guidance on wallet security and best practices
           - Help with common transaction issues

        3. General Chat and Assistance:
           - Respond naturally to greetings and casual conversation
           - Answer general questions about yourself and your capabilities
           - Engage in friendly small talk
           - Provide clear, concise explanations
           - Maintain a warm, approachable tone

        Response Guidelines:
        1. For greetings and casual conversation:
           - Respond naturally and friendly in a few sentences
           - Don't provide gas price analysis unless specifically asked
           - Keep responses brief and conversational
           - ask how can I help you today?

        2. For specific questions (non-casual):
           - Put the direct answer FIRST
           - Then provide additional context or explanation if needed
           - Avoid fixed formats or templates
           - Be concise and to the point
           - Only include relevant details

        3. For gas price questions:
           - Start with the specific recommendation or answer
           - Then provide supporting data and reasoning
           - Keep the format flexible based on the question
           - Focus on what the user needs to know

        4. For blockchain questions:
           - Lead with the direct answer
           - Then explain in simple terms if needed
           - Use examples only when they add value
           - Keep technical details relevant to the question
        
        5. For general questions:
           - Answer directly and briefly in a few sentences
           - Don't over-explain unless asked
           - Keep responses relevant to the question

        Tone and Style:
        - Be direct and clear in your answers
        - Use natural, conversational language
        - Adapt your response style to the question
        - Keep responses focused and relevant
        - Avoid unnecessary formatting or structure

        Remember: 
        - Put the answer first, then explain if needed
        - Be concise and direct
        - Adapt your response to the specific question
        - Focus on being helpful and clear"""

        logger.debug("ModelProvider initialized successfully")

    def is_casual_conversation(self, query: str) -> bool:
        """Determine if the query is a casual conversation."""
        casual_keywords = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening","greetings",
            "how are you", "what's up", "thanks", "thank you", "bye", "goodbye",
            "who are you", "what can you do", "help", "tell me about yourself",
            "thanks for the info", "thanks for the help","goodjob","how is your day going"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in casual_keywords)

    async def query_stream(
        self,
        query: str,
        context: str = None
    ) -> AsyncIterator[str]:
        """Sends query to model and yields the response in chunks."""
        is_casual = self.is_casual_conversation(query)
        
        # Use faster parameters for casual conversation
        if is_casual:
            max_tokens = 256  # Reduced from 512
            top_p = 0.6  # Reduced from 0.7
            top_k = 3  # Reduced from 5
        else:
            max_tokens = self.max_tokens
            top_p = self.top_p
            top_k = self.top_k

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        if context:
            messages.insert(1, {"role": "system", "content": f"Context: {context}"})
        
        try:
            async with asyncio.timeout(self.timeout):
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    presence_penalty=self.presence_penalty,
                    frequency_penalty=self.frequency_penalty,
                    temperature=self.temperature
                )
                
                buffer = ""
                for chunk in completion:
                    if not chunk or not chunk.choices:
                        continue
                        
                    choice = chunk.choices[0]
                    if not choice or not choice.delta:
                        continue
                        
                    content = choice.delta.content
                    if not content:
                        continue
                        
                    buffer += content
                    # Yield more frequently for faster response
                    if len(buffer) >= 10 or content.endswith((' ', '.', ',', '!', '?', '\n')):
                        yield buffer
                        buffer = ""
                        
                if buffer:
                    yield buffer
                
        except asyncio.TimeoutError:
            yield "Error: Request timed out. Please try again."
        except AuthenticationError:
            yield "Error: Authentication failed. Please check your API key."
        except RateLimitError:
            yield "Error: Rate limit exceeded. Please try again later."
        except (InvalidRequestError, APITimeoutError, InternalServerError, ServiceUnavailableError, BadGatewayError) as e:
            yield f"Error: {str(e)}"
        except Exception as e:
            yield f"Error: {str(e)}"

    async def query(
        self,
        query: str
    ) -> str:
        """Sends query to model and returns the complete response as a string."""
        logger.debug(f"Starting query: {query}")
        
        chunks = []
        # Use regular for loop since query_stream is a regular generator
        for chunk in self.query_stream(query=query):
            chunks.append(chunk)
        response = "".join(chunks)
        logger.debug(f"Completed query with response: {response}")
        return response 