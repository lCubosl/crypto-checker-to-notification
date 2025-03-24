#todo
#1. fix market.log trend not working properly after being initialized with market_temp.log values

import json
import datetime
import time
import websocket
import sys

import smtplib
from email.message import EmailMessage

sys.stdout.reconfigure(encoding="utf-8")

trading_pairs = ['btcusdt', 'ethusdt', 'bnbusdt']
interval = '1m'
close_price = {pair: [] for pair in trading_pairs}
temp_logs = {pair: [] for pair in trading_pairs}

last_logged_date = None

#first line in Market.log (DATE "YEAR-MONTH-DAY")
with open("Market.log", "w", encoding="utf-8") as f:
  f.write(datetime.datetime.now().strftime("%Y-%m-%d") + "\n")
  try:
    with open("Market_temp.log", "r", encoding="utf-8") as temp_f:
      temp_data = temp_f.read().strip()
      if temp_data:
        f.write(temp_data + "\n")

  except FileNotFoundError:
    print("not found, skip")
  
  except Exception as e:
    print(f"Market_temp.log: {e}")    

#loads config.json
with open("config.json") as config_file:
  config = json.load(config_file)

#reads candles and writes VALUE$, HIGH, LOW and TREND. needs to be called by other functions
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
      trend = "🔴" if close < last_close else "🟢"

    close_price[pair].append(close)
    log_entry = f"{pair.upper()}: {round(close, 2)}$ | H:{round(high, 2)}, L:{round(low, 2)} | Trend: {trend}"
    
    return log_entry
  
# log to file logic
def log_to_file(log_entry, pair):
  global temp_logs

  with open("Market.log", "a", encoding="utf-8") as f:
    f.write(log_entry + "\n")

  temp_logs[pair] = log_entry

  with open("Market_temp.log", "w", encoding="utf-8") as f:
    for entry in temp_logs.values():
      if entry:
        f.write(entry + "\n")

def on_message(ws, message):
  json_message = json.loads(message)
  candle = json_message['k']

  log_entry = process_candle(ws, candle)    
  if log_entry:
    #print(log_entry)
    log_to_file(log_entry, ws.symbol) 

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
    print(f"error MAIL NOT SENT: {e}")

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