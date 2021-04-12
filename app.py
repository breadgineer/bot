import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET)

def num_of_zeros(n):
    if n<1:
        s = '{:.16f}'.format(n).split('.')[1]
        return 1 + len(s) - len(s.lstrip('0'))
    else:
        return 0

def orderSpot(side, quantity, ticker, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.create_order(symbol=ticker, side=side, type=order_type, quantity=quantity)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return order

def buyAmount(coin, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceBuy = float(client.get_asset_balance(coin,
    recvWindow=10000)['free'])
    close = float(client.get_symbol_ticker(symbol=ticker)['price'])
    maxBuy = round(balanceBuy / close * .995, r)
    return maxBuy
    
def sellAmount(coin, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceSell = float(client.get_asset_balance(coin,
    recvWindow=10000)['free'])
    maxSell = round(balanceSell * .995, r)
    return maxSell

def orderIsolatedMargin(side, quantity, ticker, order_type=ORDER_TYPE_MARKET, iso="TRUE"):
    try:
        print(f"sending order {order_type} - {side} {quantity} {ticker} " )
        order = client.create_margin_order(symbol=ticker, side=side, type=order_type, quantity=quantity, isIsolated=iso)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return order

def buyAmountIsolatedMargin(ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceBuy = float(client.get_isolated_margin_account(symbols=ticker, 
    recvWindow=10000)['assets'][0]['quoteAsset']['free'])
    close = float(client.get_symbol_ticker(symbol=ticker)['price'])
    maxBuy = round(balanceBuy / close * .995, r)
    return maxBuy
    
def sellAmountIsolatedMargin(ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"]) # pos in list can change when updated
    r = num_of_zeros(step)
    balanceSell = float(client.get_isolated_margin_account(symbols=ticker,
    recvWindow=10000)['assets'][0]['baseAsset']['free'])
    maxSell = round(balanceSell * .995, r)
    return maxSell



@app.route('/')

@app.route('/webhook_spot', methods=['POST'])
def webhook_spot():
    
    data = json.loads(request.data)
    
    if data['user'] != config.WEBHOOK_USER:
        return {
            "code": "error",
            "message": "invalid user"
        }
    
    ticker= data.get('ticker')
    side = data.get('side')
    if side == "BUY":
        quantity = buyAmount('USDT', ticker)
    elif side == "SELL":
        quantity = sellAmount(ticker[:-4], ticker)
    print(quantity)
    order_response = orderSpot(side, quantity, ticker)

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }

@app.route('/webhook_isolated_margin', methods=['POST'])
def webhook_isolated_margin():
    
    data = json.loads(request.data)
    
    if data['user'] != config.WEBHOOK_USER:
        return {
            "code": "error",
            "message": "invalid user"
        }
    
    ticker= data.get('ticker')
    side = data.get('side')
    if side == "BUY":
        quantity = buyAmountIsolatedMargin(ticker)
    elif side == "SELL":
        quantity = sellAmountIsolatedMargin(ticker)
    print(quantity)
    order_response = orderIsolatedMargin(side, quantity, ticker)

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }