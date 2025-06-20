import logging
import os
from dotenv import load_dotenv
from typing import AsyncIterator, Dict, Any
from .providers.gas_price_provider import GasPriceProvider
from .providers.model_provider import ModelProvider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.debug("Environment variables loaded")

class GasGenie:
    def __init__(self, name: str):
        """Initialize the Gas Genie agent."""
        self.name = name
        
        # Initialize model provider
        model_api_key = os.getenv("FIREWORKS_API_KEY")
        if not model_api_key:
            raise ValueError("FIREWORKS_API_KEY is not set")
        self.model_provider = ModelProvider(api_key=model_api_key)
        
        # Initialize gas price provider
        etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
        if not etherscan_api_key:
            raise ValueError("ETHERSCAN_API_KEY is not set")
        self.gas_provider = GasPriceProvider(api_key=etherscan_api_key)

    async def get_gas_data(self) -> Dict[str, Any]:
        """Get gas price data."""
        try:
            # Get current prices first
            current_prices = await self.gas_provider.get_current_gas_prices()
            if not current_prices:
                raise ValueError("Failed to get current gas prices")
            
            # Add to price history for trend analysis
            self.gas_provider.price_history.append(current_prices)
            
            # Get price trend
            price_trend = self.gas_provider._analyze_price_trend()
            
            # Get network metrics
            gas_used_ratio = current_prices.get("gas_used_ratio", [0])[0]
            base_fee = current_prices.get("suggested_base_fee", 0)
            
            # Calculate optimal price
            optimal_price = current_prices["propose"]
            confidence = 0.8
            
            # Adjust based on network congestion
            if gas_used_ratio > 0.9:  # High congestion
                optimal_price = current_prices["fast"]
                confidence = 0.9
            elif gas_used_ratio < 0.5:  # Low congestion
                optimal_price = current_prices["safe"]
                confidence = 0.7
                
            # Adjust based on price trend
            if price_trend["trend"] == "increasing":
                optimal_price = min(optimal_price * 1.1, current_prices["fast"])
                confidence *= 0.9
            elif price_trend["trend"] == "decreasing":
                optimal_price = max(optimal_price * 0.9, current_prices["safe"])
                confidence *= 0.9
                
            # Determine suggestion
            if optimal_price > current_prices["fast"] * 1.1:
                suggestion = "wait"
            elif optimal_price < current_prices["propose"] * 0.9:
                suggestion = "send"
            else:
                suggestion = "monitor"
            
            # Return a single dictionary, not a generator
            return {
                "recommended_price": optimal_price,
                "confidence": confidence,
                "suggestion": suggestion,
                "current_prices": current_prices,
                "price_trend": price_trend,
                "network_metrics": {
                    "base_fee": base_fee,
                    "gas_used_ratio": gas_used_ratio,
                    "congestion_level": "high" if gas_used_ratio > 0.9 else "medium" if gas_used_ratio > 0.7 else "low"
                }
            }
        except Exception as e:
            logger.error(f"Error getting gas data: {str(e)}", exc_info=True)
            raise

    async def assist(self, query: str, query_id: str) -> AsyncIterator[str]:
        """Process gas-related queries and provide recommendations."""
        try:
            # Check if the query is about gas prices
            gas_keywords = ["gas", "price", "fee", "transaction", "send", "wait", "network", "congestion"]
            is_gas_query = any(keyword in query.lower() for keyword in gas_keywords)
            
            if is_gas_query:
                # Get gas data only if the query is about gas prices
                gas_data = await self.get_gas_data()
                
                if not gas_data:
                    yield "Error: Failed to get gas price data"
                    return
                
                current_prices = gas_data.get('current_prices', {})
                if not current_prices:
                    yield "Error: No current gas prices available"
                    return
                
                price_trend = gas_data.get('price_trend', {})
                network_metrics = gas_data.get('network_metrics', {})
                
                # Build comprehensive prompt for gas-related queries
                prompt = f"""Current gas prices and network conditions:
- Safe: {current_prices.get('safe', 'N/A')} Gwei
- Propose: {current_prices.get('propose', 'N/A')} Gwei
- Fast: {current_prices.get('fast', 'N/A')} Gwei
- Base Fee: {current_prices.get('suggested_base_fee', 'N/A')} Gwei

Network Status:
- Base Fee: {network_metrics.get('base_fee', 'N/A')} Gwei
- Gas Used Ratio: {network_metrics.get('gas_used_ratio', 'N/A')}
- Congestion Level: {network_metrics.get('congestion_level', 'N/A')}

Price Trend:
- Trend: {price_trend.get('trend', 'unknown')}
- Change: {price_trend.get('change_percentage', 0):.2f}%
- Current Price: {price_trend.get('current_price', 'N/A')} Gwei
- Previous Price: {price_trend.get('previous_price', 'N/A')} Gwei

Recommendation:
- Suggested Action: {gas_data.get('suggestion', 'monitor')}
- Recommended Price: {gas_data.get('recommended_price', 'N/A')} Gwei
- Confidence: {gas_data.get('confidence', 0) * 100:.1f}%

User query: {query}

Please provide a detailed analysis and recommendation based on the above data. Consider:
1. Current network conditions and their impact
2. Price trends and their implications
3. Specific recommendations for the user's query
4. Alternative options if applicable
5. Any risks or considerations to be aware of"""
            else:
                # For non-gas queries, use a simpler prompt
                prompt = f"""User query: {query}

Please provide a helpful and friendly response. Keep it concise and natural."""
            
            # Get the generator from query_stream
            response_generator = self.model_provider.query_stream(prompt)
            
            # Stream the model response
            async for chunk in response_generator:
                if chunk and isinstance(chunk, str):
                    yield chunk
                
        except Exception as e:
            logger.error(f"Error in assist: {str(e)}", exc_info=True)
            yield f"Error: {str(e)}"

    async def query(self, query: str) -> str:
        """Query the model with a single prompt and return the complete response."""
        try:
            gas_data = await self.get_gas_data()
            if not gas_data:
                return "Error: Failed to get gas price data"
            
            current_prices = gas_data.get('current_prices', {})
            if not current_prices:
                return "Error: No current gas prices available"
            
            prompt = f"""Current gas prices:
- Safe: {current_prices.get('safe', 'N/A')} Gwei
- Propose: {current_prices.get('propose', 'N/A')} Gwei
- Fast: {current_prices.get('fast', 'N/A')} Gwei
- Base Fee: {current_prices.get('suggested_base_fee', 'N/A')} Gwei

User query: {query}"""
            
            response = ""
            async for chunk in self.model_provider.query_stream(prompt):
                if chunk and isinstance(chunk, str):
                    response += chunk
            return response
            
        except Exception as e:
            logger.error(f"Error in query: {str(e)}", exc_info=True)
            return f"Error: {str(e)}" 