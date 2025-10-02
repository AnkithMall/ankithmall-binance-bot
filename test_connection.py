#!/usr/bin/env python3
"""
Binance Futures API Connection Tester

This script tests the connection to Binance Futures Testnet API and validates
configuration and credentials. It performs the following checks:
1. Environment variable loading
2. API key validation
3. Server connectivity
4. Symbol information retrieval
5. Account balance (if available)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *

# -----------------------------
# Constants
# -----------------------------
TEST_SYMBOL = "BTCUSDT"
LOG_FILE = "test_connection.log"

# -----------------------------
# Setup logging
# -----------------------------
def setup_logging():
    """Configure logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode='a'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# -----------------------------
# Test Functions
# -----------------------------
class BinanceTester:
    """Class to handle Binance API testing."""
    
    def __init__(self, api_key, api_secret):
        """Initialize with API credentials."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        self.connected = False
        
    def connect(self):
        """Establish connection to Binance Testnet."""
        try:
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=True,  # Use testnet
                tld='com'  # or 'us' for US users
            )
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False
    
    def test_connection(self):
        """Test basic API connectivity."""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_server_time(self):
        """Get server time to verify connectivity."""
        try:
            server_time = self.client.get_server_time()
            server_time_dt = datetime.fromtimestamp(server_time['serverTime'] / 1000)
            return server_time_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Failed to get server time: {str(e)}")
            return None
    
    def get_exchange_info(self, symbol):
        """Get exchange information for a symbol."""
        try:
            return self.client.get_symbol_info(symbol)
        except Exception as e:
            logger.error(f"Failed to get exchange info: {str(e)}")
            return None
    
    def get_account_balance(self):
        """Get account balance information."""
        try:
            account = self.client.futures_account_balance()
            return {
                'assets': [
                    {'asset': item['asset'], 'wallet_balance': item['balance']}
                    for item in account if float(item['balance']) > 0
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            return None

def run_tests():
    """Run all connection tests."""
    # Load environment
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("API keys not found in .env file")
        print("❌ Error: Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
        print("You can get testnet API keys from: https://testnet.binance.vision/")
        return False
    
    logger.info("Starting Binance Testnet Connection Tests")
    logger.info("-" * 50)
    
    try:
        # Initialize tester
        tester = BinanceTester(api_key, api_secret)
        
        # Test 1: Basic connection
        print("\n1. Testing API connection...")
        if not tester.connect():
            logger.error("Failed to initialize API client")
            print("❌ Failed to connect to Binance API")
            return False
        print("✅ Connected to Binance Testnet API")
        
        # Test 2: Server ping
        print("\n2. Testing server connectivity...")
        if not tester.test_connection():
            logger.error("Connection test failed")
            print("❌ Failed to ping Binance API")
            return False
        print("✅ Successfully pinged Binance API")
        
        # Test 3: Server time
        print("\n3. Checking server time...")
        server_time = tester.get_server_time()
        if not server_time:
            logger.error("Failed to get server time")
            print("❌ Failed to get server time")
            return False
        print(f"✅ Server time: {server_time}")
        
        # Test 4: Exchange info
        print(f"\n4. Fetching exchange info for {TEST_SYMBOL}...")
        exchange_info = tester.get_exchange_info(TEST_SYMBOL)
        if not exchange_info:
            logger.error(f"Failed to get exchange info for {TEST_SYMBOL}")
            print(f"❌ Failed to get exchange info for {TEST_SYMBOL}")
            return False
        print(f"✅ Successfully retrieved exchange info for {TEST_SYMBOL}")
        
        # Test 5: Account balance
        print("\n5. Fetching account balance...")
        account_info = tester.get_account_balance()
        if not account_info:
            logger.warning("Failed to get account balance")
            print("⚠️  Failed to get account balance (check API key permissions)")
        else:
            usdt_balance = next(
                (a['wallet_balance'] for a in account_info['assets'] if a['asset'] == 'USDT'),
                'N/A'
            )
            print(f"✅ Account balance retrieved. USDT Balance: {usdt_balance}")
            
            # Print all non-zero balances
            print("\nAccount Balances:")
            print("-" * 50)
            for asset in account_info['assets']:
                balance = float(asset['wallet_balance'])
                if balance > 0:
                    print(f"{asset['asset']}: {balance:.8f}")
        
        print("\n" + "-" * 50)
        print("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        print(f"\n❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Binance Futures API connection')
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='Trading pair to test (default: BTCUSDT)')
    args = parser.parse_args()
    
    # Update test symbol if provided
    TEST_SYMBOL = args.symbol.upper()
    
    # Run tests
    success = run_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
