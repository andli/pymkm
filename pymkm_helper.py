#!/usr/bin/env python3
"""
Helper functions for the PyMKM example app.
"""

__author__ = "Andreas Ehrlund"
__version__ = "1.5.0"
__license__ = "MIT"

import math
import statistics
from distutils.util import strtobool


class PyMkmHelper:

    @staticmethod
    def calculate_average(table, col_no_count, col_no_price):
        flat_array = []
        for row in table:
            l = row[col_no_count] * [row[col_no_price]]
            flat_array.extend(l)
        return round(statistics.mean(flat_array), 2)

    @staticmethod
    def calculate_median(table, col_no_count, col_no_price):
        flat_array = []
        for row in table:
            l = row[col_no_count] * [row[col_no_price]]
            flat_array.extend(l)
        return round(statistics.median(flat_array), 2)

    @staticmethod
    def calculate_lowest(table, col_no_price):
        flat_array = []
        for row in table:
            flat_array.extend([row[col_no_price]])
        return min(flat_array)

    @staticmethod
    def round_up_to_limit(limit, price):
        inverse_limit = 1 / limit
        return math.ceil(price * inverse_limit) / inverse_limit

    @staticmethod
    def round_down_to_limit(limit, price):
        inverse_limit = 1 / limit
        return math.floor(price * inverse_limit) / inverse_limit

    @staticmethod
    def prompt_bool(prompt_string):
        print('{} [y/N]: '.format(prompt_string))
        val = input()
        if val == '':
            return False
        try:
            return strtobool(val)
        except ValueError:
            print("Please answer with y/n")
            return PyMkmHelper.prompt_bool(prompt_string)

    @staticmethod
    def prompt_string(prompt_string):
        print('{}: '.format(prompt_string))
        val = input()
        return val
