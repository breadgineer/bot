import json, config
import math

from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

import logging
import sys

app = Flask(__name__)

# diables flask logger
logging.getLogger('werkzeug').disabled = True

logger = logging.getLogger('POSITION')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s ') ## development
formatter = logging.Formatter('[%(levelname)s] %(message)s ')  ## deployment
handler.setFormatter(formatter)
logger.addHandler(handler)

giancarlo = Client(config.user_credentials[0]["API"]["key"], config.user_credentials[0]["API"]["secret"])


def num_of_zeros(n):
    if n < 1:
        s = '{:.16f}'.format(n).split('.')[1]
        return 1 + len(s) - len(s.lstrip('0'))
    else:
        return 0


def order_futures(client, side, quantity, ticker, reduce, order_type=ORDER_TYPE_MARKET, iso="TRUE"):
    try:
        if reduce == 'true':
            trade_direction = 'SHORT' if side == 'SELL' else 'LONG'
            logger.info(f"Closing previous {trade_direction} order - {quantity} {ticker}")
        else:
            trade_direction = 'LONG' if side == 'BUY' else 'SHORT'
            logger.info(f"Sending {trade_direction} order - {quantity} {ticker}")
        order = client.futures_create_order(symbol=ticker, side=side, type=order_type, quantity=quantity,
                                            reduceOnly=reduce)
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
    if purchase_amount < 1:
        max_buy = round(purchase_amount, r - 1)
    else:
        max_buy = float(math.floor(purchase_amount))

    return max_buy


def close_order_quantity_futures(client, ticker):
    open_positions = client.futures_position_information()
    for position in open_positions:
        if ticker == position['symbol']:
            max_sell = abs(float(position['positionAmt']))

    return max_sell


@app.route('/')
def bot():
    return render_template('index.html')


@app.route('/futures', methods=['POST'])
def futures_entry():
    data = json.loads(request.data)
    ticker = data.get('ticker')
    side = data.get('side')
    action = data.get('action')
    client = giancarlo
    client.futures_change_leverage(symbol=ticker, leverage=1)

    if action == "CLOSE":
        quantity_close = close_order_quantity_futures(client, ticker)
        if quantity_close != 0:
            reduce = order_futures(client, side, quantity_close, ticker, "true")

            if str(reduce) == "None":
                logger.warning("Previous position reduction failed to fill")
                return 'ORDER FAILED TO FILL'
            else:
                reduce_order_time = reduce["updateTime"]
                reduce_order_average_price = client.futures_aggregate_trades(symbol=ticker, startTime=reduce_order_time)[0]['p']
                logger.info(f"Order filled at an average price of {reduce_order_average_price} USDT")
                return 'ORDER FILLED SUCCESSFULLY'
        else:
            logger.warning("No open orders, nothing to reduce")
            return 'NO OPEN ORDERS. NOTHING TO REDUCE'

    if action == "OPEN":
        quantity_open = open_order_quantity_futures(client, ticker)
        open = order_futures(client, side, quantity_open, ticker, "false")

        if str(open) == "None":
            logger.warning("New position failed to fill")
            return 'ORDER FAILED TO FILL'
        else:
            open_order_time = open["updateTime"]
            open_order_average_price = client.futures_aggregate_trades(symbol=ticker, startTime=open_order_time)[0]['p']
            logger.info(f"Order filled at an average price of {open_order_average_price} USDT")
            return 'ORDER FILLED SUCCESSFULLY'


@app.route('/test', methods=['GET'])
def futures_test():
    return "PING!"
