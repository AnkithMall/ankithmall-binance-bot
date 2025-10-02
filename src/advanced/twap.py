# src/advanced/twap.py
import os
import time
import logging
from decimal import Decimal
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_TESTNET_URL
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import DerivativesTradingUsdsFutures
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)

# Load API keys from environment
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    logging.error("API_KEY and API_SECRET must be set in environment variables.")
    exit(1)

# Initialize client
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

def validate_twap_order(symbol, side, total_qty, chunks):
    """Validate TWAP order inputs and wallet balances with detailed logging."""
    logging.info("🔍 Starting TWAP order validation...")
    logging.info(f"Symbol: {symbol}, Side: {side}, Total Qty: {total_qty}, Chunks: {chunks}")

    # Basic checks
    if total_qty <= 0:
        logging.error("❌ Validation failed: Total quantity must be greater than zero.")
        return False
    logging.info("✅ Total quantity check passed")

    if chunks <= 0:
        logging.error("❌ Validation failed: Number of chunks must be greater than zero.")
        return False
    logging.info("✅ Chunks count check passed")

    # Fetch price
    price = get_price(symbol)
    if price is None or price <= 0:
        logging.error("❌ Validation failed: Could not fetch valid current price.")
        return False
    logging.info(f"✅ Current price check passed: {price}")

    # Determine assets
    base_asset = symbol[:-4]   # e.g., BTCUSDT -> BTC
    quote_asset = symbol[-4:]  # e.g., BTCUSDT -> USDT
    logging.info(f"Base Asset: {base_asset}, Quote Asset: {quote_asset}")

    # Check balance for BUY/SELL
    if side.upper() == "BUY":
        balance = get_usdt_balance()
        notional = total_qty * price
        logging.info(f"Checking BUY: Required {notional} {quote_asset}, Available {balance}")
        if balance < notional:
            logging.error(f"❌ Validation failed: Insufficient {quote_asset} balance for TWAP order notional {notional}")
            return False
        logging.info("✅ Balance check for BUY passed")
    else:  # SELL
        balance = get_asset_balance(base_asset)
        loggin

def place_twap_order(symbol, side, total_qty, chunks, interval_sec=10):
    if not validate_twap_order(symbol, side, total_qty, chunks):
        logging.error("TWAP order validation failed")
        return

    qty_per_chunk = total_qty / chunks
    logging.info(f"Placing TWAP order: {chunks} chunks, {qty_per_chunk} qty per chunk, interval {interval_sec}s")

    for i in range(chunks):
        try:
            current_price = get_price(symbol)
            order_response = client.rest_api.new_order(
                symbol=symbol,
                side=side.upper(),
                order_type="MARKET",
                quantity=str(qty_per_chunk)
            )
            logging.info(f"✅ Chunk {i+1}/{chunks} placed at price {current_price}: {order_response.data()}")
        except Exception as e:
            logging.error(f"❌ Error placing chunk {i+1}: {e}")
        time.sleep(interval_sec)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 6:
        logging.error("Usage: python src/advanced/twap.py SYMBOL SIDE TOTAL_QTY CHUNKS INTERVAL_SEC")
        exit(1)

    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    total_qty = Decimal(sys.argv[3])
    chunks = int(sys.argv[4])
    interval_sec = int(sys.argv[5])

    place_twap_order(symbol, side, total_qty, chunks, interval_sec)
