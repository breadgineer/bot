import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from unicodedata import name
import requests

app = Flask(__name__)

breadgineer = Client(config.user_credentials[0]["API"]["key"], config.user_credentials[0]["API"]["secret"])
david = Client(config.user_credentials[1]["API"]["key"], config.user_credentials[1]["API"]["secret"])

def clientCreator(data):
    if data["user"]=="breadgineer":
        client=breadgineer
    else:
        client=david
    return client

def num_of_zeros(n):
    if n<1:
        s = '{:.16f}'.format(n).split('.')[1]
        return 1 + len(s) - len(s.lstrip('0'))
    else:
        return 0

def orderSpot(client, side, quantity, ticker, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.create_order(symbol=ticker, side=side, type=order_type, quantity=quantity)
    except Exception as e:
        error="There was an error with the order - " + str(e)
        send_message(error)
        # return False ###### for debugging
    return order

def orderIsolatedMargin(client, side, quantity, ticker, order_type=ORDER_TYPE_MARKET, iso="TRUE"):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.create_margin_order(symbol=ticker, side=side, type=order_type, quantity=quantity, isIsolated=iso)
    except Exception as e:
        error="There was an error with the order - " + str(e)
        send_message(error)
        # return False ###### for debugging
    return order

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

def send_message(message):
    return requests.post(
        "https://api.mailgun.net/v3/sandboxa9a4e79977d24da59b94080d8e9ace3d.mailgun.org/messages",
        auth=("api", "d3743a5f880cb69e598d39673ec3c8bc-a09d6718-4c9c0cf4"),
        data={"from": "Breadhooks <mailgun@sandboxa9a4e79977d24da59b94080d8e9ace3d.mailgun.org>",
              "to": ["giancarlo.errigo@gmail.com"],
              "subject": "We've got a problem",
              "text": f"{message}"})



@app.route('/')
def bot():
    n=2
    return render_template('index.html',bots=n)

@app.route('/webhook_spot', methods=['POST'])
def webhook_spot():
    
    data = json.loads(request.data)

    client = clientCreator(data)
    ticker= data.get('ticker')
    side = data.get('side')

    if side == "BUY":
        quantity = buyAmount(client, 'USDT', ticker)
    elif side == "SELL":
        quantity = sellAmount(client, ticker[:-4], ticker)

    order_response = orderSpot(client, side, quantity, ticker)
    ##### for debugging
    # if order_response:
    #     return {
    #         "code": "success",
    #         "message": "order executed"
    #     }
    # else:
    #     print("order failed")

    #     return {
    #         "code": "error",
    #         "message": "order failed"
    #     }

@app.route('/webhook_isolated_margin', methods=['POST'])
def webhook_isolated_margin():
    
    data = json.loads(request.data)
    client = clientCreator(data)
    ticker = data.get('ticker')
    side = data.get('side')

    if side == "BUY":
        quantity = buyAmountIsolatedMargin(client, ticker)
    elif side == "SELL":
        quantity = sellAmountIsolatedMargin(client, ticker)
    print(quantity)
    order_response = orderIsolatedMargin(client, side, quantity, ticker)
    
    ##### for debugging
    # if order_response:
    #     return {
    #         "code": "success",
    #         "message": "order executed"
    #     }
    # else:
    #     print("order failed")

    #     return {
    #         "code": "error",
    #         "message": "order failed"
    #     }