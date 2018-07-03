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


def main():
    """ Main entry point of the app """
    print(">>> Welcome to pymkm.")

    try:
        config=yaml.load(open('config.yml'))
    except Exception as error:
        print("You must copy config_template.yml to config.yml and populate the fields.")
        sys.exit(0)
    
    url = 'https://www.mkmapi.eu/ws/v1.1/account'

    mkmService = OAuth1Session(
        config['app_token'],
        client_secret=config['app_secret'],
        resource_owner_key=config['access_token'],
        resource_owner_secret=config['access_token_secret'],
        realm=url
        )
    
    r = mkmService.get(url)
    print(r.request.headers)
    print('---')
    print(r)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()