#!/usr/bin/env python3
"""
This is a test program for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.3.0"
__license__ = "MIT"

from pymkm import PyMKM
import json
import tableprint as tp
import progressbar
from distutils.util import strtobool


def main():
    """ Main entry point of the app """
    tp.banner(" Welcome to the pymkm example app! ")

    api = PyMKM()
    try:
        print('>>> Testing api methods...')
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

        print(__update_stock_prices_to_trend(api))

    except ConnectionError as err:
        print(err)


def __update_stock_prices_to_trend(api):
    ''' This function updates all prices in the user's stock to TREND. '''
    try:
        d = api.get_stock()['article']
    except ValueError as err:
        print(err)

    keys = ['idArticle', 'idProduct', 'product', 'count', 'price', 'isFoil']
    stock_list = [{x: y for x, y in art.items() if x in keys} for art in d]

    table_data = []
    uploadable_json = []
    total_price_diff = 0
    index = 0

    bar = progressbar.ProgressBar(max_value=len(stock_list))
    for article in stock_list:
        if not article['isFoil']:
            r = api.get_product(article['idProduct'])
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
            index += 1
            bar.update(index)

    print('')  # HACK: table breaks because of progress bar rendering
    tp.table(sorted(table_data, key=lambda x: x[3], reverse=True)[:10], [
             'Name', 'Old price', 'New price', 'Diff (sorted)'], width=28)
    print('Total price difference: {}'.format(str(round(total_price_diff, 2))))

    if __prompt("Do you want to update these prices?") == True:
        # Update articles on MKM
        api.set_stock(uploadable_json)
        print('Prices updated.')
    else:
        print('Prices not updated.')


def __get_top_10_expensive_articles_in_stock(api):
    # TODO: use a fancy list printing lib to output the list
    return None


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
