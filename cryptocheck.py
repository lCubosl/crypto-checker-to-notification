#todo
#1.try to add emojis via their unicode value 

import json
import datetime
import time
import websocket

import smtplib
from email.message import EmailMessage

trading_pairs = ['btcusdt', 'ethusdt', 'bnbusdt']
interval = '1m'
close_price = {pair: [] for pair in trading_pairs}

last_logged_date = None

#first line in Market.log (DATE "YEAR-MONTH-DAY")
with open("market.log", "w", encoding="utf-8") as f:
  f.write(datetime.datetime.now().strftime("%Y-%m-%d") + "\n")

#loads config.json
with open("config.json") as config_file:
  config = json.load(config_file)

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
      trend = "DOWN" if close < last_close else "UP"

    close_price[pair].append(close)
    log_entry = f"($){pair.upper()}: Close:{round(close, 2)}, High:{round(high, 2)}, Low:{round(low, 2)} | Trend: {trend}"

    return log_entry
  
# log to file logic
def log_to_file(log_entry):
  with open("Market.log", "a", encoding="utf-8") as f:
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

#email alert logic
def email_alert(subject, body, to): 
  user = config["EMAIL_USER"]
  password = config["EMAIL_PASS"]
  
  msg = EmailMessage()
  msg.set_content(body)
  msg['subject'] = subject
  msg['to'] = to
  msg['from'] = user

  server = smtplib.SMTP("smtp.gmail.com", 587)
  server.starttls()
  server.login(user, password)
  server.send_message(msg)
  server.quit()

#reads market.log file and calls email_alert with content of market.log
def send_market_log():
  try:
    with open("Market.log", "r", encoding="utf-8") as f:
      log_content = f.read().strip()
      print(log_content)

    if log_content:
      email_alert("Market Log Update", log_content, config["EMAIL_USER"])
      print("email sent success")
    
  except Exception as e:
    print(f"error: {e}")

def periodic_log_email():
  while True:
    time.sleep(120)
    send_market_log()

if __name__ == "__main__":
  import threading

  for pair in trading_pairs:
    ws_thread = threading.Thread(target=start_socket, args=(pair,))
    ws_thread.start()

  log_thread = threading.Thread(target=periodic_log_email, daemon=True)
  log_thread.start()