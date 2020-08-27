# -*- coding: UTF-8 -*-
# @yasinkuyu

# Define Python imports
import os
import sys
import time
import config
import threading
import math
import logging
import logging.handlers

import numpy as np

# Define Custom imports
from Database import Database
from BinanceWrapper import BinanceWrapper


formater_str = '%(asctime)s,%(msecs)d %(levelname)s %(name)s: %(message)s'
formatter = logging.Formatter(formater_str)
datefmt="%Y-%b-%d %H:%M:%S"

LOGGER_ENUM = {'debug':'debug.log', 'trading':'trades.log','errors':'general.log'}
LOGGER_FILE = "binance-trader.log"
FORMAT = '%(asctime)-15s - %(levelname)s:  %(message)s'

logger = logging.basicConfig(filename=LOGGER_FILE, filemode='a',
                             format=formater_str, datefmt=datefmt,
                             level=logging.INFO)

# Aproximated value to get back the commision for sell and buy
TOKEN_COMMISION = 0.001
BNB_COMMISION   = 0.0005
#((eth*0.05)/100)

class Trading():

    klines = []

    running = False
    holding = False
    orgFund = 0 #USDT
    asset = 0 #USDT
    
    symbol = ""

    # Define trade vars  
    order_id = 0
    order_data = None

    buy_filled = True
    sell_filled = True

    buy_filled_qty = 0
    sell_filled_qty = 0
    
    tic = 0

    bestprice = 0

    exitrequest = False
    # float(step_size * math.floor(float(free)/step_size))
    step_size = 0

    WAIT_TIME_BUY_SELL = 1 # seconds
    WAIT_TIME_CHECK_BUY_SELL = 0.2 # seconds
    WAIT_TIME_CHECK_SELL = 5 # seconds
    WAIT_TIME_STOP_LOSS = 20 # seconds
    # Type of commision, Default BNB_COMMISION
    commision = TOKEN_COMMISION

    def __init__(self, option):
        print("options: {0}".format(option))

        # Get argument parse options
        self.option = option

    def buy(self, symbol, quantity):
        try:
            # Create order
            order = BinanceWrapper.buy_market(symbol, quantity)
            orderId = order['orderId']
            #print('Buy order created id:%d, q:%.8f, p:%.8f' % (orderId, quantity, float(buyPrice)))
            print('%s : Buy order created id:%d, q:%.8f' % (symbol, orderId, quantity))

            time.sleep(self.WAIT_TIME_CHECK_SELL)

            # Database log
            # Database.write([orderId, symbol, 0, buyPrice, 'BUY', quantity, self.option.profit])

            count = 0

            while order['status'] != 'FILLED' and count < 5:
                time.sleep(self.WAIT_TIME_BUY_SELL)
                print('Buy order (Filled) Id: %d' % orderId)
                count = count+1
            if order['status'] != 'FILLED':
                self.cancel(symbol, orderId)
                return None

            self.order_id = orderId
            return orderId

        except Exception as e:
            print('Buy error: %s' % (e))
            time.sleep(self.WAIT_TIME_BUY_SELL)
            return None

    def sell(self, symbol, quantity, orderId, refprice):

        if orderId > 0:
            buy_order = BinanceWrapper.get_order(symbol, orderId)

            if buy_order['status'] == 'FILLED' and buy_order['side'] == 'BUY':
                print('Buy order filled... Try sell...')
            else:
                time.sleep(self.WAIT_TIME_CHECK_BUY_SELL)
                if buy_order['status'] == 'FILLED' and buy_order['side'] == 'BUY':
                    print('Buy order filled after 0.1 second... Try sell...')
                elif buy_order['status'] == 'PARTIALLY_FILLED' and buy_order['side'] == 'BUY':
                    print('Buy order partially filled... Try sell... Cancel remaining buy...')
                    self.cancel(symbol, orderId)
                else:
                    self.cancel(symbol, orderId)
                    print('Buy order fail (Not filled) Cancel order...')
                    self.order_id = 0
                    return
         
        available_quantity = float(BinanceWrapper.balance(symbol))
        trunc_quantity = math.floor(available_quantity *100)/100
        if available_quantity>quantity:
            if quantity*refprice > self.minNotational:
                print('Sell order s: %s q:%f' % (symbol,quantity))
                sell_order = BinanceWrapper.sell_market(symbol, math.floor(quantity *100)/100)
                sell_id = sell_order['orderId']
                print('Sell order create id: %d' % sell_id)
            else:
                return
        else:
            if trunc_quantity > 0.001 and trunc_quantity*refprice > self.minNotational:
                print('Sell order s: %s q:%f' % (symbol,trunc_quantity))
                sell_order = BinanceWrapper.sell_market(symbol, trunc_quantity)
                sell_id = sell_order['orderId']
                print('Sell order create id: %d' % sell_id)
            else:
                return
        
        time.sleep(self.WAIT_TIME_CHECK_SELL)
        count = 0
        while sell_order['status'] != 'FILLED' and count < 5:
            time.sleep(self.WAIT_TIME_BUY_SELL)
            print('Sell order (Filled) Id: %d' % orderId)
            count = count+1
        newasset = float(sell_order['price'])*float(sell_order['cummulativeQuoteQty'])
        print("new asset on bot %s: %s" %(self.symbol, newasset)) 

        if self.orgFund*(1-self.option.stop_trade/100) > newasset:
            self.exitrequest = True

    def cancel(self, symbol, orderId):
        # If order is not filled, cancel it.
        check_order = BinanceWrapper.get_order(symbol, orderId)

        if not check_order:
            self.order_id = 0
            self.order_data = None
            return True

        if check_order['status'] == 'NEW' or check_order['status'] != 'CANCELLED':
            BinanceWrapper.cancel_order(symbol, orderId)
            self.order_id = 0
            self.order_data = None
            return True

    # 0:hold, 1:buy, 2:sell
    def analyzeSMA(self, symbol, newKline):
        # shortMA = np.average(klinearray[0:5,4], weights=[1,2/3,2/4,2/5,2/6])
        priceArray = [float(k["c"]) for k in self.klines ]
        priceArray.append(float(newKline["k"]["c"]))
        closePrices = np.array(priceArray)

        shortMA = np.average(closePrices[len(closePrices)-5:len(closePrices)], weights=[2/(i+2) for i in range(5)])
        longMA = np.average(closePrices[len(closePrices)-30:len(closePrices)], weights=[2/(i+2) for i in range(30)])

        retval = 0
        
        if shortMA > longMA*1.003:
            retval = 1
        elif shortMA < longMA*0.997:
            retval = 2

        # Order book prices
        lastBid, lastAsk = BinanceWrapper.get_order_book(symbol)
        if retval == 1:
            price = lastBid + self.increasing
        else:
            price = lastAsk - self.decreasing

        if self.bestprice == 0:
            if retval == 1:
                self.bestprice = lastAsk 
        else:
            if lastAsk > self.bestprice:
                self.bestprice = lastAsk 

            if self.bestprice*(1-self.option.stop_loss/100) > lastAsk:
                retval = 2
                return retval, price

        toc = time.time()
        if retval != 0:
            if toc-self.tic < 30:
                return 0, 0
            else:
                self.tic = toc
        return retval, price

    def analyzeSpotMA(self, symbol, newKline):
        # shortMA = np.average(klinearray[0:5,4], weights=[1,2/3,2/4,2/5,2/6])
        priceArray = [float(k["c"]) for k in self.klines ]
        priceArray.append(float(newKline["k"]["c"]))
        closePrices = np.array(priceArray)

        longMA = np.average(closePrices[len(closePrices)-30:len(closePrices)], weights=[2/(i+2) for i in range(30)])

        # Order book prices
        lastBid, lastAsk = BinanceWrapper.get_order_book(symbol)

        retval = 0
        
        if lastBid > longMA*1.003:
            retval = 1
        elif lastAsk < longMA*0.997:
            retval = 2

        if retval == 1:
            price = lastBid + self.increasing
        else:
            price = lastAsk - self.decreasing

        if self.bestprice == 0:
            if retval == 1:
                self.bestprice = lastAsk 
        else:
            if lastAsk > self.bestprice:
                self.bestprice = lastAsk 

            if self.bestprice*(1-self.option.stop_loss/100) > lastAsk:
                retval = 2
                return retval, price

        toc = time.time()
        if retval != 0:
            if toc-self.tic < 30:
                return 0, 0
            else:
                self.tic = toc
        return retval, price


    def action(self, msg):
        #import ipdb; ipdb.set_trace()

        # analyze = threading.Thread(target=analyze, args=(symbol,))
        # analyze.start()

        if self.exitrequest:
            BinanceWrapper.socketStop(self.conn_soc)

        analyze, price = self.analyzeSpotMA(self.symbol, msg)

        newkline = msg["k"]
        if newkline['x'] == True:
            self.klines.append(newkline)

        if analyze == 1 and self.holding == False:
            self.holding = True
            quantity = self.format_step(self.asset/price)
            print("buying order s: %s p: %s q: %s" %(self.symbol, price, quantity))
            if self.order_id == 0:
                sellAction = threading.Thread(target=self.buy, args=(self.symbol,quantity ))
                sellAction.start()
        elif analyze == 2:
            self.holding = False
            quantity = self.format_step(self.asset/price)
            print("selling order ID: %s s: %s p: %s q: %s" %(self.order_id,self.symbol, price, quantity))
            sellAction = threading.Thread(target=self.sell, args=(self.symbol, quantity, self.order_id, price))
            sellAction.start()
        else:
            return

    def filters(self):

        # Get symbol exchange info
        symbol_info = BinanceWrapper.get_info(self.symbol)

        if not symbol_info:
            print('Invalid symbol, please try again...')
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}

        return symbol_info

    def format_step(self, quantity):
        return float(self.lotSize * math.floor(float(quantity)/self.lotSize))

    def validate(self):
        filters = self.filters()['filters']

        # Order book prices
        lastBid, lastAsk = BinanceWrapper.get_order_book(self.symbol)

        lastPrice = BinanceWrapper.get_ticker(self.symbol)

        # tickSize defines the intervals that a price/stopPrice can be increased/decreased by
        tickSize = float(filters['PRICE_FILTER']['tickSize'])
        self.lotSize = float(filters['LOT_SIZE']['stepSize'])
        self.minNotational = float(filters['MIN_NOTIONAL']['minNotional'])

        # If option increasing default tickSize greater than
        if (float(self.option.increasing) < tickSize):
            self.increasing = tickSize

        # If option decreasing default tickSize greater than
        if (float(self.option.decreasing) < tickSize):
            self.decreasing = tickSize

        # Just for validation
        lastBid = lastBid + self.increasing

    def run(self, symbol, asset):
        self.symbol = symbol
        self.orgFund = asset
        self.asset = asset

        print('Auto Trading for Binance.com @yasinkuyu')
        print('\n')

        # Validate symbol
        self.validate()

        print('Started...')
        print('Trading Symbol: %s' % symbol)
        print('Asset: %s USDT' % asset)
        print('Stop-Loss Amount: %s' % self.option.stop_loss)
        print('Stop-Trade Amount: %s' % self.option.stop_trade)

        #init klines
        try:
            klines = BinanceWrapper.get_historical_klines(symbol, "1m", "30 min ago UTC")
            index = ["t","o","h","l","c","v","T","q","n","V","Q","B"]
            self.klines = [{index[i] : k[i] for i in range(len(index))} for k in klines[0:len(klines)-1] ]

            self.conn_soc = BinanceWrapper.start_kline_socket(symbol, self.action)
        except:
            print("Exception in kline of coin %s" %symbol)

        print('\n')
