#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a working app for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.9.0"
__license__ = "MIT"

from pymkm import PyMKM
from pymkm import api_wrapper
from helper import PyMKM_Helper
import json
import tableprint as tp
import progressbar
import math
from distutils.util import strtobool


def main():
    api = PyMKM()

    loop = True
    while loop:
        menu_items = [
            "Show top 10 expensive items in stock",
            "Update stock prices",
            "Show prices for Coiling Oracle promo",
            "Show account info"
        ]
        __print_menu(menu_items)

        choice = input("Action number: ")

        if choice == "1":
            try:
                show_top_10_expensive_articles_in_stock(api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "2":
            try:
                update_stock_prices_to_trend(api=api)
            except ConnectionError as err:
                print(err)
                print(err)
        elif choice == "3":
            try:
                show_prices_for_product(18204, api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "4":
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
    print(api.get_account())


@api_wrapper
def show_prices_for_product(product_id, api):  # 294758 works
    articles = api.get_articles(product_id, **{
        'isFoil': 'true',
        'isAltered': 'false',
        'isSigned': 'false',
        'minCondition': 'GD',
        'country': api.get_account()['account']['country'],
        'idLanguage': 1
    })
    table_data = []
    for article in articles:
        table_data.append([
            article['seller']['username'],
            article['seller']['address']['country'],
            article['condition'],
            article['count'],
            article['price']
        ])
    if len(table_data) > 0:
        __print_product_top_list(table_data, 4, 20)
    else:
        print('No prices found.')


def __print_product_top_list(table_data, sort_column, rows):
    print('Top {} cheapest articles for chosen product'.format(rows))
    tp.table(sorted(table_data, key=lambda x: x[sort_column], reverse=False)[:rows],
             ['Username', 'Country', 'Condition', 'Count', 'Price'], width=20)
    print('Total average price: {}, Total median price: {}, Total # of articles: {}'.format(
        str(PyMKM_Helper.calculate_average(table_data, 3, 4)),
        str(PyMKM_Helper.calculate_median(table_data, 3, 4)),
        str(len(table_data))
    )
    )


@api_wrapper
def update_stock_prices_to_trend(api):
    ''' This function updates all prices in the user's stock to TREND. '''
    stock_list = __get_stock_as_array(api=api)
    # HACK: filter out a foil product
    stock_list = [x for x in stock_list if x['idProduct'] == 18204]
    # stock_list = [x for x in stock_list if x['idProduct'] == 261922]
    # stock_list = [x for x in stock_list if x['isFoil']]
    # 301546 expensive

    table_data = []
    uploadable_json = []
    total_price_diff = 0
    new_total_value = 0
    index = 0

    bar = progressbar.ProgressBar(max_value=len(stock_list))
    for article in stock_list:
        r = api.get_product(article['idProduct'])
        if not article['isFoil']:
            new_price = math.ceil(r['product']['priceGuide']['TREND'] * 4) / 4
        else:  # FOIL
            new_price = __get_foil_price(api, article['idProduct'])
        price_diff = new_price - article['price']
        new_total_value += new_price
        total_price_diff += price_diff
        table_data.append(
            [article['product']['enName'], article['isFoil'], article['price'], new_price, price_diff])
        uploadable_json.append({
            "idArticle": article['idArticle'],
            "price": new_price,
            "count": article['count']
        })
        index += 1
        bar.update(index)
    bar.finish()

    if len(uploadable_json) > 0:
        print('Best diffs:')  # table breaks because of progress bar rendering
        tp.table(sorted(table_data, key=lambda x: x[4], reverse=True)[:10], [
            'Name', 'Foil?', 'Old price', 'New price', 'Diff (sorted)'], width=32)
        print('Worst diffs:')
        tp.table(sorted(table_data, key=lambda x: x[4])[:10], [
            'Name', 'Foil?', 'Old price', 'New price', 'Diff (sorted)'], width=32)
        print('Total price difference: {} (new sum: {})'.format(
            str(round(total_price_diff, 2)), str(round(new_total_value))
        ))

        if __prompt("Do you want to update these prices?") == True:
            # Update articles on MKM
            api.set_stock(uploadable_json)
            print('Prices updated.')
        else:
            print('Prices not updated.')
    else:
        print('No prices to update.')


@api_wrapper
def show_top_10_expensive_articles_in_stock(api):
    stock_list = __get_stock_as_array(api=api)
    table_data = []

    for article in stock_list:
        table_data.append(
            [str(article['idProduct']), article['product']['enName'], article['price']])
    if len(stock_list) > 0:
        print('Top 10 most expensive articles in stock:')
        tp.table(sorted(table_data, key=lambda x: x[2], reverse=True)[:10], [
            'Product ID', 'Name', 'Price'], width=36)
    return None


def __get_foil_price(api, product_id):
    # NOTE: This is a rough algorithm, designed to be safe and not to sell aggressively.
    # 1) See filter parameters below.
    # 2) Set price to lowest + (median - lowest / 2), rounded to closest quarter Euro.
    # 3) Undercut price in own country if not contradicting 2)
    # 4) Never go below 0.25 for foils

    account_country = api.get_account()['account']['country']
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
        if article['seller']['address']['country'] == account_country:
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


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
