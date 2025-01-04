import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
import os
import time
from dotenv import load_dotenv

# Load environment variables from a .env file (if using environment variables)
load_dotenv()

# OANDA API Configuration - Ensure the variables are loaded securely
API_KEY = os.getenv('OANDA_API_KEY')  # Set your OANDA API Key in environment or input at runtime
ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')  # Set your OANDA Account ID in environment or input at runtime
OANDA_URL = "https://api-fxpractice.oanda.com/v3"  # Use practice account for testing
client = oandapyV20.API(access_token=API_KEY)

# Grid trading bot parameters
symbol = "EUR_USD"  # Forex trading pair
lower_price = float(input("Enter lower price for grid: "))  # User input
upper_price = float(input("Enter upper price for grid: "))  # User input
grid_levels = int(input("Enter number of grid levels: "))  # User input
capital = float(input("Enter your capital in base currency (e.g., GBP): "))  # User input
grid_size = (upper_price - lower_price) / grid_levels  # Price range for each grid level
trade_size = capital / grid_levels  # Trade size per grid (adjust for margin)

# Generate grid levels
grid_prices = [lower_price + i * grid_size for i in range(grid_levels + 1)]


# Function to get the current price
def get_current_price(instrument):
    try:
        params = {"instruments": instrument}
        response = client.request(pricing.PricingInfo(accountID=ACCOUNT_ID, params=params))
        prices = response['prices']
        for price in prices:
            if price['instrument'] == instrument:
                return float(price['bids'][0]['price'])  # Bid price (current sell price)
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None


# Function to place a trade
# New user inputs for stop-loss and take-profit distances
sl_distance = float(input("Enter stop-loss distance (in pips): "))  # Distance from entry price
tp_distance = float(input("Enter take-profit distance (in pips): "))  # Distance from entry price


# Function to calculate SL and TP prices
def calculate_sl_tp(entry_price, is_buy):
    sl_price = entry_price - (sl_distance / 10000) if is_buy else entry_price + (sl_distance / 10000)
    tp_price = entry_price + (tp_distance / 10000) if is_buy else entry_price - (tp_distance / 10000)
    return round(sl_price, 5), round(tp_price, 5)


# Updated place_trade function to include SL and TP
def place_trade(instrument, price, units, order_type):
    try:
        is_buy = units > 0
        sl_price, tp_price = calculate_sl_tp(price, is_buy)
        order = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "LIMIT",
                "price": str(price),
                "positionFill": "DEFAULT",
                "stopLossOnFill": {
                    "price": str(sl_price)
                },
                "takeProfitOnFill": {
                    "price": str(tp_price)
                }
            }
        }
        print(f"Placing {order_type.upper()} order for {units} units at price {price} "
              f"with SL: {sl_price}, TP: {tp_price}")
        client.request(orders.OrderCreate(accountID=ACCOUNT_ID, data=order))
    except Exception as e:
        print(f"Error placing trade: {e}")


# Function to place initial grid orders
def place_initial_grid_orders():
    for price in grid_prices:
        if price < (lower_price + (upper_price - lower_price) / 2):  # Below midpoint -> Buy
            units = int(trade_size / price * 1000)  # Units in forex (e.g., micro-lots)
            place_trade(symbol, price, units, "buy")
        else:  # Above midpoint -> Sell
            units = int(-trade_size / price * 1000)  # Negative for sell trades
            place_trade(symbol, price, units, "sell")


# Function to monitor and rebalance the grid
def monitor_and_rebalance():
    while True:
        try:
            current_price = get_current_price(symbol)
            if current_price is None:
                time.sleep(10)
                continue

            print(f"Current Price: {current_price}")
            for price in grid_prices:
                if abs(current_price - price) < grid_size / 10:  # Simulate trigger near the grid price
                    if current_price > price:  # Place a new sell order above
                        new_sell_price = price + grid_size
                        units = int(-trade_size / new_sell_price * 1000)
                        place_trade(symbol, new_sell_price, units, "sell")
                    elif current_price < price:  # Place a new buy order below
                        new_buy_price = price - grid_size
                        units = int(trade_size / new_buy_price * 1000)
                        place_trade(symbol, new_buy_price, units, "buy")
            time.sleep(10)
        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(10)


# Main execution
if __name__ == "__main__":
    print("Starting OANDA Grid Trading Bot...")
    place_initial_grid_orders()
    monitor_and_rebalance()
