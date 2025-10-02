# Trading Bot for Binance Futures (USDT-M)

A Python-based trading bot that supports various order types for Binance Futures (USDT-M) trading. The bot provides a command-line interface for executing different trading strategies programmatically.

## Features

- **Market Orders**: Execute orders at the current market price
- **Limit Orders**: Place orders at a specific price
- **Stop-Limit Orders**: Set stop-loss and take-profit levels
- **TWAP Orders**: Time-Weighted Average Price execution
- **Grid Trading**: Automated trading within a price range

## Prerequisites

- Python 3.7+
- Binance Futures account with API keys
- Basic understanding of cryptocurrency trading

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Primetrade.ai
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your Binance API credentials:
   ```
   BINANCE_API_KEY=your_api_key_here
   BINANCE_API_SECRET=your_api_secret_here
   ```

## Usage

The bot is controlled via command-line arguments. Here are examples for each order type:

### 1. Market Order
Execute an order at the current market price.

```bash
python src/main.py MARKET BTCUSDT BUY 0.001
```

### 2. Limit Order
Place an order that will be executed when the price reaches the specified limit.

```bash
python src/main.py LIMIT BTCUSDT BUY 0.001 50000.00
```

### 3. Stop-Limit Order
Set a stop price and limit price for more control over order execution.

```bash
python src/main.py STOP_LIMIT BTCUSDT SELL 0.001 49000.00 48950.00
```

### 4. TWAP (Time-Weighted Average Price) Order
Execute a large order in smaller chunks over time to minimize market impact.

```bash
python src/main.py TWAP BTCUSDT BUY 1 10 60
```
This will buy 1 BTC in 10 equal chunks (0.1 BTC each) with 60 seconds between orders.

### 5. Grid Trading
Automatically place buy and sell orders within a price range.

```bash
python src/main.py GRID BTCUSDT 45000 55000 10 0.01 300
```
This creates a grid from $45,000 to $55,000 with 10 price levels, trading 0.01 BTC per order, and checking every 5 minutes (300 seconds).

## Testing

### Prerequisites
- Python 3.7+
- Binance Testnet API keys
- Required packages: `python-binance`, `python-dotenv`

### Running Tests

1. Install dependencies:
   ```bash
   pip install python-binance python-dotenv
   ```

2. Create a `.env` file with your testnet API keys:
   ```
   BINANCE_API_KEY=your_testnet_api_key_here
   BINANCE_API_SECRET=your_testnet_api_secret_here
   ```

3. Run the test script:
   ```bash
   python test_connection.py
   ```

### Test Results

```
1. Testing API connection...
✅ Connected to Binance Testnet API

2. Testing server connectivity...
✅ Successfully pinged Binance API

3. Checking server time...
✅ Server time: 2025-10-03 01:08:01

4. Fetching exchange info for BTCUSDT...
✅ Successfully retrieved exchange info for BTCUSDT

5. Fetching account balance...
✅ Account balance retrieved. USDT Balance: N/A

Account Balances:
--------------------------------------------------
--------------------------------------------------
✅ All tests completed successfully!
```

## Logging

All trading activities are logged to `bot.log` in the project root directory. This includes order placements, executions, and any errors that occur.

## Risk Warning

- This is a trading bot for educational purposes only.
- Cryptocurrency trading involves substantial risk of loss.
- Always test with small amounts first.
- Never share your API keys with anyone.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
