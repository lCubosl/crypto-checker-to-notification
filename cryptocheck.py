import json
import websocket

trading_pairs = ['btcusdt', 'ethusdt', 'bnbusdt']
interval = '1m'

def on_message(ws, message):
  json_message = json.loads(message)
  candle = json_message['k']
  
  is_candle_closed = candle['x']
  close = float(candle['c'])
  high = float(candle['h'])
  low = float(candle['l'])
  # vol = candle['v']

  if is_candle_closed:
    print(f"CURRENCY: {ws.symbol.upper()}, Close:{round(close, 2)} High:{round(high, 2)} Low:{round(low, 2)}")

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