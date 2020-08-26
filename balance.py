#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys

sys.path.insert(0, './app')

import time
import config
import numpy as np
from datetime import timedelta, datetime

from binance.client import Client
from Orders import Orders

class Binance:

    def __init__(self):
        self.client = Client(config.api_key, config.api_secret)

    def balances(self):
        balances = self.client.get_account()
      
        for balance in balances['balances']:
            if float(balance['locked']) > 0 or float(balance['free']) > 0:
                print('%s: %s' % (balance['asset'], balance['free']))

    def balance(self, asset='BTC'):
        balances = self.client.get_account()
        balances['balances'] = {item['asset']: item for item in balances['balances']}
        
        if asset in balances['balances']:
            print(balances['balances'][asset]['free'])
        if asset[0:3] in balances['balances']:
            print(balances['balances'][asset[0:3]]['free'])
        if asset[0:4] in balances['balances']:
            print(balances['balances'][asset[0:4]]['free'])
        if asset[0:5] in balances['balances']:
            print(balances['balances'][asset[0:5]]['free'])

    def orders(self, symbol):
        orders = self.client.get_open_orders(symbol=symbol)
        print(orders)

    def get_all_info(self):
        infos = self.client.get_ticker()
        usdtput_dict = [i for i in infos if "USDT" in i["symbol"][2:]]
        best = sorted(usdtput_dict, key=lambda k: float(k["quoteVolume"]), reverse=True)
        for i in range(20):
            print(best[i]["symbol"])
        return best

    # def moving_average(self, symbol, period):
    def moving_average(self, symbol, period):
        try:        
            klines = self.client.get_historical_klines(symbol, period, "30 min ago UTC")
            klinearray = np.flipud(np.array(klines).astype(np.float))
            print(klinearray[0:5,4])
            shortMA = np.average(klinearray[0:2,4], weights=[1,2/3])
            longMA = klinearray[0:20,4].mean()
            print ("short: %.5f long: %.5f" %(shortMA,longMA)) 
        except Exception as e:
            print('Get MA Exception: %s' % e)

    def tickers(self):
        
        return self.client.get_all_tickers()

    def server_status(self):
        systemT=int(time.time()*1000)           #timestamp when requested was launch
        serverT= self.client.get_server_time()  #timestamp when server replied
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

    def openorders(self):
        
        return self.client.get_open_orders()

    def profits(self, asset='BTC'):
        coins = self.client.get_products()
        
        for coin in coins['data']:
            if coin['quoteAsset'] == asset:
                orders = self.client.get_order_book(symbol=coin['symbol'], limit=5)             
                if len(orders['bids'])>0 and len(orders['asks'])>0: 
                    lastBid = float(orders['bids'][0][0]) #last buy price (bid)
                    lastAsk = float(orders['asks'][0][0]) #last sell price (ask)
                    
                    if lastBid!=0: 
                        profit = (lastAsk - lastBid) /  lastBid * 100
                    else:
                        profit = 0
                    print('%6.2f%% profit : %s (bid: %.8f / ask: %.8f)' % (profit, coin['symbol'], lastBid, lastAsk))
                else:
                    print('---.--%% profit : %s (No bid/ask info retrieved)' % (coin['symbol']))

    def market_value(self, symbol, kline_size, dateS, dateF="" ):                 
        dateS=datetime.strptime(dateS, "%d/%m/%Y %H:%M:%S")
        
        if dateF!="":
            dateF=datetime.strptime(dateF, "%d/%m/%Y %H:%M:%S")
        else:
            dateF=dateS + timedelta(seconds=59)

        print('Retrieving values...\n')    
        klines = self.client.get_klines(symbol=symbol, interval=kline_size, startTime=int(dateS.timestamp()*1000), endTime=int(dateF.timestamp()*1000))

        if len(klines)>0:
            for kline in klines:
                print('[%s] Open: %s High: %s Low: %s Close: %s' % (datetime.fromtimestamp(kline[0]/1000), kline[1], kline[2], kline[3], kline[4]))

        return
    
try:

    while True:
        m = Binance()

        print('\n')
        print('1 >> Print orders')
        print('2 >> List Coins')
        print('3 >> List balances')
        print('4 >> Check balance')
        print('7 >> Server status')
        print('8 >> Moving average')
        print('9 >> Buy')
        print('10 >> Sell')
        print('0 >> Exit')
        print('\nEnter option number:')

        option = input()

        print('\n')

        if option=='1':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('%s Orders' % (symbol))
            
            m.orders(symbol)
            
        if option=='2':
            t = time.time()
            all_symbol = m.get_all_info()
            print(time.time() - t)
            
        elif option=='3':      
            m.balances()
            
        elif option=='4':
            print('Enter asset: (i.e. BTC)')
            symbol = input()
            print('%s balance' % (symbol))
            
            m.balance(symbol)

        elif option=='7':
            lag=m.server_status()

        elif option=='8':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('Enter period: (i.e. 1m)')
            period = input()
            print('%s moving average for %s period' % (symbol, period))
            m.moving_average(symbol,period)

        elif option=='9':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('Enter price')
            price = input()
            print('Enter quantity')
            quantity = input()
            Orders.buy_limit(symbol, quantity, price)

        elif option=='10':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('Enter price')
            price = input()
            print('Enter quantity')
            quantity = input()
            Orders.sell_limit(symbol, quantity, price)

        elif option=='0':
            break
        
        else:
            print('Option not reconigzed')


except Exception as e:
    print('Exception: %s' % e)
