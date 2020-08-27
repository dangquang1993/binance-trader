#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys
import argparse

sys.path.insert(0, './app')

from Manager import Manager

if __name__ == '__main__':

    # Set parser
    parser = argparse.ArgumentParser()
 
    parser.add_argument('--stop_loss', type=float, help='Target Stop-Loss %% (If the price drops by 6%%, sell market_price.)', default=1)
    parser.add_argument('--stop_trade', type=float, help='Target Stop-trade %% (If the price value of asset drop by 20%%, sell market_price and stop trade.)', default=10)

    parser.add_argument('--increasing', type=float, help='Buy Price +Increasing (0.00000001)', default=0.00000001)
    parser.add_argument('--decreasing', type=float, help='Sell Price -Decreasing (0.00000001)', default=0.00000001)

    option = parser.parse_args()

    # Get start
    t = Manager(option)
    t.run()
