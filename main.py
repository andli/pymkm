#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a working app for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.9.0"
__license__ = "MIT"

import sys
import os.path
from pymkm import PyMKM
from pymkm import api_wrapper
from helper import PyMKM_Helper
import json
import pprint
import tabulate as tb
import progressbar
import math
from distutils.util import strtobool

PRICE_CHANGES_FILE = 'price_changes.json'


def main():
    try:
        api = PyMKM()
    except FileNotFoundError:
        print("You must copy config_template.json to config.json and populate the fields.")
        sys.exit(0)
    except Exception as error:
        print(error)

    loop = True
    while loop:
        menu_items = [
            "Update stock prices",
            "Update price for specific card",
            "List article competition",
            "Show top 20 expensive items in stock",
            "Show account info"
        ]
        __print_menu(menu_items)

        choice = input("Action number: ")

        if choice == "1":
            try:
                update_stock_prices_to_trend(api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "2":
            search_string = __prompt_string('Search string')
            try:
                update_product_to_trend(search_string, api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "3":
            is_foil = False
            search_string = __prompt_string('Search string')
            if __prompt("Foil?") == True:
                is_foil = True
            try:
                search_for_product(search_string, is_foil, api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "4":
            try:
                show_top_expensive_articles_in_stock(20, api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "5":
            try:
                show_account_info(api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "0":
            loop = False
        else:
            print("Not a valid choice, try again.")


def __print_menu(menu_items):
    menu_top = "╭" + 3 * "─" + " MENU " + 50 * "─" + "╮"
    print(menu_top)
    index = 1
    for item in menu_items:
        print("│ {}: {}{}│".format(str(index), menu_items[index - 1], (len(menu_top) -
                                                                       len(menu_items[index - 1]) - 6) * " "))
        index += 1
    print("│ 0: Exit" + (len(menu_top) - 10) * " " + "│")
    print("╰" + (len(menu_top) - 2) * "─" + "╯")


@api_wrapper
def show_account_info(api):
    pp = pprint.PrettyPrinter()
    pp.pprint(api.get_account())


@api_wrapper
def search_for_product(search_string, is_foil, api):
    try:
        product = api.find_product(search_string, **{
            'exact ': 'true',
            'idGame': 1,
            'idLanguage': 1
            # TODO: Add Partial Content support
        })['product'][0]

        show_competition_for_product(product['idProduct'], product['enName'], is_foil, api=api)
    except Exception as err:
        print(err)


def show_competition_for_product(product_id, product_name, is_foil, api):
    print("Found product: {}".format(product_name))
    account = api.get_account()['account']
    country_code = account['country']
    articles = api.get_articles(product_id, **{
        'isFoil': str(is_foil).lower(),
        'isAltered': 'false',
        'isSigned': 'false',
        'minCondition': 'EX',
        'country': country_code,
        'idLanguage': 1
    })
    table_data = []
    table_data_local = []
    for article in articles:
        username = article['seller']['username']
        if article['seller']['username'] == account['username']:
            username = '-> ' + username
        item = [
            username,
            article['seller']['address']['country'],
            article['condition'],
            article['count'],
            article['price']
        ]
        if article['seller']['address']['country'] == country_code:
            table_data_local.append(item)
        table_data.append(item)
    if table_data_local:
        __print_product_top_list("Local competition:", table_data_local, 4, 20)
    if table_data:
        __print_product_top_list("Top 20 cheapest:", table_data, 4, 20)
    else:
        print('No prices found.')


def __print_product_top_list(title_string, table_data, sort_column, rows):
    print(70*'-')
    print('{} \n'.format(title_string))
    print(tb.tabulate(sorted(table_data, key=lambda x: x[sort_column], reverse=False)[:rows],
                      headers=['Username', 'Country',
                               'Condition', 'Count', 'Price'],
                      tablefmt="simple"))
    print(70*'-')
    print('Total average price: {}, Total median price: {}, Total # of articles: {}\n'.format(
        str(PyMKM_Helper.calculate_average(table_data, 3, 4)),
        str(PyMKM_Helper.calculate_median(table_data, 3, 4)),
        str(len(table_data))
    )
    )


@api_wrapper
def update_product_to_trend(search_string, api):
    ''' This function updates one product in the user's stock to TREND. '''

    try:
        product = api.find_stock_article(search_string, 1)[0]
    except Exception as err:
        print(err)

    r = _update_price_for_single_article(product, api)

    if r:
        _draw_price_changes_table([r])

        if __prompt("Do you want to update these prices?") == True:
            # Update articles on MKM
            api.set_stock([r])
            print('Price updated.')
        else:
            print('Prices not updated.')
    else:
        print('No prices to update.')


@api_wrapper
def update_stock_prices_to_trend(api):
    ''' This function updates all prices in the user's stock to TREND. '''
    uploadable_json = []
    if os.path.isfile(PRICE_CHANGES_FILE):
        if __prompt("Found existing changes. Upload [y] or discard [n]?") == True:
            with open(PRICE_CHANGES_FILE, 'r') as changes:
                uploadable_json = json.load(changes)

    else:

        uploadable_json = _calculate_new_prices_for_stock(api)
        with open(PRICE_CHANGES_FILE, 'w') as outfile:
            json.dump(uploadable_json, outfile)

    if len(uploadable_json) > 0:

        _display_price_changes_table(uploadable_json)

        if __prompt("Do you want to update these prices?") == True:
            # Update articles on MKM
            api.set_stock(uploadable_json)
            print('Prices updated.')
            os.remove(PRICE_CHANGES_FILE)
        else:
            print('Prices not updated. Changes saved.')
    else:
        print('No prices to update.')


def _calculate_new_prices_for_stock(api):
    stock_list = __get_stock_as_array(api=api)
    # HACK: filter out a foil product
    # stock_list = [x for x in stock_list if x['idProduct'] == 18204]
    # stock_list = [x for x in stock_list if x['idProduct'] == 261922]
    # stock_list = [x for x in stock_list if x['idProduct'] == 273118] # Thunderbreak Regent GD foil
    # stock_list = [x for x in stock_list if x['isFoil']]
    # 301546 expensive

    result_json = []
    index = 0

    bar = progressbar.ProgressBar(max_value=len(stock_list))
    for article in stock_list:
        updated_article = _update_price_for_single_article(article, api)
        if updated_article:
            result_json.append(updated_article)
        index += 1
        bar.update(index)
    bar.finish()
    return result_json


def _update_price_for_single_article(article, api):
    if not article['isFoil']:
        r = api.get_product(article['idProduct'])
        new_price = math.ceil(r['product']['priceGuide']['TREND'] * 4) / 4
    else:  # FOIL
        new_price = __get_foil_price(api, article['idProduct'])
    price_diff = new_price - article['price']
    if price_diff != 0:
        return {
            "name": article['product']['enName'],
            "foil": article['isFoil'],
            "old_price": article['price'],
            "price": new_price,
            "price_diff": price_diff,
            "idArticle": article['idArticle'],
            "count": article['count']
        }


def _display_price_changes_table(changes_json):
    if len(changes_json) > 0:
        # table breaks because of progress bar rendering
        print('\nBest diffs:\n')
        sorted_best = sorted(
            changes_json, key=lambda x: x['price_diff'], reverse=True)[:10]
        _draw_price_changes_table(
            i for i in sorted_best if i['price_diff'] > 0)
        print('\nWorst diffs:\n')
        sorted_worst = sorted(changes_json, key=lambda x: x['price_diff'])[:10]
        _draw_price_changes_table(
            i for i in sorted_worst if i['price_diff'] < 0)

        print('\nTotal price difference: {}\n'.format(
            str(round(sum(item['price_diff'] for item in changes_json), 2))))


def _draw_price_changes_table(sorted_best):
    print(tb.tabulate(
        [[item['name'], item['foil'], item['old_price'], item['price'],
            item['price_diff']] for item in sorted_best],
        headers=['Name', 'Foil?', 'Old price', 'New price', 'Diff'],
        tablefmt="simple"
    ))


@api_wrapper
def show_top_expensive_articles_in_stock(num_articles, api):
    stock_list = __get_stock_as_array(api=api)
    table_data = []

    for article in stock_list:
        table_data.append(
            [str(article['idProduct']), article['product']['enName'], article['price']])
    if len(stock_list) > 0:
        print('Top {} most expensive articles in stock:\n'.format(str(num_articles)))
        print(tb.tabulate(sorted(table_data, key=lambda x: x[2], reverse=True)[:num_articles],
                          headers=['Product ID', 'Name', 'Price'],
                          tablefmt="simple")
              )
    return None


def __get_foil_price(api, product_id):
    # NOTE: This is a rough algorithm, designed to be safe and not to sell aggressively.
    # 1) See filter parameters below.
    # 2) Set price to lowest + (median - lowest / 4), rounded to closest quarter Euro.
    # 3) Undercut price in own country if not contradicting 2)
    # 4) Never go below 0.25 for foils

    account = api.get_account()['account']
    articles = api.get_articles(product_id, **{
        'isFoil': 'true',
        'isAltered': 'false',
        'isSigned': 'false',
        'minCondition': 'GD',
        'idLanguage': 1  # English
    })

    keys = ['idArticle', 'count', 'price', 'condition', 'seller']
    foil_articles = [{x: y for x, y in art.items() if x in keys}
                     for art in articles]
    local_articles = []
    for article in foil_articles:
        if article['seller']['address']['country'] == account['country'] and article['seller']['username'] != account['username']:
            local_articles.append(article)

    local_table_data = []
    for article in local_articles:
        if article:
            local_table_data.append([
                article['seller']['username'],
                article['seller']['address']['country'],
                article['condition'],
                article['count'],
                article['price']
            ])

    table_data = []
    for article in foil_articles:
        if article:
            table_data.append([
                article['seller']['username'],
                article['seller']['address']['country'],
                article['condition'],
                article['count'],
                article['price']
            ])

    median_price = PyMKM_Helper.calculate_median(table_data, 3, 4)
    lowest_price = PyMKM_Helper.calculate_lowest(table_data, 4)
    median_guided = PyMKM_Helper.round_up_to_quarter(
        lowest_price + (median_price - lowest_price) / 4)

    if len(local_table_data) > 0:
        # Undercut if there is local competition
        lowest_in_country = PyMKM_Helper.round_down_to_quarter(
            PyMKM_Helper.calculate_lowest(local_table_data, 4))
        return max(0.25, min(median_guided, lowest_in_country - 0.25))
    else:
        # No competition in our country, set price a bit higher.
        return PyMKM_Helper.round_up_to_quarter(median_guided * 1.2)


def __get_stock_as_array(api):
    d = api.get_stock()['article']

    keys = ['idArticle', 'idProduct',
            'product', 'count', 'price', 'isFoil']
    stock_list = [{x: y for x, y in art.items() if x in keys} for art in d]
    return stock_list


def __prompt(query):
    print('{} [y/n]: '.format(query))
    val = input()
    try:
        ret = strtobool(val)
    except ValueError:
        print("Please answer with y/n")
        return __prompt(query)
    return ret


def __prompt_string(query):
    print('{}: '.format(query))
    val = input()
    return val


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
