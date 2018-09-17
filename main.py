#!/usr/bin/env python3
"""
This is a test program for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.3.0"
__license__ = "MIT"

from pymkm import PyMKM
from pymkm import api_wrapper
import json
import tableprint as tp
import progressbar
import statistics
from distutils.util import strtobool
from consolemenu import *
from consolemenu.items import *


def main():
    api = PyMKM()
    try:
        print('>>> Running api methods...')
        # print(api.get_account())
        # print(api.get_games())
        # print(api.set_display_language(1))
        # print(api.set_vacation_status(False))
        # print(api.get_articles_in_shoppingcarts())
        # print('# items: ' + str(len(api.get_stock(1))))
        # print(api.get_expansions(1)['expansion'][52]['idExpansion'])
        # print(str(len(api.get_cards_in_expansion(1599)['expansion'])))
        # with open('data.json', 'w') as outfile:
        #   json.dump(api.get_cards_in_expansion(1599), outfile)
        # print(api.get_product(272464))
        # with open('data.json', 'w') as outfile:
        #   json.dump(api.get_stock(), outfile)

        # print(__update_stock_prices_to_trend(api))
        # with open('data.json', 'w') as outfile:
        #json.dump(self.__show_prices_for_product(api, 319751), outfile)
        #__show_prices_for_product(294758, api=api)
        show_top_10_expensive_articles_in_stock(api=api)

    except ConnectionError as err:
        print(err)

    # Create the menu
    menu = ConsoleMenu("Welcome to the pymkm example app!", "It's fantastic.")
    menu.append_item(FunctionItem("List top 10 articles in stock",
                                  show_top_10_expensive_articles_in_stock, [api]))


@api_wrapper
def show_prices_for_product(product_id, api):
    articles = api.get_articles(product_id, **{
        # 'isFoil': 'true',
        # 'isAltered': 'false',
        'isSigned': 'false',
        'minCondition': 'PO',
        # 'idLanguage': 1
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
        print('Top 10 cheapest articles for chosen product')
        tp.table(sorted(table_data, key=lambda x: x[4], reverse=False)[:10],
                 ['Username', 'Country', 'Condition', 'Count', 'Price'], width=20)
        print('Total average price: ' +
              str(round(__calculate_average(table_data, 3, 4), 2)))
        print('Total median price: ' +
              str(round(__calculate_median(table_data, 3, 4), 2)))
        print('Total # of articles:' + str(len(table_data)))
    else:
        print('No prices found.')


@api_wrapper
def update_stock_prices_to_trend(api):
    ''' This function updates all prices in the user's stock to TREND. '''
    stock_list = __get_stock_as_array(api=api)
    # HACK: filter out a foil product
    #stock_list = [x for x in stock_list if x['idProduct'] == 319751]

    table_data = []
    uploadable_json = []
    total_price_diff = 0
    index = 0

    bar = progressbar.ProgressBar(max_value=len(stock_list))
    for article in stock_list:
        r = api.get_product(article['idProduct'])
        if not article['isFoil']:
            new_price = r['product']['priceGuide']['TREND']
            price_diff = new_price - article['price']
            total_price_diff += price_diff
            table_data.append(
                [article['product']['enName'], article['price'], new_price, price_diff])
            uploadable_json.append({
                "idArticle": article['idArticle'],
                "price": new_price,
                "count": article['count']
            })
        # else: #FOIL
            # print(r['product']['priceGuide'])
        index += 1
        bar.update(index)

    if len(uploadable_json) > 0:
        print('')  # table breaks because of progress bar rendering
        tp.table(sorted(table_data, key=lambda x: x[3], reverse=True)[:10], [
            'Name', 'Old price', 'New price', 'Diff (sorted)'], width=28)
        print('Total price difference: {}'.format(
            str(round(total_price_diff, 2))))

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


def __calculate_average(table, col_no_count, col_no_price):
    flat_array = []
    for row in table:
        flat_array.extend([row[col_no_price] * row[col_no_count]])
    return statistics.mean(flat_array)


def __calculate_median(table, col_no_count, col_no_price):
    flat_array = []
    for row in table:
        flat_array.extend([row[col_no_price] * row[col_no_count]])
    return statistics.median(flat_array)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
