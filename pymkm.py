#!/usr/bin/env python3
"""
This is the main module responsible for calling the cardmarket.com API and returning JSON responses.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.3.0"
__license__ = "MIT"

import sys
import logging
import re
import requests
import json
from requests_oauthlib import OAuth1Session


class api_wrapper(object):

    def __init__(self, function):
        self.function = function

    def __call__(self, *arg, **kwargs):
        #print("DEBUG Entering", self.function.__name__)
        #print(arg)
        #print(kwargs)
        self.function(*arg, **kwargs)
        if 'api' in kwargs:
            api = kwargs['api']
            if (int(api.requests_max) > 0):
                print('>> Cardmarket.com requests used today: {}/{}'.format(
                    api.requests_count, api.requests_max))
        #print("DEBUG Exited", self.function.__name__)


class PyMKM:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    config = None
    base_url = 'https://api.cardmarket.com/ws/v2.0/output.json'
    conditions = ['MT', 'NM', 'EX', 'GD', 'LP', 'PL', 'PO']
    requests_max = 0
    requests_count = 0

    def __init__(self, config=None):
        if (config == None):
            logging.debug(">> Loading config file")
            try:
                self.config = json.load(open('config.json'))
            except Exception as error:
                print(
                    "You must copy config_template.json to config.json and populate the fields.")
                print(error)
                sys.exit(0)
        else:
            self.config = config

    def __handle_response(self, response):
        self.requests_count = response.headers['X-Request-Limit-Count']
        self.requests_max = response.headers['X-Request-Limit-Max']
        
        handled_codes = (
            requests.codes.ok,
            requests.codes.no_content,  # TODO: handle 204 better
            requests.codes.partial_content,
        )
        if (response.status_code in handled_codes):
            # TODO: use requests count to handle code 429, Too Many Requests
            return True
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
            max_items = int(re.search('\/(\d+)', response.headers['Content-Range']).group(1))
        except KeyError as err:
            logging.debug(">>> Header error finding content-range")
        return max_items

    def get_games(self, api=None):
        url = '{}/games'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting all games")
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_expansions(self, game_id, api=None):
        url = '{}/games/{}/expansions'.format(self.base_url, str(game_id))
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting all expansions for game id " + str(game_id))
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_cards_in_expansion(self, expansion_id, api=None):
        # Response: Expansion with Product objects
        url = '{}/expansions/{}/singles'.format(self.base_url, expansion_id)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(
            ">> Getting all cards for expansion id: " + str(expansion_id))
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_product(self, product_id, api=None):
        url = '{}/products/{}'.format(self.base_url, str(product_id))
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting data for product id " + str(product_id))
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_account(self, api=None):
        url = '{}/account'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting account details")
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_articles_in_shoppingcarts(self, api=None):
        url = '{}/stock/shoppingcart-articles'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting articles in other users' shopping carts")
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def set_vacation_status(self, vacation_status=False, api=None):
        # https://www.mkmapi.eu/ws/documentation/API_2.0:Account_Vacation
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
        # https://www.mkmapi.eu/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)
        if (start):
            url = url + '/' + str(start)
        mkm_oauth = self.__setup_service(url, api)

        logging.debug(">> Getting stock")
        r = mkm_oauth.get(url)

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

        if (self.__handle_response(r)):
            return r.json()

    def set_stock(self, payload=None, api=None):
        # https://www.mkmapi.eu/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)

        mkm_oauth = self.__setup_service(url, api)
        xml_payload = self.__json_to_xml(payload)

        logging.debug(">> Updating stock")
        r = mkm_oauth.put(url, data=xml_payload)

        if (self.__handle_response(r)):
            return r.json

    def get_articles(self, product_id, start=0, api=None, **kwargs):
        # https://www.mkmapi.eu/ws/documentation/API_2.0:Articles
        INCREMENT = 1000
        url = '{}/articles/{}'.format(self.base_url, product_id)
        mkm_oauth = self.__setup_service(url, api)

        # for key, value in kwargs.items():
        #    print("{} = {}".format(key, value))

        logging.debug(">> Getting articles on product: " + str(product_id))
        params = kwargs

        if (start > 0):
            params.update({'start': start, 'maxResults': INCREMENT})

        r = mkm_oauth.get(url, params=params)

        max_items = 0 
        if (r.status_code == requests.codes.partial_content 
        or r.status_code == requests.codes.no_content):
            max_items = self.__get_max_items_from_header(r)
            logging.debug('> Content-Range header: ' + r.headers['Content-Range'])
            logging.debug('> # articles in response: ' + str(len(r.json()['article'])))  
            if (start + INCREMENT >= max_items and self.__handle_response(r)):
                return r.json()['article']
            else:
                return r.json()['article'] + self.get_articles(product_id, start=start+INCREMENT, kwargs=kwargs)
