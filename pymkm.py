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

    def get_account(self, mkmService=None):
        url = 'https://www.mkmapi.eu/ws/v1.1/output.json/account'
        if (mkmService == None):
            if (self.config != None):
                print(">>> Getting account details...")
                mkmService = OAuth1Session(
                    self.config['app_token'],
                    client_secret=self.config['app_secret'],
                    resource_owner_key=self.config['access_token'],
                    resource_owner_secret=self.config['access_token_secret'],
                    realm=url
                )
                if (mkmService == None):
                    raise ConnectionError("Failed to establish OAuth session.")

        r = mkmService.get(url)

        if (r.status_code == requests.codes.ok):
            return r.json()
        else:
            raise ValueError("Error: HTTP "+str(r.status_code))
