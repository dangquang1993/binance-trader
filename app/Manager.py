import os
import sys
import time
import config
import threading

from BinanceWrapper import BinanceWrapper
from Trading import Trading

class Bot:
    index: int
    bot: Trading
    thread: threading.Thread
    def __init__(self, i, bot):
        self.index = i
        self.bot = bot

class Manager():
    wait_time = 10
    nbbot = 10
    bots = []
    def __init__(self, option):
        print("options: {0}".format(option))

        self.option = option
        for i in range(self.nbbot):
            self.bots.append(Bot(i, Trading(option)))


    def run(self):
        print('start session')
        print('Auto Trading for Binance.com @dqnguyen')
        print('\n')

        print('Started...')

        print('\n')

        BinanceWrapper.socketStart()

        while (True):

            startTime = time.time()
            best = BinanceWrapper.get_all_info()[0:self.nbbot]
            avaiBalance = BinanceWrapper.balance("USDT")

            
            for b in self.bots:
                if b.bot.running == False:
                    b.thread = threading.Thread(target=b.bot.run, args = (best[b.index]["symbol"],float(avaiBalance)/5))
                    b.thread.start()
                    b.bot.running = True 

            endTime = time.time()

            if endTime - startTime < self.wait_time:

                time.sleep(self.wait_time - (endTime - startTime))
