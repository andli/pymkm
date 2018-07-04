#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.1.0"
__license__ = "MIT"

import sys
import requests
from requests_oauthlib import OAuth1Session, OAuth1
import yaml

class PyMKM:
    config = None
    mkmService = None

    def __init__(self):
        print(">>> Loading config file.")
        try:
            self.config=yaml.load(open('config.yml'))
        except Exception as error:
            print("You must copy config_template.yml to config.yml and populate the fields.")
            sys.exit(0)

        #TODO: test if config is OK, if not throw exception

    def get_account(self):
        url = 'https://www.mkmapi.eu/ws/v1.1/output.json/account'
        if (self.config != None):
            self.mkmService = OAuth1Session(
            self.config['app_token'],
            client_secret=self.config['app_secret'],
            resource_owner_key=self.config['access_token'],
            resource_owner_secret=self.config['access_token_secret'],
            realm=url
            )

        r = self.mkmService.get(url)
        if (r.status_code == requests.codes.ok):
            return r.json()
        else:
            return r.code 
            #TODO: return someting better, throw exception?