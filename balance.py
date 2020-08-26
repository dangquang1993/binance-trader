#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys

sys.path.insert(0, './app')

import time
import numpy as np
from datetime import timedelta, datetime
from BinanceWrapper import BinanceWrapper

try:
    while True:
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
            
            BinanceWrapper.orders(symbol)
            
        if option=='2':
            t = time.time()
            all_symbol = BinanceWrapper.get_all_info()
            print(time.time() - t)
            
        elif option=='3':      
            for b in BinanceWrapper.balances():
                print("%s: %s" % (b["asset"], b["free"]))
            
        elif option=='4':
            print('Enter asset: (i.e. BTC)')
            symbol = input()
            print('%s balance: %s' % (symbol, BinanceWrapper.balance(symbol)))
            
            

        elif option=='7':
            lag=BinanceWrapper.server_status()

        elif option=='8':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('Enter period: (i.e. 1m)')
            period = input()
            print('%s moving average for %s period' % (symbol, period))
            BinanceWrapper.moving_average(symbol,period)

        elif option=='9':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('Enter quantity')
            quantity = input()
            BinanceWrapper.buy_market(symbol, quantity)

        elif option=='10':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('Enter quantity')
            quantity = input()
            BinanceWrapper.sell_market(symbol, quantity)

        elif option=='0':
            break
        
        else:
            print('Option not reconigzed')


except Exception as e:
    print('Exception: %s' % e)
