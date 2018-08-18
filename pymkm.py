#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.1.0"
__license__ = "MIT"

import sys
import requests
from requests_oauthlib import OAuth1Session
import json


class PyMKM:
    config = None
    base_url = 'https://api.cardmarket.com/ws/v1.1/output.json'

    def __init__(self, config=None):
        if (config == None):
            print(">> Loading config file...")
            try:
                self.config = json.load(open('config.json'))
            except Exception as error:
                print(
                    "You must copy config_template.json to config.json and populate the fields.")
                print(error)
                sys.exit(0)
        else:
            self.config = config

    def __handle_errors(self, response):
        if (response.status_code == requests.codes.ok):
            return True
        elif (response.status_code == requests.codes.partial_content):
            return True #TODO: handle 206 better
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

    def get_games(self, mkmOAuth=None):
        url = self.base_url + '/games'
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting all games...")
        r = mkmOAuth.get(url)

        if (self.__handle_errors(r)):
            return r.json()

    def get_account(self, mkmOAuth=None):
        url = self.base_url + '/account'
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting account details...")
        r = mkmOAuth.get(url)

        if (self.__handle_errors(r)):
            return r.json()

    def set_vacation_status(self, vacation_status=False, mkmOAuth=None):
        url = self.base_url + '/account/vacation/' + \
            str(vacation_status).lower()
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Setting vacation status to: " + str(vacation_status))
        r = mkmOAuth.put(url)

        if (self.__handle_errors(r)):
            return r.json()

    def set_display_language(self, display_langauge=1, mkmOAuth=None):
        # 1: English, 2: French, 3: German, 4: Spanish, 5: Italian
        url = self.base_url + '/account/language/' + \
            str(display_langauge).lower()
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Setting display language to: " + str(display_langauge))
        r = mkmOAuth.put(url)

        if (self.__handle_errors(r)):
            return r.json()

    def get_stock(self, start=None, mkmOAuth=None):
        url = self.base_url + '/stock'
        if (start):
            url = url + '/' + str(start)
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting stock...")
        r = mkmOAuth.get(url)

        if (self.__handle_errors(r)):
            return r.json()

    def get_shoppingcart_articles(self, mkmOAuth=None):
        url = self.base_url + '/stock/shoppingcart-articles'
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting articles in other users' shopping carts...")
        r = mkmOAuth.get(url)

        if (self.__handle_errors(r)):
            return r.json()
