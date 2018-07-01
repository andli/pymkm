#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Andreas Ehrlund"
__version__ = "0.1.0"
__license__ = "MIT"

from rauth import OAuth1Service
import yaml


def main():
    """ Main entry point of the app """
    print("Welcome to pymkm.")

    try:
        config=yaml.load(open('config.yml'))
        print (config)
    except Exception as error:
        print("You must copy config_template.yml to config.yml and populate the fields.")

    mkmService = OAuth1Service(
        name='mkm',
        consumer_key='', 
        consumer_secret='',
        request_token_url='', #https://api.twitter.com/oauth/request_token',
        access_token_url='', #https://api.twitter.com/oauth/access_token',
        authorize_url='', #https://api.twitter.com/oauth/authorize',
        base_url='' #https://api.twitter.com/1.1/'
        )

    

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()