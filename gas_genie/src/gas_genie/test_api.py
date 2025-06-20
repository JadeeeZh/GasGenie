import aiohttp
import asyncio
import json
from sentient_agent_framework import Session, Query, ResponseHandler

async def test_api():
    async with aiohttp.ClientSession() as session:
        # Test health check endpoint
        async with session.get("http://localhost:8000/health") as response:
            print("Health check response:", await response.json())
        
        # Test assist endpoint
        test_query = {
            "query": {
                "prompt": "What is the current gas price? Should I send my transaction now?",
                "id": "test-1"
            }
        }
        
        async with session.post(
            "http://localhost:8000/assist",
            json=test_query
        ) as response:
            print("Assist response status:", response.status)
            async for line in response.content:
                if line:
                    print("Received chunk:", line.decode().strip())

if __name__ == "__main__":
    asyncio.run(test_api()) 