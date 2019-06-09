#!/usr/bin/env python3
"""
This is the main module responsible for calling the cardmarket.com API and returning JSON responses.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.9.0"
__license__ = "MIT"

import sys
import logging
import re
import requests
import json
import urllib.parse
from requests_oauthlib import OAuth1Session
from requests import ConnectionError


def api_wrapper(func):

    def wrapper(*arg, **kwargs):
        logging.debug(f">> Entering {func.__name__}")

        return_value = func(*arg, **kwargs)
        if 'api' in kwargs:
            api = kwargs['api']
            if (int(api.requests_max) > 0):
                print('\n>> Cardmarket.com requests used today: {}/{}\n'.format(
                    api.requests_count, api.requests_max))
        logging.debug(">> Exited {}".format(func.__name__))
        return return_value
    return wrapper


class NoResultsError(Exception):
    def __init__(self, message, errors=None):
        if (message == None):
            message = 'No results found.'
        super().__init__(message)

        self.errors = errors


class PyMkmApi:
    logging.basicConfig(stream=sys.stderr, level=logging.WARN)
    config = None
    base_url = 'https://api.cardmarket.com/ws/v2.0/output.json'
    conditions = ['MT', 'NM', 'EX', 'GD', 'LP', 'PL', 'PO']
    languages = ['English', 'French', 'German', 'Spanish', 'Italian', 'S-Chinese', 'Japanese',
                 'Portugese', 'Russian', 'Korean', 'T-Chinese', 'Dutch', 'Polish', 'Czech', 'Hungarian']
    requests_max = 0
    requests_count = 0

    def __init__(self, config=None):
        if (config == None):
            logging.debug(">> Loading config file")
            try:
                self.config = json.load(open('config.json'))
            except FileNotFoundError:
                logging.error("You must copy config_template.json to config.json and populate the fields.")
                sys.exit(0)
        else:
            self.config = config

    def __handle_response(self, response):
        try:
            self.requests_count = response.headers['X-Request-Limit-Count']
            self.requests_max = response.headers['X-Request-Limit-Max']
        except (AttributeError, KeyError) as err:
            logging.debug(">> Attribute not found in header: {}".format(err))

        handled_codes = (
            requests.codes.ok,
            requests.codes.partial_content,
            requests.codes.temporary_redirect,
        )
        if (response.status_code in handled_codes):
            # TODO: use requests count to handle code 429, Too Many Requests
            return True
        elif (response.status_code == requests.codes.no_content):
            raise NoResultsError('No results found.')
        else:
            raise requests.exceptions.ConnectionError(response)

    def __setup_service(self, url, oauth):
        if (oauth == None):
            if (self.config != None):
                oauth = OAuth1Session(
                    self.config['app_token'],
                    client_secret=self.config['app_secret'],
                    resource_owner_key=self.config['access_token'],
                    resource_owner_secret=self.config['access_token_secret'],
                    realm=url
                )

                if (oauth == None):
                    raise ConnectionError("Failed to establish OAuth session.")

        return oauth

    def __json_to_xml(self, json_input):
        from dicttoxml import dicttoxml

        xml = dicttoxml(json_input, custom_root='request',
                        attr_type=False, item_func=lambda x: 'article')
        return xml.decode('utf-8')

    def __get_max_items_from_header(self, response):
        max_items = 0
        try:
            max_items = int(
                re.search('\/(\d+)', response.headers['Content-Range']).group(1))
        except KeyError as err:
            logging.debug(">>> Header error finding content-range")
        return max_items

    @staticmethod
    def __chunks(l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n]

    def get_games(self, api=None):
        url = '{}/games'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting all games")
        r = self.mkm_request(mkm_oauth, url)

        if (r):
            return r.json()

    def mkm_request(self, mkm_oauth, url):
        try:
            r = mkm_oauth.get(url, allow_redirects=False)
            self.__handle_response(r)
        except requests.exceptions.ConnectionError as err:
            logging.debug(err)
        
        return r

    def get_expansions(self, game_id, api=None):
        url = '{}/games/{}/expansions'.format(self.base_url, str(game_id))
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting all expansions for game id " + str(game_id))
        r = self.mkm_request(mkm_oauth, url)

        if (r):
            return r.json()

    def get_cards_in_expansion(self, expansion_id, api=None):
        # Response: Expansion with Product objects
        url = '{}/expansions/{}/singles'.format(self.base_url, expansion_id)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(
            ">> Getting all cards for expansion id: " + str(expansion_id))
        r = self.mkm_request(mkm_oauth, url)

        if (r):
            return r.json()

    def get_product(self, product_id, api=None):
        url = '{}/products/{}'.format(self.base_url, str(product_id))
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting data for product id " + str(product_id))
        r = self.mkm_request(mkm_oauth, url)

        if (r):
            return r.json()

    def get_account(self, api=None):
        url = '{}/account'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting account details")
        r = self.mkm_request(mkm_oauth, url)

        if (r):
            return r.json()

    def get_articles_in_shoppingcarts(self, api=None):
        url = '{}/stock/shoppingcart-articles'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting articles in other users' shopping carts")
        r = self.mkm_request(mkm_oauth, url)

        if (r):
            return r.json()

    def set_vacation_status(self, vacation_status=False, api=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Account_Vacation
        url = '{}/account/vacation'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Setting vacation status to: " + str(vacation_status))
        r = mkm_oauth.put(
            url, params={'onVacation': str(vacation_status).lower()})
        # cancelOrders
        # relistItems

        if (self.__handle_response(r)):
            return r.json()

    def set_display_language(self, display_langauge=1, api=None):
        # 1: English, 2: French, 3: German, 4: Spanish, 5: Italian
        url = '{}/account/language'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Setting display language to: " +
                      str(display_langauge))
        r = mkm_oauth.put(url, params={'idDisplayLanguage': display_langauge})

        if (self.__handle_response(r)):
            return r.json()

    def get_stock(self, start=None, api=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)
        if (start):
            url = url + '/' + str(start)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting stock")
        r = self.mkm_request(mkm_oauth, url)

        if (r.status_code == requests.codes.temporary_redirect):
            return self.get_stock(1)
        
        if (start is not None):
            max_items = self.__get_max_items_from_header(r)
    
            if (start > max_items or r.status_code == requests.codes.no_content):
                # terminate recursion
                """ NOTE: funny thing is, even though the API talks about it,
                it never responds with 204 (no_content). Therefore we check for
                exceeding content-range instead."""
                return []

            if (r.status_code == requests.codes.partial_content):
                print('> ' + r.headers['Content-Range'])
                # print('# articles in response: ' + str(len(r.json()['article'])))
                return r.json()['article'] + self.get_stock(start+100)

        if (r):
            return r.json()['article']

    def add_stock(self, payload=None, api=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)

        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Adding stock")
        chunked_list = list(self.__chunks(payload, 100))
        for chunk in chunked_list:
            xml_payload = self.__json_to_xml(chunk)
            r = mkm_oauth.post(url, data=xml_payload)

        # TODO: Only considers the last response.
        if (self.__handle_response(r)):
            return r.json

    def set_stock(self, payload=None, api=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)

        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Updating stock")
        chunked_list = list(self.__chunks(payload, 100))
        for chunk in chunked_list:
            xml_payload = self.__json_to_xml(chunk)
            r = mkm_oauth.put(url, data=xml_payload)

        # TODO: Only considers the last response.
        if (self.__handle_response(r)):
            return r.json

    def delete_stock(self, payload=None, api=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)

        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Deleting stock")
        chunked_list = list(self.__chunks(payload, 100))
        for chunk in chunked_list:
            xml_payload = self.__json_to_xml(chunk)
            r = mkm_oauth.delete(url, data=xml_payload)

        # TODO: Only considers the last response.
        if (self.__handle_response(r)):
            return r.json

    def get_articles(self, product_id, start=0, api=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Articles
        INCREMENT = 1000
        url = '{}/articles/{}'.format(self.base_url, product_id)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting articles on product: " + str(product_id))
        params = kwargs

        if (start > 0):
            params.update({'start': start, 'maxResults': INCREMENT})

        r = mkm_oauth.get(url, params=params)

        max_items = 0
        if (r.status_code == requests.codes.partial_content):
            max_items = self.__get_max_items_from_header(r)
            logging.debug('> Content-Range header: ' +
                          r.headers['Content-Range'])
            logging.debug('> # articles in response: ' +
                          str(len(r.json()['article'])))
            if (start + INCREMENT >= max_items and self.__handle_response(r)):
                return r.json()['article']
            else:
                return r.json()['article'] + self.get_articles(product_id, start=start+INCREMENT, **kwargs)
        elif (r.status_code == requests.codes.no_content):
            raise NoResultsError('No products found in stock.')
        elif (r.status_code == requests.codes.ok):
            return r.json()['article']
        else:
            raise ConnectionError(r)

    def find_product(self, search, api=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Find_Products

        url = '{}/products/find'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Finding product for search string: " + str(search))

        params = kwargs
        if 'search' not in kwargs:
            params['search'] = search

        r = mkm_oauth.get(url, params=params)

        if (self.__handle_response(r)):
            return r.json()

    def find_stock_article(self, name, game_id, api=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Find_Articles

        url = '{}/stock/articles/{}/{}'.format(
            self.base_url, urllib.parse.quote(name), game_id)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Finding articles in stock: " + str(name))

        r = self.mkm_request(mkm_oauth, url)

        if (r.status_code == requests.codes.no_content):
            raise NoResultsError('No articles found.')
        elif (r.status_code == requests.codes.ok):
            return r.json()['article']
        else:
            raise ConnectionError(r)
