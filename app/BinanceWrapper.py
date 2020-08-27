import config 

import time
import numpy as np

from binance.client import Client
from binance.websockets import BinanceSocketManager
from Messages import Messages

# Define Custom import vars
client = Client(config.api_key, config.api_secret)
websocket = BinanceSocketManager(client)

class BinanceWrapper():
 
    @staticmethod
    def socketStart():
        websocket.start()

    @staticmethod
    def socketStop(conn_key):
        websocket.stop_socket(conn_key)

    @staticmethod
    def start_kline_socket(symbol, function, interval = Client.KLINE_INTERVAL_1MINUTE):
        websocket.start_kline_socket(symbol, function, interval)

    @staticmethod
    def start_trade_socket(symbol, function):
        websocket.start_trade_socket(symbol, function)

    @staticmethod
    def balances():
        balances = client.get_account()
        posbalance = [b for b in balances['balances'] if  float(b['locked']) > 0 or float(b['free']) > 0]
        return posbalance

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

    @staticmethod
    def orders(symbol):
        orders = client.get_open_orders(symbol=symbol)
        return orders
        
    @staticmethod
    def get_all_info():
        infos = client.get_ticker()
        usdtput_dict = [i for i in infos if "USDT" in i["symbol"][2:]]
        best = sorted(usdtput_dict, key=lambda k: float(k["quoteVolume"]), reverse=True)
        # for i in range(20):
        #     print(best[i]["symbol"])
        return best

    @staticmethod
    def moving_average(symbol, period):
        try:        
            klines = client.get_historical_klines(symbol, period, "30 min ago UTC")
            klinearray = np.array(klines).astype(np.float)
            print(klinearray[len(klinearray)-5:len(klinearray),4])
            shortMA = np.average(klinearray[len(klinearray)-5:len(klinearray),4], weights=[1,2/3,2/4,2/5,2/6])
            longMA = klinearray[len(klinearray)-20:len(klinearray),4].mean()
            print ("short: %.5f long: %.5f" %(shortMA,longMA)) 
        except Exception as e:
            print('Get MA Exception: %s' % e)

    @staticmethod
    def server_status():
        systemT=int(time.time()*1000)           #timestamp when requested was launch
        serverT= client.get_server_time()  #timestamp when server replied
        lag=int(serverT['serverTime']-systemT)

        print('System timestamp: %d' % systemT)
        print('Server timestamp: %d' % serverT['serverTime'])
        print('Lag: %d' % lag)

        if lag>1000:
            print('\nNot good. Excessive lag (lag > 1000ms)')
        elif lag<0:
            print('\nNot good. System time ahead server time (lag < 0ms)')
        else:  
            print('\nGood (0ms > lag > 1000ms)')              
        return

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
    def get_historical_klines(symbol, period, limit):
        try:        
    
            klines = client.get_historical_klines(symbol, period, limit)
 
            return klines
            
        except Exception as e:
            print('get_historical_klines Exception: %s' % e)