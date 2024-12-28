import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.types import StopLossDetails, TakeProfitDetails
from oandapyV20.types import OrderPositionFill
import time

# OANDA API Configuration
API_KEY = "YOUR_OANDA_API_KEY"
ACCOUNT_ID = "YOUR_ACCOUNT_ID"
OANDA_URL = "https://api-fxpractice.oanda.com/v3"  # Practice account URL
client = oandapyV20.API(access_token=API_KEY)

# Grid trading bot parameters
symbol = "EUR_USD"  # Forex trading pair
lower_price = 1.05  # Lower limit of the grid
upper_price = 1.15  # Upper limit of the grid
grid_levels = 10  # Number of grid levels
capital = 1000  # Total capital (in base currency, e.g., USD)
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
def place_trade(instrument, price, units, order_type):
    try:
        order = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "LIMIT",
                "price": str(price),
                "positionFill": "DEFAULT"
            }
        }
        print(f"Placing {order_type.upper()} order for {units} units at price {price}")
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
