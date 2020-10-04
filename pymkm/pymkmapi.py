#!/usr/bin/env python3
"""
This is the main module responsible for calling the cardmarket.com API and returning JSON responses.
"""

__author__ = "Andreas Ehrlund"
__version__ = "2.0.0"
__license__ = "MIT"

import asyncio
import copy
import json
import logging
import logging.handlers
import re
import sys
import urllib.parse

import requests
from authlib.integrations.httpx_client import AsyncOAuth1Client, OAuth1Auth
from requests import ConnectionError
from requests_oauthlib import OAuth1Session


class CardmarketError(Exception):
    def __init__(self, message, url=None, errors=None):
        if message is None:
            message = "No results found."
        super().__init__(message)

        self.errors = errors
        self.url = url

    def mkm_msg(self):
        prefix_string = "[Cardmarket API] "
        error_string = ""
        if isinstance(self.args[0], str):
            error_string = self.args[0]
        else:
            error_string = self.args[0].get("mkm_error_description")
        return prefix_string + error_string


class PyMkmApi:
    logger = None
    config = None
    base_url = "https://api.cardmarket.com/ws/v2.0/output.json"
    conditions = ["MT", "NM", "EX", "GD", "LP", "PL", "PO"]
    languages = [
        "English",
        "French",
        "German",
        "Spanish",
        "Italian",
        "S-Chinese",
        "Japanese",
        "Portuguese",
        "Russian",
        "Korean",
        "T-Chinese",
        "Dutch",
        "Polish",
        "Czech",
        "Hungarian",
    ]

    def __init__(self, config=None, logger=None):

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh = logging.handlers.RotatingFileHandler(
                f"log_pymkm.log", maxBytes=500000, backupCount=2
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            sh = logging.StreamHandler()
            sh.setLevel(logging.ERROR)
            sh.setFormatter(formatter)
            self.logger.addHandler(sh)

        self.requests_max = 0
        self.requests_count = 0

        if config is None:
            self.logger.debug(">> Loading config file")
            try:
                self.config = json.load(open("config.json"))
            except FileNotFoundError:
                self.logger.error(
                    "You must copy config_template.json to config.json and populate the fields."
                )
                sys.exit(0)
        else:
            self.config = config

        self.set_api_quota_attributes()

    def __handle_response(self, response):
        handled_codes = (
            requests.codes.ok,
            requests.codes.partial_content,
        )
        if response.status_code in handled_codes:
            self.__read_request_limits_from_header(response)

            # TODO: use requests count to handle code 429, Too Many Requests
            return True
        elif response.status_code == requests.codes.temporary_redirect:
            raise CardmarketError(response.json())
        elif response.status_code == requests.codes.no_content:
            raise CardmarketError("No results found.", url=response.request.url)
        elif response.status_code == requests.codes.bad_request:
            raise CardmarketError(response.json())
        elif response.status_code == requests.codes.not_found:
            raise CardmarketError(response.json())
        else:
            raise requests.exceptions.ConnectionError(response)

    def __read_request_limits_from_header(self, response):
        try:
            self.requests_count = response.headers["X-Request-Limit-Count"]
            self.requests_max = response.headers["X-Request-Limit-Max"]
        except (AttributeError, KeyError) as err:
            self.logger.debug(">> Attribute not found in header: {}".format(err))

    def __setup_service(self, url, provided_oauth):
        if provided_oauth is not None:
            return provided_oauth
        else:
            if self.config is not None:
                oauth = OAuth1Session(
                    self.config["app_token"],
                    client_secret=self.config["app_secret"],
                    resource_owner_key=self.config["access_token"],
                    resource_owner_secret=self.config["access_token_secret"],
                    realm=url,
                )

                if oauth is None:
                    raise ConnectionError("Failed to establish OAuth session.")
                else:
                    return oauth

    def __json_to_xml(self, json_input):
        from dicttoxml import dicttoxml

        xml = dicttoxml(
            json_input,
            custom_root="request",
            attr_type=False,
            item_func=lambda x: "article",
        )
        return xml.decode("utf-8")

    def __get_max_items_from_header(self, response):
        max_items = 0
        if not response.status_code == requests.codes.no_content:
            try:
                max_items = int(
                    re.search("\/(\d+)", response.headers["Content-Range"]).group(1)
                )
            except KeyError as err:
                self.logger.debug(">>> Header error finding content-range")
            return max_items

    def set_api_quota_attributes(self, provided_oauth=None):
        # Use a 400 to get the response headers
        url = "{}/games".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.info(">> Getting request quotas")
        r = self.mkm_request(mkm_oauth, url)

    def get_language_code_from_string(self, language_string):
        if language_string in self.languages:
            return self.languages.index(language_string) + 1
        else:
            self.logger.error(">>> Configuration error, review config file.")
            raise Exception("Configuration error (search_filters, language).")

    @staticmethod
    def __chunks(l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i : i + n]

    def get_games(self, provided_oauth=None):
        url = "{}/games".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting all games")
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    def mkm_request(self, mkm_oauth, url, params=None):
        try:
            r = mkm_oauth.get(url, params=params, allow_redirects=False)
            # However, you should switch off the behaviour to automatically
            # redirect to the given request URI, because a new Authorization
            # header needs to be compiled for the redirected resource. (MKM API docs)
            self.__handle_response(r)
            return r
        except CardmarketError as err:
            print(err.mkm_msg())
            # sys.exit(0)
        except Exception as err:
            print(f"\n>> Cardmarket connection error: {err} for {url}")
            self.logger.error(f"{err} for {url}")
            # sys.exit(0)

    def get_expansions(self, game_id, provided_oauth=None):
        url = "{}/games/{}/expansions".format(self.base_url, str(game_id))
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting all expansions for game id " + str(game_id))
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    def get_cards_in_expansion(self, expansion_id, provided_oauth=None):
        # Response: Expansion with Product objects
        url = "{}/expansions/{}/singles".format(self.base_url, expansion_id)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting all cards for expansion id: " + str(expansion_id))
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    def get_product(self, product_id, provided_oauth=None):
        url = "{}/products/{}".format(self.base_url, str(product_id))
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting data for product id " + str(product_id))
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    async def fetch(self, sem, client, url, uri):
        async with sem:
            client_auth = copy.copy(client.auth)
            client_auth.realm = url
            resp = await client.get(url, auth=client_auth)
            return resp.json()  # TODO: handle non-good responses...?

    async def get_items(self, item_type, item_id_list):
        async with AsyncOAuth1Client(
            client_id=self.config["app_token"],
            client_secret=self.config["app_secret"],
            token=self.config["access_token"],
            token_secret=self.config["access_token_secret"],
        ) as client:
            tasks = []
            sem = asyncio.Semaphore(100)
            for item_id in item_id_list:
                tasks.append(
                    asyncio.ensure_future(
                        self.fetch(
                            sem,
                            client,
                            f"{self.base_url}/{item_type}/{str(item_id)}",
                            f"{self.base_url}/{item_type}/",
                        )
                    )
                )
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            return responses

    def get_items_async(self, item_type, item_id_list):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_items(item_type, item_id_list))

    def get_metaproduct(self, metaproduct_id, provided_oauth=None):
        # https://api.cardmarket.com/ws/v2.0/metaproducts/:idMetaproduct
        url = f"{self.base_url}/metaproducts/{str(metaproduct_id)}"
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting data for metaproduct id " + str(metaproduct_id))
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    def get_account(self, provided_oauth=None):
        url = "{}/account".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting account details")
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    def get_articles_in_shoppingcarts(self, provided_oauth=None):
        url = "{}/stock/shoppingcart-articles".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting articles in other users' shopping carts")
        r = self.mkm_request(mkm_oauth, url)

        if r:
            return r.json()

    def set_vacation_status(self, vacation_status=False, provided_oauth=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Account_Vacation
        url = "{}/account/vacation".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Setting vacation status to: " + str(vacation_status))
        r = mkm_oauth.put(url, params={"onVacation": str(vacation_status).lower()})
        # cancelOrders
        # relistItems

        if self.__handle_response(r):
            return r.json()

    def set_display_language(self, display_language=1, provided_oauth=None):
        # 1: English, 2: French, 3: German, 4: Spanish, 5: Italian
        url = "{}/account/language".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Setting display language to: " + str(display_language))
        r = mkm_oauth.put(url, params={"idDisplayLanguage": display_language})

        if self.__handle_response(r):
            return r.json()

    def get_stock(self, start=None, provided_oauth=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        self.logger.debug(f"-> get_stock start={start}")
        url = "{}/stock".format(self.base_url)
        if start:
            url = url + "/" + str(start)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        r = self.mkm_request(mkm_oauth, url)

        return self.handle_partial_content("article", mkm_oauth, url, **kwargs)

    def add_stock(self, payload=None, provided_oauth=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = "{}/stock".format(self.base_url)

        # clean data because the API treats "False" as true, must be "false".
        for entry in payload:
            for key, value in entry.items():
                if isinstance(value, bool):
                    entry[key] = str.lower(str(value))

        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Adding stock")
        chunked_list = list(self.__chunks(payload, 100))
        for chunk in chunked_list:
            # chunk[0]["comments"] = "DO NOT BUY"  # HACK: temp comment for testing
            try:
                xml_payload = self.__json_to_xml(chunk)
                r = mkm_oauth.post(url, data=xml_payload)
                inserted = r.json()
                for item in inserted["inserted"]:
                    if not item["success"]:
                        raise CardmarketError(
                            f"{item['error']}: {item['tried']}"  # , url=r.request.url
                        )
                    else:
                        self.logger.debug(
                            f">> Added {item['idArticle']['product']['enName']}."
                        )
                #'{"inserted":[{"success":false,"tried":{"idProduct":"12636","idLanguage":"1","count":"1","price":"0.75","condition":"nm","isFoil":"false","amount":"1"},"error":"An error has ocurred, the card has NOT been listed."}]}'
            except CardmarketError as err:
                self.logger.error(f"{err.mkm_msg()} {err.url}")
                print(err.mkm_msg())
        # TODO: Only considers the last response.
        if self.__handle_response(r):
            return r.json()

    def set_stock(self, payload=None, provided_oauth=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = "{}/stock".format(self.base_url)

        # clean data because the API treats "False" as true, must be "false".
        for entry in payload:
            for key, value in entry.items():
                entry[key] = str.lower(str(value))

        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Updating stock")
        chunked_list = list(self.__chunks(payload, 100))
        for chunk in chunked_list:
            xml_payload = self.__json_to_xml(chunk)
            r = mkm_oauth.put(url, data=xml_payload)

        # TODO: Only considers the last response.
        if self.__handle_response(r):
            return r.json()

    def delete_stock(self, payload=None, provided_oauth=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Stock_Management
        url = "{}/stock".format(self.base_url)

        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Deleting stock")
        chunked_list = list(self.__chunks(payload, 100))
        for chunk in chunked_list:
            xml_payload = self.__json_to_xml(chunk)
            r = mkm_oauth.delete(url, data=xml_payload)

        # TODO: Only considers the last response.
        if self.__handle_response(r):
            return r.json()

    def get_articles(self, product_id, start=0, provided_oauth=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Articles
        self.logger.debug(f"-> get_articles product_id={product_id} start={start}")
        url = "{}/articles/{}".format(self.base_url, product_id)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting articles on product: " + str(product_id))

        return self.handle_partial_content("article", mkm_oauth, url, **kwargs)

    def handle_partial_content(self, item_name, mkm_oauth, url, start=0, **kwargs):
        INCREMENT = 100
        params = kwargs
        params.update({"start": start, "maxResults": INCREMENT})

        r = self.mkm_request(mkm_oauth, url, params=params)

        max_items = 0
        if r.status_code == requests.codes.partial_content:
            max_items = self.__get_max_items_from_header(r)
            self.logger.info(f"> Content-Range header: {r.headers['Content-Range']}")
            self.logger.debug(
                f"> # {item_name}s in response: {str(len(r.json()[item_name]))}"
            )
            if start + INCREMENT >= max_items and self.__handle_response(r):
                return r.json()[item_name]
            else:
                next_start = start + INCREMENT
                params.update({"start": next_start, "maxResults": INCREMENT})
                self.logger.debug(
                    f"-> get {item_name}s recurring to next_start={next_start}"
                )
                return r.json()[item_name] + self.handle_partial_content(
                    item_name, mkm_oauth, url, **kwargs
                )
        elif r.status_code == requests.codes.no_content:
            raise CardmarketError(f"No {item_name}s found.")
            return False
        elif r.status_code == requests.codes.ok:
            return r.json()[item_name]
        else:
            raise ConnectionError(r)

    def find_product(self, search, provided_oauth=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Find_Products

        url = "{}/products/find".format(self.base_url)
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Finding product for search string: " + str(search))

        if "search" not in kwargs:
            kwargs["search"] = search
        if len(search) < 4:
            kwargs["exact"] = "true"

        return self.handle_partial_content("product", mkm_oauth, url, **kwargs)

    def find_stock_article(self, name, game_id, provided_oauth=None):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Find_Articles

        url = "{}/stock/articles/{}/{}".format(
            self.base_url, urllib.parse.quote(name), game_id
        )
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Finding articles in stock: " + str(name))

        r = self.mkm_request(mkm_oauth, url)

        if r.status_code == requests.codes.no_content:
            raise CardmarketError("No articles found.")
        elif r.status_code == requests.codes.ok:
            return r.json()["article"]
        else:
            raise ConnectionError(r)

    def find_user_articles(
        self, user_id, game_id=1, start=0, provided_oauth=None, **kwargs
    ):
        # https://api.cardmarket.com/ws/documentation/API_2.0:User_Articles
        INCREMENT = 1000
        url = f"{self.base_url}/users/{user_id}/articles"
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting articles from user: " + str(user_id))
        return self.handle_partial_content("article", mkm_oauth, url, **kwargs)

    def get_wantslists(self, provided_oauth=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Wantslist

        url = f"{self.base_url}/wantslist"
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting all wants lists")

        r = self.mkm_request(mkm_oauth, url)
        return r.json()["wantslist"]

    def get_wantslist_items(self, idWantsList, provided_oauth=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Wantslist_Item

        url = f"{self.base_url}/wantslist/{idWantsList}"
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting wants list items")

        r = self.mkm_request(mkm_oauth, url)
        return r.json()["wantslist"]

    def get_orders(self, actor, state, start=None, provided_oauth=None, **kwargs):
        # https://api.cardmarket.com/ws/documentation/API_2.0:Filter_Orders
        self.logger.debug(f"-> get_orders start={start}")
        url = f"{self.base_url}/orders/{actor}/{state}"
        if start:
            url += f"/{start}"
        mkm_oauth = self.__setup_service(url, provided_oauth)

        self.logger.debug(">> Getting orders")
        return self.handle_partial_content("order", mkm_oauth, url, **kwargs)
