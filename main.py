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
import csv
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
            "Update price for a card",
            "List competition for a card",
            "Show top 20 expensive items in stock",
            "Show account info",
            "Clear entire stock (WARNING)",
            "Import stock from .\list.csv"
        ]
        __print_menu(menu_items)

        choice = input("Action number: ")

        if choice == "1":
            try:
                update_stock_prices_to_trend(api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "2":
            search_string = __prompt_string('Search card name')
            try:
                update_product_to_trend(search_string, api=api)
            except ConnectionError as err:
                print(err)
        elif choice == "3":
            is_foil = False
            search_string = __prompt_string('Search card name')
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
        elif choice == "6":
            try:
                clear_entire_stock(api=api)
            except ConnectionError as err:
                print(err)
                print(err)
        elif choice == "7":
            try:
                import_from_csv(api=api)
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


def import_from_csv(api):
    print("Note the required format: Card, Set name, Quantity, Foil, Language (with header row).")
    print("Cards are added in condition NM.")
    problem_cards = []
    with open('list.csv', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        index = 0
        bar = progressbar.ProgressBar(max_value=sum(1 for row in csv_reader))
        csvfile.seek(0)
        for row in csv_reader:
            if index > 0:
                (name, set_name, count, foil, language, *other) = row
                if (all(v is not '' for v in [name, set_name, count])):
                    possible_products = api.find_product(name)['product']
                    product_match = [x for x in possible_products if x['expansionName']
                                     == set_name and x['categoryName'] == "Magic Single"]
                    if len(product_match) == 0:
                        problem_cards.append(row)
                    elif len(product_match) == 1:
                        foil = (True if foil == 'Foil' else False)
                        langauge_id = (
                            1 if language == '' else api.languages.index(language) + 1)
                        price = _get_price_for_product(
                            product_match[0]['idProduct'], foil, langauge_id, api)
                        card = {
                            'idProduct': product_match[0]['idProduct'],
                            'idLanguage': langauge_id,
                            'count': count,
                            'price': str(price),
                            'condition': 'NM',
                            'isFoil': ('true' if foil else 'false')
                        }
                        api.add_stock([card])
                    else:
                        problem_cards.append(row)

            index += 1
            bar.update(index)
        bar.finish()
    if len(problem_cards) > 0:
        try:
            with open('failed_imports.csv', 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerows(problem_cards)
            print('Wrote failed imports to failed_imports.csv')
            print(
                'Most failures are due to mismatching set names or multiple versions of cards.')
        except Exception as err:
            print(err.value)


@api_wrapper
def clear_entire_stock(api):
    stock_list = get_stock_as_array(api=api)
    if __prompt("Do you REALLY want to clear your entire stock ({} items)?".format(len(stock_list))) == True:

        # for article in stock_list:
            #article['count'] = 0
        delete_list = [{'count': x['count'], 'idArticle': x['idArticle']}
                       for x in stock_list]

        api.delete_stock(delete_list)
        print('Stock cleared.')
    else:
        print('Aborted.')


@api_wrapper
def show_account_info(api):
    pp = pprint.PrettyPrinter()
    pp.pprint(api.get_account())


@api_wrapper
def search_for_product(search_string, is_foil, api):
    try:
        products = api.find_product(search_string, **{
            # 'exact ': 'true',
            'idGame': 1,
            'idLanguage': 1,
            # TODO: Add Partial Content support
        })['product']

        stock_list_products = [x['idProduct']
                               for x in get_stock_as_array(api=api)]
        products = [x for x in products if x['idProduct']
                    in stock_list_products]

        if len(products) > 1:
            product = _select_from_list_of_products(
                [i for i in products if i['categoryName'] == 'Magic Single'])
        else:
            product = products[0]

        show_competition_for_product(
            product['idProduct'], product['enName'], is_foil, api=api)
    except Exception as err:
        print(err)


def _select_from_list_of_products(products):
    index = 1
    for product in products:
        print('{}: {} [{}] {}'.format(index, product['enName'],
                                      product['expansionName'], product['rarity']))
        index += 1
    choice = int(input("Choose card: "))
    return products[choice - 1]


def _select_from_list_of_articles(articles):
    index = 1
    for article in articles:
        product = article['product']
        print('{}: {} [{}] {}'.format(index, product['enName'],
                                      product['expansion'], product['rarity']))
        index += 1
    choice = int(input("Choose card: "))
    return articles[choice - 1]


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
        articles = api.find_stock_article(search_string, 1)
    except Exception as err:
        print(err)

    if len(articles) > 1:
        article = _select_from_list_of_articles(articles)
    else:
        article = articles[0]
        print('Found: {} [{}].'.format(article['product']
                                       ['enName'], article['product']['expansion']))
    r = _get_price_for_single_article(article, api)

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
            os.remove(PRICE_CHANGES_FILE)
            update_stock_prices_to_trend(api)

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
        os.remove(PRICE_CHANGES_FILE)


def _calculate_new_prices_for_stock(api):
    stock_list = get_stock_as_array(api=api)
    # HACK: filter out a foil product
    # stock_list = [x for x in stock_list if x['isFoil']]

    result_json = []
    total_price = 0
    index = 0

    bar = progressbar.ProgressBar(max_value=len(stock_list))
    for article in stock_list:
        updated_article = _get_price_for_single_article(article, api)
        if updated_article:
            result_json.append(updated_article)
            total_price += updated_article.get('price')
        else:
            total_price += article.get('price')
        index += 1
        bar.update(index)
    bar.finish()

    print('Total stock value: {}'.format(str(total_price)))
    return result_json


def _get_price_for_single_article(article, api):
    #TODO: compare prices also for signed cards, like foils
    if not article.get('isSigned') or True: # keep prices for signed cards fixed
        new_price = _get_price_for_product(
            article['idProduct'], article['isFoil'], api, article['language']['idLanguage'])
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


@api_wrapper
def _get_price_for_product(product_id, is_foil, api, language_id=1):
    if not is_foil:
        r = api.get_product(product_id)
        found_price = math.ceil(r['product']['priceGuide']['TREND'] * 4) / 4
    else:
        found_price = __get_foil_price(api, product_id, language_id)

    if found_price == None:
        raise ValueError('No price found!')
    else:
        return found_price


def _display_price_changes_table(changes_json):
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

    print('\nTotal price difference: {}.'.format(
        str(round(sum(item['price_diff'] for item in changes_json), 2))
        ))


def _draw_price_changes_table(sorted_best):
    print(tb.tabulate(
        [[item['name'], u'\u2713' if item['foil'] else '', item['old_price'], item['price'],
            item['price_diff']] for item in sorted_best],
        headers=['Name', 'Foil?', 'Old price', 'New price', 'Diff'],
        tablefmt="simple"
    ))


@api_wrapper
def show_top_expensive_articles_in_stock(num_articles, api):
    stock_list = get_stock_as_array(api=api)
    table_data = []
    total_price = 0

    for article in stock_list:
        name = article['product']['enName']
        expansion = article.get('product').get('expansion')
        foil = article.get('isFoil')
        language_code = article.get('language')
        language_name = language_code.get('languageName')
        price = article.get('price')
        table_data.append(
            [name, expansion, u'\u2713' if foil else '', language_name if language_code != 1 else '', price])
        total_price += price
    if len(stock_list) > 0:
        print('Top {} most expensive articles in stock:\n'.format(str(num_articles)))
        print(tb.tabulate(sorted(table_data, key=lambda x: x[4], reverse=True)[:num_articles],
                          headers=['Name', 'Expansion', 'Foil?', 'Language', 'Price'],
                          tablefmt="simple")
              )
        print('\nTotal stock value: {}'.format(str(total_price)))
    return None


def __get_foil_price(api, product_id, language_id):
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
        'idLanguage': language_id
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


def get_stock_as_array(api):
    d = api.get_stock()

    keys = ['idArticle', 'idProduct', 'product', 'count', 
            'price', 'isFoil', 'isSigned', 'language']  # TODO: [language][languageId]
    stock_list = [{x: y for x, y in article.items() if x in keys} for article in d]
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
