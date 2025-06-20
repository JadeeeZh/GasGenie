import asyncio
import os
import logging
from dotenv import load_dotenv
from src.gas_genie.providers.gas_price_provider import GasPriceProvider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.debug("Environment variables loaded")

async def test_gas_price_provider():
    try:
        # Initialize the provider with explicit API key
        api_key = os.getenv("ETHERSCAN_API_KEY")
        if not api_key:
            logger.error("ETHERSCAN_API_KEY not found in environment variables")
            raise Exception("ETHERSCAN_API_KEY not found in environment variables")
        
        logger.debug("Initializing GasPriceProvider...")    
        provider = GasPriceProvider(api_key=api_key)
        
        # Test 1: Current gas prices
        print("\n=== Test 1: Current Gas Prices ===")
        logger.info("Fetching current gas prices...")
        current_prices = await provider.get_current_gas_prices()
        logger.debug(f"Received current prices: {current_prices}")
        
        print("Current Gas Prices:")
        print(f"Safe: {current_prices['safe']:.2f} Gwei")
        print(f"Propose: {current_prices['propose']:.2f} Gwei")
        print(f"Fast: {current_prices['fast']:.2f} Gwei")
        print(f"Suggested Base Fee: {current_prices['suggested_base_fee']:.2f} Gwei")
        print(f"Gas Used Ratio: {current_prices['gas_used_ratio']}")
        
        # Test 2: Price trend analysis
        print("\n=== Test 2: Price Trend Analysis ===")
        logger.info("Analyzing price trends...")
        # Add a few data points to test trend analysis
        for _ in range(2):
            prices = await provider.get_current_gas_prices()
            provider.price_history.append(prices)
            await asyncio.sleep(1)  # Wait a bit between fetches
            
        trend_analysis = provider._analyze_price_trend()
        print("Price Trend Analysis:")
        print(f"Trend: {trend_analysis['trend']}")
        print(f"Change Percentage: {trend_analysis['change_percentage']:.2f}%")
        print(f"Current Price: {trend_analysis['current_price']:.2f} Gwei")
        print(f"Previous Price: {trend_analysis['previous_price']:.2f} Gwei")
        
        # Test 3: Optimal price prediction
        print("\n=== Test 3: Optimal Price Prediction ===")
        logger.info("Predicting optimal gas price...")
        optimal_price = await provider.predict_optimal_gas_price()
        logger.debug(f"Received optimal price prediction: {optimal_price}")
        
        print("Optimal Price Prediction:")
        print(f"Recommended Price: {optimal_price['recommended_price']:.2f} Gwei")
        print(f"Confidence: {optimal_price['confidence']:.2f}")
        print(f"Suggestion: {optimal_price['suggestion']}")
        print(f"Network Congestion: {optimal_price['network_metrics']['congestion_level']}")
        print(f"Current Gas Used Ratio: {optimal_price['network_metrics']['gas_used_ratio']:.2f}")
        
        # Test 4: Transaction speed-up options
        print("\n=== Test 4: Transaction Speed-up Options ===")
        logger.info("Getting transaction speed-up options...")
        current_gas_price = current_prices['propose']  # Use propose price as current price
        speed_up_options = await provider.get_transaction_speed_up_options(current_gas_price)
        
        print("Transaction Speed-up Options:")
        print(f"Current Price: {speed_up_options['current_price']:.2f} Gwei")
        for i, option in enumerate(speed_up_options['speed_up_options'], 1):
            print(f"\nOption {i}:")
            print(f"  Price: {option['price']:.2f} Gwei")
            print(f"  Estimated Time: {option['estimated_time']}")
            print(f"  Confidence: {option['confidence']:.2f}")
            print(f"  Price Increase: {option['price_increase']:.2f}%")
        
        print(f"\nNetwork Congestion: {speed_up_options['network_metrics']['congestion_level']}")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_gas_price_provider()) 