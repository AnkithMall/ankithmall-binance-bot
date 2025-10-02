import os
import logging
from decimal import Decimal
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import DerivativesTradingUsdsFutures
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Configure logging (console + file)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Load API keys from environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    logging.error("API_KEY and API_SECRET must be set in environment variables.")
    exit(1)

# Initialize client
config = ConfigurationRestAPI(
    api_key=API_KEY,
    api_secret=API_SECRET,
    base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL
)
client = DerivativesTradingUsdsFutures(config_rest_api=config)

def get_price(symbol):
    try:
        ticker_response = client.rest_api.symbol_price_ticker(symbol=symbol)
        price = Decimal(ticker_response.data().actual_instance.price)
        logging.info(f"{symbol} Current Price: {price}")
        return price
    except Exception as e:
        logging.error(f"Failed to fetch price for {symbol}: {e}")
        return None

def get_usdt_balance():
    try:
        response = client.rest_api.account_information_v2()
        data = response.data()
        balance = next((Decimal(a.wallet_balance) for a in data.assets if a.asset == "USDT"), Decimal("0"))
        logging.info(f"USDT Futures Wallet Balance: {balance}")
        return balance
    except Exception as e:
        logging.error(f"Failed to fetch USDT balance: {e}")
        return Decimal("0")

def validate_order(symbol, qty, price):
    logging.info("🔍 Starting order validation...")
    logging.info(f"➡ Symbol: {symbol}, Side: N/A (set later), Qty: {qty}, Price: {price}")

    # Quantity check
    if qty <= 0:
        logging.error("❌ Validation failed: Quantity must be greater than zero.")
        return False
    else:
        logging.info(f"✅ Quantity check passed: {qty}")

    # Price check
    if price <= 0:
        logging.error("❌ Validation failed: Limit price must be greater than zero.")
        return False
    else:
        logging.info(f"✅ Price check passed: {price}")

    # Balance check
    balance = get_usdt_balance()
    notional = qty * price
    logging.info(f"➡ Required notional: {notional}, Available balance: {balance}")
    if balance < notional:
        logging.error(f"❌ Validation failed: Insufficient USDT balance {balance} for order notional {notional}")
        return False
    else:
        logging.info("✅ Balance check passed")

    logging.info("🎯 All validations passed successfully")
    return True

def place_limit_order(symbol, side, qty, price):
    if not validate_order(symbol, qty, price):
        logging.error("Validation failed, order not placed.")
        return

    try:
        order_response = client.rest_api.new_order(
            symbol=symbol,
            side=side.upper(),
            order_type="LIMIT",
            quantity=str(qty),
            price=str(price),
            time_in_force="GTC"  # Good-Til-Canceled
        )
        logging.info(f"✅ Limit Order placed: {order_response.data()}")
    except Exception as e:
        logging.error(f"❌ Error placing limit order: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        logging.error("Usage: python src/limit_orders.py SYMBOL SIDE QUANTITY LIMIT_PRICE")
        exit(1)

    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    qty = Decimal(sys.argv[3])
    limit_price = Decimal(sys.argv[4])

    place_limit_order(symbol, side, qty, limit_price)
