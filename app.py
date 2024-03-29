import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from unicodedata import name
import requests
from binance.streams import BinanceSocketManager
from functools import wraps
import time

app = Flask(__name__)

giancarlo = Client(config.user_credentials[0]["API"]["key"], config.user_credentials[0]["API"]["secret"])
price = 0


def delay(sleep_time:int):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            time.sleep(sleep_time)
            print(f"Sleeping {sleep_time} seconds")
            return function(*args, **kwargs)
        return wrapper
    return decorator

def num_of_zeros(n):
    if n<1:
        s = '{:.16f}'.format(n).split('.')[1]
        return 1 + len(s) - len(s.lstrip('0'))
    else:
        return 0

# def orderSpot(client, side, quantity, ticker, user_name, order_type=ORDER_TYPE_MARKET):
#     try:
#         print(f"sending order {order_type} - {side} {quantity} {ticker} " )
#         order = client.create_order(symbol=ticker, side=side, type=order_type, quantity=quantity)
#         return order
#     except Exception as e:
#         error="An error was encountered - " + str(e)
#         # send_message(error, user_name)

def orderFutures(client, side, quantity, ticker, order_type=ORDER_TYPE_MARKET, iso="TRUE"):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.futures_create_order(symbol=ticker, side=side, type=order_type, quantity=quantity)
        return order
    except Exception as e:
        error="An error was encountered - " + str(e)
        # send_message(error,user_name)

def cancelOrderFutures(client, ticker):
    # try:
    print(f"cancelling {ticker} order" )
    order = client.futures_cancel_all_open_orders(symbol=ticker)
    return order
    # except Exception as e:
    #     error="An error was encountered - " + str(e)
    #     # send_message(error,user_name)

# def buyAmount(client, coin, ticker):
#     step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
#     r = num_of_zeros(step)
#     balanceBuy = float(client.get_asset_balance(coin,
#     recvWindow=10000)['free'])
#     close = float(client.get_symbol_ticker(symbol=ticker)['price'])
#     maxBuy = round(balanceBuy / close * .995, r)
#     return maxBuy
    
# def sellAmount(client, coin, ticker):
#     step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
#     r = num_of_zeros(step)
#     balanceSell = float(client.get_asset_balance(coin,
#     recvWindow=10000)['free'])
#     maxSell = round(balanceSell * .995, r)
#     return maxSell

def buyAmountFutures(client, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceBuy = float(client.futures_account_balance(recvWindow=10000)[0]['availableBalance'])
    close = float(client.get_symbol_ticker(symbol=ticker)['price'])
    maxBuy = round(balanceBuy / close * .995, r)
    return maxBuy
    
def sellAmountFutures(client,ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceSell = float(client.futures_account_balance(recvWindow=10000)[0]['availableBalance'])
    maxSell = round(balanceSell * .995, r)
    return maxSell

def send_message(message, user_name):
    return requests.post(
        "https://api.mailgun.net/v3/sandboxa9a4e79977d24da59b94080d8e9ace3d.mailgun.org/messages",
        auth=("api", "d3743a5f880cb69e598d39673ec3c8bc-a09d6718-4c9c0cf4"),
        data={"from": "Breadhooks <mailgun@sandboxa9a4e79977d24da59b94080d8e9ace3d.mailgun.org>",
              "to": ["giancarlo.errigo@gmail.com"],
              "subject": "We've got a problem",
              "text": f"The order for {user_name} could not be filled. {message}"})


@app.route('/DLkmvcox') #Laura

def indexL():
    return render_template('/sites/DLkmvcox.htm')


@app.route('/FPbbldoe') #Gianca

def indexG():
    return render_template('/sites/FPbbldoe.htm')


@app.route('/')
def bot():
    return render_template('index.html')

# @app.route('/webhook_spot', methods=['POST'])
# def webhook_spot():

#     data = json.loads(request.data)

#     ticker= data.get('ticker')
#     side = data.get('side')

#     for user_data in clients:
#         user_name = user_data["user_name"]
#         client = user_data["client"]
#         try:
#             if side == "BUY":
#                 quantity = buyAmount(client, 'USDT', ticker)
#             elif side == "SELL":
#                 quantity = sellAmount(client, ticker[:-4], ticker)
#             orderSpot(client, side, quantity, ticker, user_name)
#         except:
#             continue

@delay(5)
@app.route('/futures_entry', methods=['POST'])
def futures_entry():

    data = json.loads(request.data)

    ticker = data.get('ticker')
    side = data.get('side')
    client = giancarlo

    # if side == "BUY":
    #     quantity = buyAmountFutures(client, ticker)
    # elif side == "SELL":
    #     quantity = sellAmountFutures(client, ticker)
    order_response = orderFutures(client, side, 10, ticker)
    
    return order_response

@app.route('/futures_exit', methods=['POST'])
def futures_exit():

    data = json.loads(request.data)

    ticker = data.get('ticker')
    client = giancarlo

    order_response = cancelOrderFutures(client, ticker)
    
    return order_response

# what you neeed to do is add a decorator that delays time
# then you should have two endpoints. 1 for the Entering trades and another for exiting
# Emtering always has a delay, exiting is immediate