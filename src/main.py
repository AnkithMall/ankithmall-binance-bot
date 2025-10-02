# src/main.py
import sys
import logging
from decimal import Decimal

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.market_orders import place_market_order
from src.limit_orders import place_limit_order
from src.advanced.stop_limit import place_stop_limit_order
from src.advanced.twap import place_twap_order
from src.advanced.grid import place_grid_order
from src.advanced.oco import place_oco_order  # Import OCO functions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

def print_usage():
    logging.info("""
Usage:
python src/main.py ORDER_TYPE [PARAMETERS]

Order Types & Example Usage:
1. Market Order:
   python src/main.py MARKET SYMBOL SIDE QUANTITY
2. Limit Order:
   python src/main.py LIMIT SYMBOL SIDE QUANTITY LIMIT_PRICE
3. Stop-Limit Order:
   python src/main.py STOP_LIMIT SYMBOL SIDE QUANTITY STOP_PRICE LIMIT_PRICE
4. TWAP Order:
   python src/main.py TWAP SYMBOL SIDE TOTAL_QTY CHUNKS INTERVAL_SEC
5. Grid Order:
   python src/main.py GRID SYMBOL LOWER_PRICE UPPER_PRICE STEPS QTY_PER_ORDER INTERVAL_SEC
""")

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    order_type = sys.argv[1].upper()

    try:
        if order_type == "MARKET":
            if len(sys.argv) != 5:
                print_usage()
                sys.exit(1)
            symbol = sys.argv[2].upper()
            side = sys.argv[3].upper()
            qty = Decimal(sys.argv[4])
            place_market_order(symbol, side, qty)

        elif order_type == "LIMIT":
            if len(sys.argv) != 6:
                print_usage()
                sys.exit(1)
            symbol = sys.argv[2].upper()
            side = sys.argv[3].upper()
            qty = Decimal(sys.argv[4])
            limit_price = Decimal(sys.argv[5])
            place_limit_order(symbol, side, qty, limit_price)

        elif order_type == "STOP_LIMIT":
            if len(sys.argv) != 7:
                print_usage()
                sys.exit(1)
            symbol = sys.argv[2].upper()
            side = sys.argv[3].upper()
            qty = Decimal(sys.argv[4])
            stop_price = Decimal(sys.argv[5])
            limit_price = Decimal(sys.argv[6])
            place_stop_limit_order(symbol, side, qty, stop_price, limit_price)
        
        elif order_type == "OCO":
            if len(sys.argv) != 7:
                print_usage()
                sys.exit(1)
            symbol = sys.argv[2].upper()
            side = sys.argv[3].upper()
            qty = Decimal(sys.argv[4])
            take_profit_price = Decimal(sys.argv[5])
            stop_price = Decimal(sys.argv[6])
            
            place_oco_order(symbol, side, qty, take_profit_price, stop_price)

        elif order_type == "TWAP":
            if len(sys.argv) != 7:
                print_usage()
                sys.exit(1)
            symbol = sys.argv[2].upper()
            side = sys.argv[3].upper()
            total_qty = Decimal(sys.argv[4])
            chunks = int(sys.argv[5])
            interval_sec = int(sys.argv[6])
            place_twap_order(symbol, side, total_qty, chunks, interval_sec)

        elif order_type == "GRID":
            if len(sys.argv) != 8:
                print_usage()
                sys.exit(1)
            symbol = sys.argv[2].upper()
            lower_price = Decimal(sys.argv[3])
            upper_price = Decimal(sys.argv[4])
            steps = int(sys.argv[5])
            qty_per_order = Decimal(sys.argv[6])
            interval_sec = int(sys.argv[7])
            place_grid_order(symbol, lower_price, upper_price, steps, qty_per_order, interval_sec)

        else:
            logging.error(f"Unknown order type: {order_type}")
            print_usage()
            sys.exit(1)

    except Exception as e:
        logging.exception(f"❌ Error executing {order_type} order: {e}")

if __name__ == "__main__":
    main()
