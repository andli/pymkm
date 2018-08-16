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
import yaml
import json


class PyMKM:
    config = None

    def __init__(self, config=None):
        if (config == None):
            print(">>> Loading config file...")
            try:
                self.config = yaml.load(open('config.yml'))
            except Exception as error:
                print(
                    "You must copy config_template.yml to config.yml and populate the fields.")
                print(error)
                sys.exit(0)
        else:
            self.config = config

    def __handle_errors(self, response):
        if (response.status_code == requests.codes.ok):
            return True
        else:
            raise ValueError("Error: Response status code {}: {}".format(
                str(response.status_code), str(response.content)))

    def __setup_service(self, url, mkmService):
        if (mkmService == None):
            if (self.config != None):
                mkmService = OAuth1Session(
                    self.config['app_token'],
                    client_secret=self.config['app_secret'],
                    resource_owner_key=self.config['access_token'],
                    resource_owner_secret=self.config['access_token_secret'],
                    realm=url
                )
                if (mkmService == None):
                    raise ConnectionError("Failed to establish OAuth session.")

        return mkmService

    def get_games(self, mkmService=None):
        url = 'https://api.cardmarket.com/ws/v1.1/output.json/games'
        mkmService = self.__setup_service(url, mkmService)

        print(">>> Getting all games...")
        r = mkmService.get(url)

        if (self.__handle_errors(r)):
            return r.json()

    def get_account(self, mkmService=None):
        url = 'https://api.cardmarket.com/ws/v1.1/output.json/account'
        mkmService = self.__setup_service(url, mkmService)

        print(">>> Getting account details...")
        r = mkmService.get(url)

        if (self.__handle_errors(r)):
            return r.json()

    def set_vacation_status(self, vacation_status=False, mkmService=None):
        url = 'https://api.cardmarket.com/ws/v1.1/output.json/account/vacation'
        mkmService = self.__setup_service(url, mkmService)

        print(">>> Setting vacation status to: " + str(vacation_status))
        r = mkmService.put(
            url, data={'isOnVacation': str(vacation_status).lower()})

        if (self.__handle_errors(r)):
            return r.json()

    def set_display_language(self, display_langauge=1, mkmService=None):
        """ 1: English, 2: French, 3: German, 4: Spanish, 5: Italian """
        url = 'https://api.cardmarket.com/ws/v1.1/output.json/account/language'
        mkmService = self.__setup_service(url, mkmService)

        print(">>> Setting display language to: " + str(display_langauge))
        r = mkmService.get(url + '/' + str(display_langauge).lower())

        if (self.__handle_errors(r)):
            return r.json()
