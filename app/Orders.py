# -*- coding: UTF-8 -*-
# @yasinkuyu
import config 

from binance.client import Client
# from BinanceAPI import BinanceAPI
from Messages import Messages

# Define Custom import vars
client = Client(config.api_key, config.api_secret)

class Orders():
 
    @staticmethod
    def buy_limit(symbol, quantity, buyPrice):

        order = client.order_limit_buy(symbol=symbol, quantity=quantity, price=buyPrice)

        if 'msg' in order:
            Messages.get(order['msg'])

        # Buy order created.
        return order['orderId']

    @staticmethod
    def sell_limit(symbol, quantity, sell_price):

        order = client.order_limit_sell(symbol=symbol, quantity=quantity, price=sell_price)

        if 'msg' in order:
            Messages.get(order['msg'])

        return order

    @staticmethod
    def buy_market(symbol, quantity):

        order = client.order_market_buy(symbol=symbol, quantity=quantity)

        if 'msg' in order:
            Messages.get(order['msg'])

        # Buy order created.
        return order

    @staticmethod
    def sell_market(symbol, quantity):

        order = client.order_market_sell(symbol=symbol, quantity=quantity)

        if 'msg' in order:
            Messages.get(order['msg'])

        return order

    @staticmethod
    def cancel_order(symbol, orderId):
        
        try:
            
            order = client.cancel(symbol=symbol, orderId=orderId)
            if 'msg' in order:
                Messages.get(order['msg'])
            
            print('Profit loss, called order, %s' % (orderId))
        
            return True
        
        except Exception as e:
            print('cancel_order Exception: %s' % e)
            return False

    @staticmethod
    def get_order_book(symbol):
        try:

            orders = client.get_order_book(symbol=symbol, limit=5)
            lastBid = float(orders['bids'][0][0]) #last buy price (bid)
            lastAsk = float(orders['asks'][0][0]) #last sell price (ask)
     
            return lastBid, lastAsk
    
        except Exception as e:
            print('get_order_book Exception: %s' % e)
            return 0, 0

    @staticmethod
    def get_order(symbol, orderId):
        try:

            order = client.get_order(symbol=symbol, orderId=orderId)

            if 'msg' in order:
                #import ipdb; ipdb.set_trace()
                Messages.get(order['msg']) # TODO
                return False

            return order

        except Exception as e:
            print('get_order Exception: %s' % e)
            return False
    
    @staticmethod
    def get_order_status(symbol, orderId):
        return Orders.get_order(symbol, orderId)['status']
    
    @staticmethod
    def get_ticker(symbol):
        try:        
    
            ticker = client.get_ticker(symbol=symbol)
 
            return float(ticker['lastPrice'])
        except Exception as e:
            print('Get Ticker Exception: %s' % e)

    @staticmethod
    def get_info(symbol):
        try:        
    
            info = client.get_exchange_info()
            
            if symbol != "":
                return [market for market in info['symbols'] if market['symbol'] == symbol][0]
 
            return info
            
        except Exception as e:
            print('get_info Exception: %s' % e)

    @staticmethod
    def get_historical_klines(symbol, period, time):
        try:        
    
            klines = client.get_historical_klines(symbol, period, time)
 
            return klines
            
        except Exception as e:
            print('get_historical_klines Exception: %s' % e)
        
    @staticmethod
    def balance(asset='BTC'):
        balances = client.get_account()
        balances['balances'] = {item['asset']: item for item in balances['balances']}
        if asset in balances['balances']:
            return balances['balances'][asset]['free']
        if asset[0:3] in balances['balances']:
            return balances['balances'][asset[0:3]]['free']
        if asset[0:4] in balances['balances']:
            return balances['balances'][asset[0:4]]['free']
        if asset[0:5] in balances['balances']:
            return balances['balances'][asset[0:5]]['free']