import os
import sys
import logging
from decimal import Decimal
from dotenv import load_dotenv
from binance_sdk_derivatives_trading_usds_futures import DerivativesTradingUsdsFutures
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL

# -----------------------------
# Setup logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    logging.error("API_KEY or API_SECRET not set in .env")
    sys.exit(1)

def place_market_order(symbol, side, quantity):
    """
    Place a market order on Binance.
    
    Args:
        symbol (str): Trading pair (e.g., 'BTCUSDT')
        side (str): 'BUY' or 'SELL'
        quantity (Decimal): Amount to buy/sell
    
    Returns:
        dict: Order details if successful, None otherwise
    """
    # Validate inputs
    symbol = symbol.upper()
    side = side.upper()
    
    if side not in ["BUY", "SELL"]:
        logging.error("Side must be 'BUY' or 'SELL'")
        return None
        
    try:
        quantity = Decimal(str(quantity))
    except (ValueError, TypeError):
        logging.error("Quantity must be a valid number")
        return None

    # Initialize client
    config = ConfigurationRestAPI(
        api_key=API_KEY,
        api_secret=API_SECRET,
        base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL
    )
    client = DerivativesTradingUsdsFutures(config)
    client.testnet = True  # Enable testnet mode

    try:
        # Fetch exchange info
        exchange_resp = client.rest_api.exchange_information()
        exchange_data = exchange_resp.data()

        symbols_info = {s.symbol: s for s in exchange_data.symbols}

        if symbol not in symbols_info:
            logging.error(f"Symbol {symbol} not available for trading")
            return None

        # Extract filters for validation
        symbol_info = symbols_info[symbol]
        lot_size_filter = next((f for f in symbol_info.filters if f.filter_type == "LOT_SIZE"), None)
        min_notional_filter = next((f for f in symbol_info.filters if f.filter_type == "MIN_NOTIONAL"), None)

        if not lot_size_filter or not min_notional_filter:
            logging.error("Required trading filters not found for symbol")
            return None

        min_qty = Decimal(str(lot_size_filter.min_qty))
        max_qty = Decimal(str(lot_size_filter.max_qty))
        step_size = Decimal(str(lot_size_filter.step_size))
        min_notional = Decimal(str(min_notional_filter.notional))

        # Fetch current price
        ticker_resp = client.rest_api.symbol_price_ticker(symbol=symbol)
        price_data = ticker_resp.data().actual_instance
        current_price = Decimal(str(price_data.price))
        logging.info(f"{symbol} Current Price: {current_price}")

        # Fetch account balance
        response = client.rest_api.account_information_v2()
        account_data = response.data()
        usdt_balance = Decimal('0')

        # Find USDT balance
        for asset in account_data.assets:
            if asset.asset == "USDT":
                usdt_balance = Decimal(str(asset.wallet_balance or 0))
                break
        
        logging.info(f"USDT Futures Wallet Balance: {usdt_balance}")

        # Validations
        validations_passed = True

        if quantity < min_qty or quantity > max_qty:
            logging.error(f"Quantity {quantity} out of range [{min_qty}, {max_qty}]")
            validations_passed = False
        elif (quantity % step_size) != 0:
            logging.error(f"Quantity {quantity} not a multiple of step size {step_size}")
            validations_passed = False
        else:
            logging.info("✅ Quantity validation passed")

        notional_value = quantity * current_price
        if notional_value < min_notional:
            logging.error(f"Order notional {notional_value} < minimum notional {min_notional}")
            validations_passed = False
        else:
            logging.info("✅ Notional value validation passed")

        if notional_value > usdt_balance:
            logging.error(f"Insufficient USDT balance {usdt_balance} for order notional {notional_value}")
            validations_passed = False
        else:
            logging.info("✅ Balance validation passed")

        if not validations_passed:
            logging.error("Validation failed, order not placed")
            return None

        # Place market order
        order = client.rest_api.new_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=str(quantity)
        )
        
        if order.status_code == 200:
            order_data = order.data()
            logging.info(f"✅ Successfully placed {side} order for {quantity} {symbol}")
            logging.info(f"📝 Order ID: {order_data.get('orderId')}")
            logging.info(f"📊 Status: {order_data.get('status')}")
            logging.info(f"📈 Price: {order_data.get('price', 'N/A')}")
            logging.info(f"📦 Executed Qty: {order_data.get('executedQty', '0')}")
            return order_data
        else:
            error_data = order.data()
            logging.error(f"❌ Failed to place order")
            logging.error(f"Status code: {order.status_code}")
            logging.error(f"Error message: {error_data.get('msg', 'No error message')}")
            return None

    except Exception as e:
        logging.error(f"❌ An unexpected error occurred: {str(e)}", exc_info=True)
        return None
