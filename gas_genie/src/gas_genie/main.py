from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import logging
import asyncio
from .gas_genie import GasGenie
from .providers.model_provider import ModelProvider
import os
import json
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
logger.info("Initializing ModelProvider...")
model_provider = ModelProvider(api_key=os.getenv("FIREWORKS_API_KEY"))
logger.info("Initializing GasGenie...")
agent = GasGenie("Gas Genie")
logger.info("Agent initialization complete")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/assist")
async def assist(request: Request):
    """Handle assistance requests with streaming response."""
    try:
        logger.info("Received assist request")
        data = await request.json()
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        
        query_text = data.get("query", {}).get("prompt")
        query_id = data.get("query", {}).get("id", "unknown")
        
        logger.info(f"Processing query: {query_text}")
        logger.debug(f"Query ID: {query_id}")
        
        if not query_text:
            logger.error("No query provided in request")
            return JSONResponse(
                status_code=400,
                content={"error": "No query provided"}
            )
            
        logger.debug("Starting response generation")
        
        async def generate_response():
            try:
                logger.debug("Starting to generate response chunks")
                logger.debug("Calling agent.assist()")
                response_generator = agent.assist(query_text, query_id)
                logger.debug("Got response generator from agent.assist()")
                
                async for chunk in response_generator:
                    logger.debug(f"Received chunk from agent: {chunk[:50]}...")
                    if not chunk or not isinstance(chunk, str):
                        logger.debug("Skipping invalid chunk")
                        continue
                        
                    event_data = {
                        "type": "message",
                        "content": chunk
                    }
                    logger.debug(f"Sending event: {json.dumps(event_data)}")
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"Error in response generation: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                error_data = {
                    "type": "error",
                    "content": str(e)
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            finally:
                logger.debug("Sending completion event")
                completion_data = {
                    "type": "done",
                    "content": ""
                }
                yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
        
        logger.debug("Returning streaming response")
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in assist endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 