# src/advanced/grid.py
import os
import time
import logging
from decimal import Decimal
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import DerivativesTradingUsdsFutures
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    logging.error("API_KEY and API_SECRET must be set in environment variables.")
    exit(1)

config = ConfigurationRestAPI(api_key=API_KEY, api_secret=API_SECRET, base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL)
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

def validate_grid_order(symbol, lower_price, upper_price, steps, qty_per_order):
    """Validate grid order inputs and balances with detailed logging."""
    logging.info("🔍 Starting Grid order validation...")
    logging.info(f"Symbol: {symbol}, Lower Price: {lower_price}, Upper Price: {upper_price}, Steps: {steps}, Qty per Order: {qty_per_order}")

    # Basic checks
    if lower_price <= 0 or upper_price <= 0:
        logging.error("❌ Validation failed: Prices must be greater than zero.")
        return False
    logging.info("✅ Price check passed")

    if steps <= 0:
        logging.error("❌ Validation failed: Steps must be greater than zero.")
        return False
    logging.info("✅ Steps count check passed")

    if qty_per_order <= 0:
        logging.error("❌ Validation failed: Quantity per order must be greater than zero.")
        return False
    logging.info("✅ Quantity per order check passed")

    if lower_price >= upper_price:
        logging.error("❌ Validation failed: Lower price must be less than upper price.")
        return False
    logging.info("✅ Price range check passed")

    # Estimate total notional
    notional = qty_per_order * (lower_price + upper_price) / 2 * steps
    balance = get_usdt_balance()
    logging.info(f"Estimated total notional: {notional}, Available USDT balance: {balance}")

    if balance < notional:
        logging.error(f"❌ Validation failed: Insufficient USDT balance {balance} for grid total notional {notional}")
        return False
    logging.info("✅ Balance check passed")
    logging.info("🎯 All Grid order validations passed successfully")
    return True


def place_grid_order(symbol, lower_price, upper_price, steps, qty_per_order, interval_sec=5):
    if not validate_grid_order(symbol, lower_price, upper_price, steps, qty_per_order):
        logging.error("Grid order validation failed")
        return

    price_step = (upper_price - lower_price) / (steps - 1)
    logging.info(f"Placing Grid Order: {steps} levels from {lower_price} to {upper_price}, qty {qty_per_order} each")

    for i in range(steps):
        grid_price = lower_price + price_step * i
        try:
            order_response = client.rest_api.new_order(
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=str(qty_per_order),
                price=str(grid_price),
                time_in_force="GTC"
            )
            logging.info(f"✅ Grid BUY order at {grid_price}: {order_response.data()}")
        except Exception as e:
            logging.error(f"❌ Error placing grid order at {grid_price}: {e}")
        time.sleep(interval_sec)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 7:
        logging.error("Usage: python src/advanced/grid.py SYMBOL LOWER_PRICE UPPER_PRICE STEPS QTY_PER_ORDER INTERVAL_SEC")
        exit(1)

    symbol = sys.argv[1].upper()
    lower_price = Decimal(sys.argv[2])
    upper_price = Decimal(sys.argv[3])
    steps = int(sys.argv[4])
    qty_per_order = Decimal(sys.argv[5])
    interval_sec = int(sys.argv[6])

    place_grid_order(symbol, lower_price, upper_price, steps, qty_per_order, interval_sec)
