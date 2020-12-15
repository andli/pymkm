#!/usr/bin/env python3
"""
Helper functions for the PyMKM example app.
"""

__author__ = "Andreas Ehrlund"
__version__ = "2.1.0"
__license__ = "MIT"

import math
import statistics
import shelve
import collections.abc
import time
from distutils.util import strtobool


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time_label" in kw:
            print(f"{kw['log_time_label']} took {round(te - ts)}s")
        return result

    return timed


class PyMkmHelper:
    @staticmethod
    def string_to_float_or_int(input_string):
        try:
            if float(input_string).is_integer():
                return int(float(input_string))
            else:
                return float(input_string)
        except ValueError:
            return input_string

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
    def get_lowest_price_from_table(table, col_no_price):
        flat_array = []
        for row in table:
            flat_array.extend([row[col_no_price]])
        return min(flat_array)

    @staticmethod
    def round_up_to_multiple_of_lower_limit(limit, price):
        inverse_limit = 1 / limit
        return round(math.ceil(price * inverse_limit) / inverse_limit, 2)

    @staticmethod
    def round_down_to_multiple_of_lower_limit(limit, price):
        inverse_limit = 1 / limit
        return round(max(limit, math.floor(price * inverse_limit) / inverse_limit), 2)

    @staticmethod
    def prompt_bool(prompt_string):
        print("> {} [y/N]: ".format(prompt_string))
        val = input()
        if val == "":
            return False
        try:
            return strtobool(val)
        except ValueError:
            print("Please answer with y/n")
            return PyMkmHelper.prompt_bool(prompt_string)

    @staticmethod
    def prompt_string(prompt_string):
        print("> {}: ".format(prompt_string))
        val = input()
        return val

    @staticmethod
    def write_list(file_name, list_data):
        with open(file_name, "a") as f:
            for item in list_data:
                f.write(str(item) + "\n")

    @staticmethod
    def read_list(file_name, list_data):
        with open(file_name, "r") as f:
            for line in f:
                list_data.append(int(line.strip()))

    @staticmethod
    def store_to_cache(filename, label, data):
        s = shelve.open(filename)
        if len(data) > 0:
            try:
                s[label] = data
                print(f"[Cache] {label.title()} cached ({len(data)} items).")
                return len(s[label])
            finally:
                s.close()

    @staticmethod
    def append_to_cache(filename, label, data):
        s = shelve.open(filename)
        if len(data) > 0:
            try:
                appended_data = s[label]
                appended_data.extend(data)
                s[label] = appended_data
                print(f"[Cache] {label.title()} cached ({len(data)} new items).")
                return len(s[label])
            except KeyError:
                s.close()
                return PyMkmHelper.store_to_cache(filename, label, data)
            finally:
                s.close()

    @staticmethod
    def clear_cache(filename, label):
        s = shelve.open(filename)
        try:
            del s[label]
            print(f"[Cache] {label.title()} cleared.")
        except KeyError:
            pass
        finally:
            s.close()

    @staticmethod
    def read_from_cache(filename, label):
        s = shelve.open(filename)
        try:
            return s[label]
        except KeyError as ke:
            return None
        finally:
            s.close()

    @staticmethod
    def update_recursive(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = PyMkmHelper.update_recursive(d.get(k, {}), v)
            elif k not in d:
                d[k] = v
        return d
