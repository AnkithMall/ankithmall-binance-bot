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
        logging.FileHandler("bot.log", encoding="utf-8"),
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


def get_asset_balance(asset):
    """Fetch wallet balance for a specific asset."""
    try:
        response = client.rest_api.account_information_v2()
        data = response.data()
        balance = next((Decimal(a.wallet_balance) for a in data.assets if a.asset == asset), Decimal("0"))
        logging.info(f"{asset} Futures Wallet Balance: {balance}")
        return balance
    except Exception as e:
        logging.error(f"Failed to fetch {asset} balance: {e}")
        return Decimal("0")


def validate_order(symbol, side, qty, stop_price, limit_price):
    """Validate order inputs and wallet balances with detailed logging."""
    logging.info("🔍 Starting order validation...")
    logging.info(f"Symbol: {symbol}, Side: {side}, Qty: {qty}, Stop Price: {stop_price}, Limit Price: {limit_price}")

    # Quantity check
    if qty <= 0:
        logging.error("❌ Validation failed: Quantity must be greater than zero.")
        return False
    logging.info("✅ Quantity check passed")

    # Price checks
    if stop_price <= 0:
        logging.error("❌ Validation failed: Stop price must be greater than zero.")
        return False
    if limit_price <= 0:
        logging.error("❌ Validation failed: Limit price must be greater than zero.")
        return False
    logging.info("✅ Stop and Limit price checks passed")

    # Determine assets
    base_asset = symbol[:-4]   # e.g., BTCUSDT -> BTC
    quote_asset = symbol[-4:]  # e.g., BTCUSDT -> USDT
    logging.info(f"Base Asset: {base_asset}, Quote Asset: {quote_asset}")

    # Balance checks
    if side.upper() == "BUY":
        balance = get_asset_balance(quote_asset)
        notional = qty * limit_price
        logging.info(f"Checking BUY order: Need {notional} {quote_asset}, Available {balance}")
        if balance < notional:
            logging.error(f"❌ Validation failed: Insufficient {quote_asset} balance {balance} for order notional {notional}")
            return False
        logging.info("✅ Balance check for BUY passed")
    else:  # SELL
        balance = get_asset_balance(base_asset)
        logging.info(f"Checking SELL order: Need {qty} {base_asset}, Available {balance}")
        if balance < qty:
            logging.error(f"❌ Validation failed: Insufficient {base_asset} balance {balance} for order quantity {qty}")
            return False
        logging.info("✅ Balance check for SELL passed")

    logging.info("🎯 All validations passed successfully")
    return True


def place_stop_limit_order(symbol, side, qty, stop_price, limit_price):
    """Place a stop-limit order."""
    if not validate_order(symbol, side, qty, stop_price, limit_price):
        logging.error("Validation failed, order not placed.")
        return

    try:
        order_response = client.rest_api.new_order(
            symbol=symbol,
            side=side.upper(),
            order_type="STOP_MARKET",  # STOP_MARKET triggers when stop price is hit
            quantity=str(qty),
            stopPrice=str(stop_price),
            price=str(limit_price),
            time_in_force="GTC"  # Good-Til-Canceled
        )
        logging.info(f"✅ Stop-Limit Order placed: {order_response.data()}")
    except Exception as e:
        logging.error(f"❌ Error placing stop-limit order: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 6:
        logging.error("Usage: python src/advanced/stop_limit.py SYMBOL SIDE QUANTITY STOP_PRICE LIMIT_PRICE")
        exit(1)

    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    qty = Decimal(sys.argv[3])
    stop_price = Decimal(sys.argv[4])
    limit_price = Decimal(sys.argv[5])

    place_stop_limit_order(symbol, side, qty, stop_price, limit_price)
