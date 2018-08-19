#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.1.0"
__license__ = "MIT"

import sys
import re
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

    def get_games(self, mkmOAuth=None):
        url = self.base_url + '/games'
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting all games...")
        r = mkmOAuth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_account(self, mkmOAuth=None):
        url = self.base_url + '/account'
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting account details...")
        r = mkmOAuth.get(url)

        if (self.__handle_response(r)):
            return r.json()

    def set_vacation_status(self, vacation_status=False, mkmOAuth=None):
        url = self.base_url + '/account/vacation/' + \
            str(vacation_status).lower()
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Setting vacation status to: " + str(vacation_status))
        r = mkmOAuth.put(url)

        if (self.__handle_response(r)):
            return r.json()

    def set_display_language(self, display_langauge=1, mkmOAuth=None):
        # 1: English, 2: French, 3: German, 4: Spanish, 5: Italian
        url = self.base_url + '/account/language/' + \
            str(display_langauge).lower()
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Setting display language to: " + str(display_langauge))
        r = mkmOAuth.put(url)

        if (self.__handle_response(r)):
            return r.json()

    def get_stock(self, start=None, mkmOAuth=None):
        url = self.base_url + '/stock'
        if (start):
            url = url + '/' + str(start)
        mkmOAuth = self.__setup_service(url, mkmOAuth)

        print(">> Getting stock...")
        r = mkmOAuth.get(url)

        max_items = self.__get_max_items_from_header(r)  

        if (r.status_code == requests.codes.no_content or start > max_items):
            # terminate
            print("STOP")
            return []
        elif (r.status_code == requests.codes.partial_content):
            print('> ' + r.headers['Content-Range'])
            articles = r.json()['article']
            return articles.extend(self.get_stock(start+100))
        
        # if (self.__handle_response(r)):
            # return r.json()

    def __get_max_items_from_header(self, r):
        max_items=0
        try:
            max_items=int(
                re.search('\/(\d+)', r.headers['Content-Range']).group(1))
        except AttributeError:
            # AAA, ZZZ not found in the original string
            found=''  # apply your error handling
        return max_items


    def get_shoppingcart_articles(self, mkmOAuth=None):
        url=self.base_url + '/stock/shoppingcart-articles'
        mkmOAuth=self.__setup_service(url, mkmOAuth)

        print(">> Getting articles in other users' shopping carts...")
        r=mkmOAuth.get(url)

        if (self.__handle_response(r)):
            return r.json()
