from typing import Dict, Any
import aiohttp
import json
from datetime import datetime, timedelta
import os
import logging
import asyncio
from collections import deque

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GasPriceProvider:
    def __init__(self, api_key: str = None):
        """Initialize the gas price provider."""
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.price_history = deque(maxlen=100)  # Store last 100 price points
        logger.debug(f"Initialized GasPriceProvider with API key: {'present' if self.api_key else 'missing'}")
        
    async def get_current_gas_prices(self) -> Dict[str, float]:
        """Fetch current gas prices from Etherscan API."""
        try:
            url = f"{self.base_url}?module=gastracker&action=gasoracle&apikey={self.api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status {response.status}")
                    
                    data = await response.json()
                    if data.get("status") != "1":
                        raise Exception(f"API error: {data.get('message', 'Unknown error')}")
                    
                    result = data.get("result", {})
                    # Convert gasUsedRatio from comma-separated string to list of floats
                    gas_used_ratios = [float(ratio) for ratio in result.get("gasUsedRatio", "0").split(",")]
                    
                    return {
                        "safe": float(result.get("SafeGasPrice", 0)),
                        "propose": float(result.get("ProposeGasPrice", 0)),
                        "fast": float(result.get("FastGasPrice", 0)),
                        "suggested_base_fee": float(result.get("suggestBaseFee", 0)),
                        "gas_used_ratio": gas_used_ratios
                    }
        except Exception as e:
            logger.error(f"Unexpected error while fetching gas prices: {str(e)}")
            raise

    def _analyze_price_trend(self) -> Dict[str, Any]:
        """Analyze price trends from historical data."""
        if not self.price_history:
            return {"trend": "unknown", "change_percentage": 0}
            
        current = self.price_history[-1]
        if len(self.price_history) < 2:
            return {"trend": "stable", "change_percentage": 0}
            
        previous = self.price_history[-2]
        change = ((current["propose"] - previous["propose"]) / previous["propose"]) * 100
        
        if change > 5:
            trend = "increasing"
        elif change < -5:
            trend = "decreasing"
        else:
            trend = "stable"
            
        return {
            "trend": trend,
            "change_percentage": change,
            "current_price": current["propose"],
            "previous_price": previous["propose"]
        }

    async def predict_optimal_gas_price(self) -> Dict[str, Any]:
        """Predict the optimal gas price based on historical data and current network conditions."""
        current_prices = await self.get_current_gas_prices()
        self.price_history.append(current_prices)  # Add to history for trend analysis
        price_trend = self._analyze_price_trend()
        
        # Enhanced prediction algorithm
        base_fee = current_prices.get("suggested_base_fee", 0)
        gas_used_ratio = current_prices.get("gas_used_ratio", [0])[0]  # Use first value as current ratio
        
        # Calculate optimal price based on multiple factors
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

    async def get_transaction_speed_up_options(self, current_gas_price: int) -> Dict[str, Any]:
        """Get options for speeding up a transaction."""
        current_prices = await self.get_current_gas_prices()
        price_trend = self._analyze_price_trend()
        
        # Get the current gas used ratio (first value from the list)
        gas_used_ratio = current_prices.get("gas_used_ratio", [0])[0]
        
        return {
            "current_price": current_gas_price,
            "speed_up_options": [
                {
                    "price": current_prices["fast"],
                    "estimated_time": "1-2 minutes",
                    "confidence": 0.9,
                    "price_increase": ((current_prices["fast"] - current_gas_price) / current_gas_price) * 100
                },
                {
                    "price": current_prices["fast"] * 1.1,  # 10% higher than fast
                    "estimated_time": "< 1 minute",
                    "confidence": 0.95,
                    "price_increase": ((current_prices["fast"] * 1.1 - current_gas_price) / current_gas_price) * 100
                }
            ],
            "price_trend": price_trend,
            "network_metrics": {
                "gas_used_ratio": gas_used_ratio,
                "congestion_level": "high" if gas_used_ratio > 0.9 else "medium" if gas_used_ratio > 0.7 else "low"
            }
        } 