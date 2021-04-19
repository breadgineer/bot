import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from unicodedata import name
import requests
from binance.websockets import BinanceSocketManager

app = Flask(__name__)

giancarlo = Client(config.user_credentials[0]["API"]["key"], config.user_credentials[0]["API"]["secret"])
david = Client(config.user_credentials[1]["API"]["key"], config.user_credentials[1]["API"]["secret"])
price = 0

clients = [
    {
    "user_name":"Giancarlo",
    "client":giancarlo
    }
    # ,
    # {
    # "user_name":"David",
    # "client":david
    # }
] 

def num_of_zeros(n):
    if n<1:
        s = '{:.16f}'.format(n).split('.')[1]
        return 1 + len(s) - len(s.lstrip('0'))
    else:
        return 0

def orderSpot(client, side, quantity, ticker, user_name, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.create_order(symbol=ticker, side=side, type=order_type, quantity=quantity)
        return order
    except Exception as e:
        error="An error was encountered - " + str(e)
        # send_message(error, user_name)

def orderIsolatedMargin(client, side, quantity, ticker, user_name, order_type=ORDER_TYPE_MARKET, iso="TRUE"):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.create_margin_order(symbol=ticker, side=side, type=order_type, quantity=quantity, isIsolated=iso)
        return order
    except Exception as e:
        error="An error was encountered - " + str(e)
        # send_message(error,user_name)

def buyAmount(client, coin, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceBuy = float(client.get_asset_balance(coin,
    recvWindow=10000)['free'])
    close = float(client.get_symbol_ticker(symbol=ticker)['price'])
    maxBuy = round(balanceBuy / close * .995, r)
    return maxBuy
    
def sellAmount(client, coin, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceSell = float(client.get_asset_balance(coin,
    recvWindow=10000)['free'])
    maxSell = round(balanceSell * .995, r)
    return maxSell

def buyAmountIsolatedMargin(client, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceBuy = float(client.get_isolated_margin_account(symbols=ticker, 
    recvWindow=10000)['assets'][0]['quoteAsset']['free'])
    close = float(client.get_symbol_ticker(symbol=ticker)['price'])
    maxBuy = round(balanceBuy / close * .995, r)
    return maxBuy
    
def sellAmountIsolatedMargin(client,ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceSell = float(client.get_isolated_margin_account(symbols=ticker,
    recvWindow=10000)['assets'][0]['baseAsset']['free'])
    maxSell = round(balanceSell * .995, r)
    return maxSell

# def send_message(message, user_name):
#     return requests.post(
#         "https://api.mailgun.net/v3/sandboxa9a4e79977d24da59b94080d8e9ace3d.mailgun.org/messages",
#         auth=("api", "d3743a5f880cb69e598d39673ec3c8bc-a09d6718-4c9c0cf4"),
#         data={"from": "Breadhooks <mailgun@sandboxa9a4e79977d24da59b94080d8e9ace3d.mailgun.org>",
#               "to": ["giancarlo.errigo@gmail.com"],
#               "subject": "We've got a problem",
#               "text": f"The order for {user_name} could not be filled. {message}"})

def streaming_data_process(msg):
    """
    Function to process the received messages
    param msg: input message
    """
    global price
    price = msg['c']
# Starting the WebSocket

@app.route('/')
def bot():
    return render_template('index.html', eth=price)

@app.route('/webhook_spot', methods=['POST'])
def webhook_spot():
    
    data = json.loads(request.data)
 
    ticker= data.get('ticker')
    side = data.get('side')

    for user_data in clients:
        user_name = user_data["user_name"]
        client = user_data["client"]
        try:
            if side == "BUY":
                quantity = buyAmount(client, 'USDT', ticker)
            elif side == "SELL":
                quantity = sellAmount(client, ticker[:-4], ticker)
            orderSpot(client, side, quantity, ticker, user_name)
        except:
            continue

@app.route('/webhook_isolated_margin', methods=['POST'])
def webhook_isolated_margin():
    
    data = json.loads(request.data)
    
    ticker = data.get('ticker')
    side = data.get('side')

    for user_data in clients:
        user_name = user_data["user_name"]
        client = user_data["client"]
        try:
            if side == "BUY":
                quantity = buyAmountIsolatedMargin(client, ticker)
            elif side == "SELL":
                quantity = sellAmountIsolatedMargin(client, ticker)
            order_response=orderIsolatedMargin(client, side, quantity, ticker, user_name)
        except:
            continue
