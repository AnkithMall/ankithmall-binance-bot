# src/advanced/oco.py
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

def validate_oco_order(symbol, qty, side, take_profit_price, stop_price):
    """Validate OCO order inputs and wallet balances with detailed logging."""
    logging.info(f"🔍 Starting OCO order validation for {symbol} {side} qty={qty} TP={take_profit_price} STOP={stop_price}")

    # Quantity check
    if qty <= 0:
        logging.error("❌ Validation failed: Quantity must be greater than zero.")
        return False
    logging.info(f"✅ Quantity check passed: {qty} > 0")

    # Price check
    if take_profit_price <= 0:
        logging.error("❌ Validation failed: Take-profit price must be greater than zero.")
        return False
    logging.info(f"✅ Take-profit price check passed: {take_profit_price} > 0")

    if stop_price <= 0:
        logging.error("❌ Validation failed: Stop price must be greater than zero.")
        return False
    logging.info(f"✅ Stop price check passed: {stop_price} > 0")

    # Side check
    if side.upper() not in ["BUY", "SELL"]:
        logging.error("❌ Validation failed: Side must be BUY or SELL.")
        return False
    logging.info(f"✅ Side check passed: {side.upper()}")

    # Take-profit vs stop price logic
    if side.upper() == "BUY":
        if take_profit_price <= stop_price:
            logging.error(f"❌ Validation failed: For BUY OCO, take-profit ({take_profit_price}) must be higher than stop ({stop_price}).")
            return False
        logging.info(f"✅ BUY logic check passed: TP({take_profit_price}) > STOP({stop_price})")
    else:  # SELL
        if take_profit_price >= stop_price:
            logging.error(f"❌ Validation failed: For SELL OCO, take-profit ({take_profit_price}) must be lower than stop ({stop_price}).")
            return False
        logging.info(f"✅ SELL logic check passed: TP({take_profit_price}) < STOP({stop_price})")

    # Balance check
    balance = get_usdt_balance()
    notional = qty * max(take_profit_price, stop_price)
    logging.info(f"💰 Checking USDT balance: {balance} vs required notional {notional}")
    if balance < notional:
        logging.error(f"❌ Validation failed: Insufficient USDT balance {balance} for order notional {notional}")
        return False

    logging.info("✅ All OCO validation checks passed")
    return True

def place_oco_order(symbol, side, qty, take_profit_price, stop_price):
    if not validate_oco_order(symbol, qty, side, take_profit_price, stop_price):
        logging.error("Validation failed, OCO order not placed.")
        return

    try:
        order_response = client.rest_api.new_order(
            symbol=symbol,
            side=side.upper(),
            order_type="OCO",
            quantity=str(qty),
            price=str(take_profit_price),
            stop_price=str(stop_price),
            time_in_force="GTC"
        )
        logging.info(f"✅ OCO Order placed: {order_response.data()}")
    except Exception as e:
        logging.error(f"❌ Error placing OCO order: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 6:
        logging.error("Usage: python src/advanced/oco.py SYMBOL SIDE QUANTITY TAKE_PROFIT_PRICE STOP_PRICE")
        exit(1)

    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    qty = Decimal(sys.argv[3])
    take_profit_price = Decimal(sys.argv[4])
    stop_price = Decimal(sys.argv[5])

    place_oco_order(symbol, side, qty, take_profit_price, stop_price)
