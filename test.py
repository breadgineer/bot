import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from unicodedata import name
import requests
from binance.websockets import BinanceSocketManager


giancarlo = Client(config.user_credentials[0]["API"]["key"], config.user_credentials[0]["API"]["secret"])
david = Client(config.user_credentials[1]["API"]["key"], config.user_credentials[1]["API"]["secret"])
price = 0

print(david.get_all_margin_orders(symbol="ANKRUSDT",isIsolated='TRUE'))
