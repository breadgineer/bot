import asyncio
import json, config
import math

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


def delay(sleep_time: float):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            time.sleep(sleep_time)
            return function(*args, **kwargs)

        return wrapper

    return decorator


def num_of_zeros(n):
    if n < 1:
        s = '{:.16f}'.format(n).split('.')[1]
        return 1 + len(s) - len(s.lstrip('0'))
    else:
        return 0


def order_futures(client, side, quantity, ticker, reduce, order_type=ORDER_TYPE_MARKET, iso="TRUE"):
    try:
        if reduce == 'true':
            trade_direction = 'SHORT' if side == 'BUY' else 'LONG'
            print(f"Closing previous {trade_direction} order -  {quantity} {ticker} ")
        else:
            trade_direction = 'LONG' if side == 'BUY' else 'SHORT'
            print(f"sending {trade_direction} order - {quantity} {ticker} ")
        order = client.futures_create_order(symbol=ticker, side=side, type=order_type, quantity=quantity, reduceOnly=reduce)
        return order
    except Exception as e:
        error = "An error was encountered - " + str(e)
        # send_message(error,user_name)


def open_order_quantity_futures(client, ticker):
    step = float(client.get_symbol_info(symbol=ticker)["filters"][2]["stepSize"])
    r = num_of_zeros(step)
    total_balances = client.futures_account_balance(recvWindow=10000)
    for balance in total_balances:
        if balance['asset'] == 'USDT':
            balance_buy = float(balance['balance'])
    close = float(client.get_symbol_ticker(symbol=ticker)['price'])
    purchase_amount = balance_buy / close * .95
    if purchase_amount < 0:
        maxBuy = round(purchase_amount, r)
    else:
        maxBuy = float(math.floor(purchase_amount))

    return maxBuy


def close_order_quantity_futures(client,ticker):
    open_positions = client.futures_position_information()
    for position in open_positions:
        if ticker == position['symbol']:
            maxSell = abs(float(position['positionAmt']))

    return maxSell


@app.route('/')
def bot():
    return render_template('index.html')


@app.route('/futures', methods=['POST'])
def futures_entry():

    data = json.loads(request.data)
    time_delay = data.get('delay') # in s
    ticker = data.get('ticker')
    side = data.get('side')
    client = giancarlo
    client.futures_change_leverage(symbol=ticker, leverage=1)

    quantity_close = close_order_quantity_futures(client, ticker)
    quantity_open = open_order_quantity_futures(client, ticker)
    if side == 'BUY':
        if quantity_close != 0:
            reduce = order_futures(client, side, quantity_close, ticker, "true")
            time.sleep(time_delay)
        open = order_futures(client, side, quantity_open, ticker, "false")

    else:
        if quantity_close != 0:
            reduce = order_futures(client, side, quantity_close, ticker, "true")
            time.sleep(time_delay)
        open = order_futures(client, side, quantity_open, ticker, "false")

    return 'OK'


@app.route('/futures_info', methods=['GET'])
def futures_info():
    client = giancarlo
    return str(client.futures_position_information())



# what you neeed to do is add a decorator that delays time
# then you should have two endpoints. 1 for the Entering trades and another for exiting
# Emtering always has a delay, exiting is immediate
