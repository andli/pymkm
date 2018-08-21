#!/usr/bin/env python3
"""
This is a test program for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.2.0"
__license__ = "MIT"

from pymkm import PyMKM
import json


def main():
    """ Main entry point of the app """
    print(">>> Welcome to a pymkm test app.")

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

        
    except ValueError as err:
        print(err)
    
    __update_stock_prices_to_trend(api)

def __update_stock_prices_to_trend(api):
    try:
        d = api.get_stock()['article']
    except ValueError as err:
        print(err)

    keys = ['idArticle', 'idProduct', 'price', 'isFoil']
    stock_list = [{x:y for x,y in art.items() if x in keys} for art in d]

    for article in stock_list:
        if not article['isFoil']:
            r = api.get_product(article['idProduct'])
            article.update({'newPrice': r['product']['priceGuide']['TREND']})
            print(article)
        break


    #print(stock_list)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
