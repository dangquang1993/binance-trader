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
from Orders import Orders


formater_str = '%(asctime)s,%(msecs)d %(levelname)s %(name)s: %(message)s'
formatter = logging.Formatter(formater_str)
datefmt="%Y-%b-%d %H:%M:%S"

LOGGER_ENUM = {'debug':'debug.log', 'trading':'trades.log','errors':'general.log'}
#LOGGER_FILE = LOGGER_ENUM['pre']
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

    # Buy/Sell qty
    quantity = 0

    # BTC amount
    amount = 0

    # percent (When you drop 10%, sell panic.)
    stop_loss = 0

    # percent (When you drop 10%, sell panic.)
    stop_trade = 0

    # Define trade vars  
    order_id = 0
    order_data = None

    buy_filled = True
    sell_filled = True

    buy_filled_qty = 0
    sell_filled_qty = 0

    # 1 short > long
    # 0 short = long
    # -1 short > long
    short_long=0

    # 1 short > mid
    # 0 short = mid
    # -1 short > mid
    short_mid=0
    
    tic = 0

    bestprice = 0

    exitrequest = 0

    # float(step_size * math.floor(float(free)/step_size))
    step_size = 0

    # Define static vars
    WAIT_TIME_BUY_SELL = 1 # seconds
    WAIT_TIME_CHECK_BUY_SELL = 0.2 # seconds
    WAIT_TIME_CHECK_SELL = 5 # seconds
    WAIT_TIME_STOP_LOSS = 20 # seconds

    MAX_TRADE_SIZE = 7 # int

    # Type of commision, Default BNB_COMMISION
    commision = BNB_COMMISION

    def __init__(self, option):
        print("options: {0}".format(option))

        # Get argument parse options
        self.option = option

        # Define parser vars
        self.order_id = self.option.orderid
        self.quantity = self.option.quantity
        self.wait_time = self.option.wait_time
        self.stop_loss = self.option.stop_loss
        self.stop_trade = self.option.stop_trade

        self.increasing = self.option.increasing
        self.decreasing = self.option.decreasing

        # BTC amount
        self.amount = self.option.amount

        # Type of commision
        if self.option.commision == 'TOKEN':
            self.commision = TOKEN_COMMISION

    def setup_logger(self, symbol, debug=True):
        """Function setup as many loggers as you want"""
        #handler = logging.FileHandler(log_file)
        #handler.setFormatter(formatter)
        #logger.addHandler(handler)
        logger = logging.getLogger(symbol)

        stout_handler = logging.StreamHandler(sys.stdout)
        if debug:
            logger.setLevel(logging.DEBUG)
            stout_handler.setLevel(logging.DEBUG)

        #handler = logging.handlers.SysLogHandler(address='/dev/log')
        #logger.addHandler(handler)
        stout_handler.setFormatter(formatter)
        logger.addHandler(stout_handler)
        return logger


    def buy(self, symbol, quantity):

        # Do you have an open order?
        self.check_order()

        try:

            # Create order
            order = Orders.buy_market(symbol, quantity)
            orderId = order['orderId']
            #print('Buy order created id:%d, q:%.8f, p:%.8f' % (orderId, quantity, float(buyPrice)))
            print('%s : Buy order created id:%d, q:%.8f' % (symbol, orderId, quantity))

            time.sleep(self.WAIT_TIME_CHECK_SELL)

            # Database log
            # Database.write([orderId, symbol, 0, buyPrice, 'BUY', quantity, self.option.profit])

            if order['status'] == 'FILLED':
                print('Buy order (Filled) Id: %d' % orderId)

            self.order_id = orderId
            return orderId

        except Exception as e:
            print('Buy error: %s' % (e))
            time.sleep(self.WAIT_TIME_BUY_SELL)
            return None

    def sell(self, symbol, quantity, orderId):

        if orderId > 0:
            buy_order = Orders.get_order(symbol, orderId)

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
         
        available_quantity = float(Orders.balance(symbol))
        trunc_quantity = math.floor(available_quantity *100)/100
        if available_quantity>quantity:
            print('Sell order s: %s q:%f' % (symbol,quantity))
            sell_order = Orders.sell_market(symbol, quantity)
            sell_id = sell_order['orderId']
            print('Sell order create id: %d' % sell_id)
        else:
            if trunc_quantity > 0.001:
                print('Sell order s: %s q:%f' % (symbol,trunc_quantity))
                sell_order = Orders.sell_market(symbol, trunc_quantity)
                sell_id = sell_order['orderId']
                print('Sell order create id: %d' % sell_id)
            else:
                self.order_id = 0
                self.order_data = None
                return


        time.sleep(self.WAIT_TIME_CHECK_SELL)

        if sell_order['status'] == 'FILLED':
            print('Sell order (Filled) Id: %d' % sell_id)

            self.order_id = 0
            self.order_data = None
            return

    def check(self, symbol, orderId, quantity):
        # If profit is available and there is no purchase from the specified price, take it with the market.

        # Do you have an open order?
        self.check_order()

        trading_size = 0
        time.sleep(self.WAIT_TIME_BUY_SELL)

        while trading_size < self.MAX_TRADE_SIZE:

            # Order info
            order = Orders.get_order(symbol, orderId)

            side  = order['side']
            price = float(order['price'])

            # TODO: Sell partial qty
            orig_qty = float(order['origQty'])
            self.buy_filled_qty = float(order['executedQty'])

            status = order['status']

            #print('Wait buy order: %s id:%d, price: %.8f, orig_qty: %.8f' % (symbol, order['orderId'], price, orig_qty))
            print('Wait buy order: %s id:%d, price: %.8f, orig_qty: %.8f' % (symbol, order['orderId'], price, orig_qty))

            if status == 'NEW':

                if self.cancel(symbol, orderId):

                    buyo = Orders.buy_market(symbol, quantity)

                    #print('Buy market order')
                    print('Buy market order')

                    self.order_id = buyo['orderId']
                    self.order_data = buyo

                    if buyo == True:
                        break
                    else:
                        trading_size += 1
                        continue
                else:
                    break

            elif status == 'FILLED':
                self.order_id = order['orderId']
                self.order_data = order
                #print('Filled')
                print('Filled')
                break
            elif status == 'PARTIALLY_FILLED':
                #print('Partial filled')
                print('Partial filled')
                break
            else:
                trading_size += 1
                continue

    def cancel(self, symbol, orderId):
        # If order is not filled, cancel it.
        check_order = Orders.get_order(symbol, orderId)

        if not check_order:
            self.order_id = 0
            self.order_data = None
            return True

        if check_order['status'] == 'NEW' or check_order['status'] != 'CANCELLED':
            Orders.cancel_order(symbol, orderId)
            self.order_id = 0
            self.order_data = None
            return True

    def check_order(self):
        # If there is an open order, exit.
        if self.order_id > 0:
            exit(1)

    # 0:hold, 1:buy, 2:sell
    def analyze(self, symbol):
        klines = Orders.get_historical_klines(symbol, "1m", "30 min ago UTC")
        klinearray = np.flipud(np.array(klines).astype(np.float))
        # shortMA = np.average(klinearray[0:5,4], weights=[1,2/3,2/4,2/5,2/6])
        shortMA = np.average(klinearray[0:3,4], weights=[1,2/3,1/2])
        longMA = klinearray[0:20,4].mean()

        retval = 0
        new_short_long = 0
        if shortMA > longMA:
            new_short_long = 1
        elif shortMA < longMA:
            new_short_long = -1

        if self.short_long != 0 and self.short_long*new_short_long == -1:
            if new_short_long > self.short_long:
                retval = 1
            else:
                retval = 2

        self.short_long = new_short_long

        # Order book prices
        lastBid, lastAsk = Orders.get_order_book(symbol)
        if self.bestprice == 0:
            if retval == 1:
                self.bestprice = lastAsk 
        else:
            if lastAsk > self.bestprice:
                self.bestprice = lastAsk 

            if self.bestprice*(1-self.stop_loss/100) > lastAsk:
                retval = 2
                return retval
        toc = time.time()
        if retval != 0:
            if toc-self.tic < 30:
                return 0
            else:
                self.tic = toc
        return retval


    def action(self, symbol):
        #import ipdb; ipdb.set_trace()

        # Order amount
        quantity = self.quantity

        # analyze = threading.Thread(target=analyze, args=(symbol,))
        # analyze.start()
        analyze = self.analyze(symbol)

        if analyze == 1:
            print("buying order ID: %s" %self.order_id)
            if self.order_id == 0:
                self.buy(symbol, quantity)
        elif analyze == 2:
            print("selling order ID: %s" %self.order_id)
            # Perform sell action
            sellAction = threading.Thread(target=self.sell, args=(symbol, quantity, self.order_id,))
            sellAction.start()
        else:
            return

    def filters(self):

        symbol = self.option.symbol

        # Get symbol exchange info
        symbol_info = Orders.get_info(symbol)

        if not symbol_info:
            print('Invalid symbol, please try again...')
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}

        return symbol_info

    def format_step(self, quantity, stepSize):
        return float(stepSize * math.floor(float(quantity)/stepSize))

    def validate(self):

        valid = True
        symbol = self.option.symbol
        filters = self.filters()['filters']

        # Order book prices
        lastBid, lastAsk = Orders.get_order_book(symbol)

        lastPrice = Orders.get_ticker(symbol)

        minQty = float(filters['LOT_SIZE']['minQty'])
        minPrice = float(filters['PRICE_FILTER']['minPrice'])
        minNotional = float(filters['MIN_NOTIONAL']['minNotional'])
        quantity = float(self.option.quantity)

        # stepSize defines the intervals that a quantity/icebergQty can be increased/decreased by.
        stepSize = float(filters['LOT_SIZE']['stepSize'])

        # tickSize defines the intervals that a price/stopPrice can be increased/decreased by
        tickSize = float(filters['PRICE_FILTER']['tickSize'])

        # If option increasing default tickSize greater than
        if (float(self.option.increasing) < tickSize):
            self.increasing = tickSize

        # If option decreasing default tickSize greater than
        if (float(self.option.decreasing) < tickSize):
            self.decreasing = tickSize

        # Just for validation
        lastBid = lastBid + self.increasing

        # Set static
        # If quantity or amount is zero, minNotional increase 10%
        quantity = (minNotional / lastBid)
        quantity = quantity + (quantity * 10 / 100)
        notional = minNotional

        if self.amount > 0:
            # Calculate amount to quantity
            quantity = (self.amount / lastBid)

        if self.quantity > 0:
            # Format quantity step
            quantity = self.quantity

        quantity = self.format_step(quantity, stepSize)
        notional = lastBid * float(quantity)

        # Set Globals
        self.quantity = quantity
        self.step_size = stepSize

        # minQty = minimum order quantity
        if quantity < minQty:
            print('Invalid quantity, minQty: %.8f (u: %.8f)' % (minQty, quantity))
            valid = False

        if lastPrice < minPrice:
            print('Invalid price, minPrice: %.8f (u: %.8f)' % (minPrice, lastPrice))
            valid = False

        # minNotional = minimum order value (price * quantity)
        if notional < minNotional:
            print('Invalid notional, minNotional: %.8f (u: %.8f)' % (minNotional, notional))
            valid = False

        if not valid:
            exit(1)

    def run(self):

        cycle = 0
        actions = []

        symbol = self.option.symbol
        print('start session')
        print('Auto Trading for Binance.com @yasinkuyu')
        print('\n')

        # Validate symbol
        self.validate()

        print('Started...')
        print('Trading Symbol: %s' % symbol)
        print('Buy Quantity: %.8f' % self.quantity)
        print('Stop-Loss Amount: %s' % self.stop_loss)
        print('Stop-Trade Amount: %s' % self.stop_trade)

        print('\n')

        startTime = time.time()

        """
        # DEBUG LINES
        actionTrader = threading.Thread(target=self.action, args=(symbol,))
        actions.append(actionTrader)
        actionTrader.start()

        endTime = time.time()

        if endTime - startTime < self.wait_time:

            time.sleep(self.wait_time - (endTime - startTime))

            # 0 = Unlimited loop
            if self.option.loop > 0:
                cycle = cycle + 1

        """

        while (cycle <= self.option.loop and self.exitrequest == 0):

           startTime = time.time()

           actionTrader = threading.Thread(target=self.action, args=(symbol,))
           actions.append(actionTrader)
           actionTrader.start()

           endTime = time.time()

           if endTime - startTime < self.wait_time:

               time.sleep(self.wait_time - (endTime - startTime))

               # 0 = Unlimited loop
               if self.option.loop > 0:
                   cycle = cycle + 1
