import json
import datetime
import websocket

trading_pairs = ['btcusdt', 'ethusdt', 'bnbusdt']
interval = '1m'
close_price = {pair: [] for pair in trading_pairs}

last_logged_date = None

with open("market.log", "w") as f:
  f.write(datetime.datetime.now().strftime("%Y-%m-%d") + "\n")

def process_candle(ws, candle):
  is_candle_closed = candle['x']
  close = float(candle['c'])
  high = float(candle['h'])
  low = float(candle['l'])

  pair = ws.symbol

  if is_candle_closed:
    trend = ''

    if close_price[pair]:
      last_close = close_price[pair][-1]
      trend = "LOWER" if close < last_close else "HIGHER"

    close_price[pair].append(close)
    log_entry = f"CURRENCY: {pair.upper()}, Close($):{round(close, 2)} High($):{round(high, 2)} Low($):{round(low, 2)} Trend: {trend}"

    #print(log_entry, flush=True)
    return log_entry
  

# log to file logic
def log_to_file(log_entry):
  with open("Market.log", "a") as f:
    f.write(log_entry + "\n")

def on_message(ws, message):
  json_message = json.loads(message)
  candle = json_message['k']

  log_entry = process_candle(ws, candle)    
  if log_entry:
    print(log_entry)
    log_to_file(log_entry)
  

def on_close(ws):
  print(f"### closed ###")

def on_error(ws, error):
  print(f"### error ### {error}")

def start_socket(pair):
  socket_url = f"wss://stream.binance.com:9443/ws/{pair}@kline_{interval}"
  ws = websocket.WebSocketApp(socket_url, 
                              on_message=on_message, 
                              on_close=on_close,
                              on_error=on_error)
  ws.symbol = pair
  ws.run_forever()

if __name__ == "__main__":
  import threading
  for pair in trading_pairs:
    ws_thread = threading.Thread(target=start_socket, args=(pair,))
    ws_thread.start()