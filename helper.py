#!/usr/bin/env python3
"""
Helper functions for the PyMKM example app.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.9.0"
__license__ = "MIT"

import sys
import math, statistics


class PyMKM_Helper:

    @staticmethod
    def calculate_average(table, col_no_count, col_no_price):
        flat_array = []
        for row in table:
            l = row[col_no_count] * [row[col_no_price]]
            flat_array.extend(l)
        return round(statistics.mean(flat_array), 2)
    
    @staticmethod
    def calculate_median(table, col_no_count, col_no_price):
        flat_array=[]
        for row in table:
            l = row[col_no_count] * [row[col_no_price]]
            flat_array.extend(l)
        return round(statistics.median(flat_array), 2)
   
    @staticmethod
    def calculate_lowest(table, col_no_price):
        flat_array=[]
        for row in table:
            flat_array.extend([row[col_no_price]])
        return min(flat_array)

    @staticmethod
    def round_up_to_quarter(price):
        return math.ceil(price * 4) / 4

    @staticmethod
    def round_down_to_quarter(price):
        return math.floor(price * 4) / 4