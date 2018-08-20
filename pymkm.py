#!/usr/bin/env python3
"""
This is the main module responsible for calling the cardmarket.com API and returning JSON responses.
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.2.0"
__license__ = "MIT"

import sys
import re
import requests
import json
from requests_oauthlib import OAuth1Session


class PyMKM:
    config = None
    base_url = 'https://api.cardmarket.com/ws/v2.0/output.json'

    def __init__(self, config=None):
        if (config == None):
            print(">> Loading config file")
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
        handled_codes = (
            requests.codes.ok,
            requests.codes.no_content,
            requests.codes.partial_content,
        )
        if (response.status_code in handled_codes):
            return True
        else:
            raise ValueError("Error: Response status code {}: {}".format(
                str(response.status_code), str(response.content)))

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

    def __get_max_items_from_header(self, r):
        max_items = 0
        try:
            max_items = int(
                re.search('\/(\d+)', r.headers['Content-Range']).group(1))
        except AttributeError:
            # AAA, ZZZ not found in the original string
            found = ''  # apply your error handling
        return max_items

    def get_games(self, mkm_oauth=None):
        url = '{}/games'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting all games")
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_expansions(self, game_id, mkm_oauth=None):
        url = '{}/games/{}/expansions'.format(self.base_url, str(game_id))
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting all expansions for game id " + str(game_id))
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_cards_in_expansion(self, expansion_id, mkm_oauth=None):
        # Response: Expansion with Product objects
        url = '{}/expansions/{}/singles'.format(self.base_url, expansion_id)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting all cards for expansion id: " + str(expansion_id))
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()
    
    def get_product(self, product_id, mkm_oauth=None):
        url = '{}/products/{}'.format(self.base_url, str(product_id))
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting all expansions for game id " + str(product_id))
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_account(self, mkm_oauth=None):
        url = '{}/account'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting account details")
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_articles_in_shoppingcarts(self, mkm_oauth=None):
        url = '{}/stock/shoppingcart-articles'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting articles in other users' shopping carts")
        r = mkm_oauth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def set_vacation_status(self, vacation_status=False, mkm_oauth=None):
        # https://www.mkmapi.eu/ws/documentation/API_2.0:Account_Vacation
        url = '{}/account/vacation'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Setting vacation status to: " + str(vacation_status))
        r = mkm_oauth.put(
            url, params={'onVacation': str(vacation_status).lower()})
        # cancelOrders
        # relistItems

        if (self.__handle_response(r)):
            return r.json()

    def set_display_language(self, display_langauge=1, mkm_oauth=None):
        # 1: English, 2: French, 3: German, 4: Spanish, 5: Italian
        url = '{}/account/language'.format(self.base_url)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Setting display language to: " + str(display_langauge))
        r = mkm_oauth.put(url, params={'idDisplayLanguage': display_langauge})

        if (self.__handle_response(r)):
            return r.json()

    def get_stock(self, start=None, mkm_oauth=None):
        # https://www.mkmapi.eu/ws/documentation/API_2.0:Stock_Management
        url = '{}/stock'.format(self.base_url)
        if (start):
            url = url + '/' + str(start)
        mkm_oauth = self.__setup_service(url, mkm_oauth)

        print(">> Getting stock")
        r = mkm_oauth.get(url)

        max_items = self.__get_max_items_from_header(r)

        if (start > max_items or r.status_code == requests.codes.no_content):
            # terminate recursion
            """ NOTE: funny thing is, even though the API talks about it, 
            it never responds with 204 (no_content). Therefore we check for 
            exceeding content-range instead."""
            return []

        if (r.status_code == requests.codes.partial_content):
            print('> ' + r.headers['Content-Range'])
            #print('# articles in response: ' + str(len(r.json()['article'])))
            return r.json()['article'] + self.get_stock(start+100)

        if (self.__handle_response(r)):
            return r.json()
