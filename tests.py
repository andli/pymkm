"""
Python unittest
"""
import io
import json
import logging
import random
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch
from distutils.util import strtobool

import requests
from requests_oauthlib import OAuth1Session

from pymkm_app import PyMkmApp
from pymkm_helper import PyMkmHelper
from pymkmapi import PyMkmApi


class TestCommon(unittest.TestCase):

    cardmarket_get_stock_result = {
        "article": [
            {
                "count": 1,
                "idArticle": 410480091,
                "idProduct": 1692,
                "isFoil": False,
                "isPlayset": False,
                "comments": "x",
                "isSigned": True,
                "language": {"idLanguage": 7, "languageName": "Japanese"},
                "price": 0.75,
                "condition": "NM",
                "product": {
                    "enName": "Words of Worship",
                    "expIcon": "39",
                    "expansion": "Onslaught",
                    "idGame": 1,
                    "image": "./img/items/1/ONS/1692.jpg",
                    "locName": "Words of Worship",
                    "nr": "61",
                    "rarity": "Rare",
                },
            },
            {
                "count": 1,
                "idArticle": 412259385,
                "idProduct": 9145,
                "isFoil": True,
                "isPlayset": False,
                "comments": "! poop",
                "isSigned": True,
                "language": {"idLanguage": 4, "languageName": "Spanish"},
                "price": 0.25,
                "condition": "NM",
                "product": {
                    "enName": "Mulch words",
                    "expIcon": "18",
                    "expansion": "Stronghold",
                    "idGame": 1,
                    "image": "./img/items/1/STH/9145.jpg",
                    "locName": "Estiércol y paja",
                    "nr": None,
                    "rarity": "Common",
                },
            },
            {
                "count": 1,
                "idArticle": 407911824,
                "idProduct": 1079,
                "isFoil": False,
                "isPlayset": False,
                "comments": "",
                "isSigned": False,
                "language": {"idLanguage": 1, "languageName": "English"},
                "price": 0.5,
                "condition": "NM",
                "product": {
                    "enName": "Everflowing Chalice",
                    "expIcon": "164",
                    "expansion": "Duel Decks: Elspeth... Tezzeret",
                    "idGame": 1,
                    "image": "./img/items/1/DDF/242440.jpg",
                    "locName": "Everflowing Chalice",
                    "nr": "60",
                    "rarity": "Uncommon",
                },
            },
        ]
    }

    get_stock_result = cardmarket_get_stock_result["article"]

    fake_product_response = {
        "product": {
            "categoryName": "Magic Single",
            "countArticles": 876,
            "countFoils": 46,
            "countReprints": 1,
            "idProduct": 1692,
            "enName": "Words of Worship",
            "expansion": {
                "enName": "Onslaught",
                "expansionIcon": 39,
                "idExpansion": 41,
            },
            "gameName": "Magic the Gathering",
            "idGame": "1",
            "idMetaproduct": 6716,
            "priceGuide": {
                "AVG": 3.18,
                "LOW": 0.29,
                "LOWEX": 0.8,
                "LOWFOIL": 0.8,
                "SELL": 2.18,
                "TREND": 2.11,
                "TRENDFOIL": 2.07,
            },
        }
    }

    fake_list_csv = """Card,Set Name,Quantity,Foil,Language
Dragon Breath,Scourge,1,Foil,French"""

    fake_find_product_result_no_match = {
        "product": [
            {
                "categoryName": "Magic Single",
                "enName": "Dragon BreathXX",
                "expansionName": "Scourge",
                "idProduct": 9145,
                "rarity": "Rare",
            },
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "ScourgeXX",
                "idProduct": 9145,
                "rarity": "Rare",
            },
        ]
    }

    fake_find_product_result_one_match_of_3 = {
        "product": [
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "Scourge",
                "idProduct": 1079,
                "rarity": "Common",
            },
            {
                "categoryName": "Magic Single",
                "enName": "Dragon BreathXX",
                "expansionName": "Scourge",
                "idProduct": 9145,
                "rarity": "Rare",
            },
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "ScourgeXX",
                "idProduct": 9145,
                "rarity": "Rare",
            },
        ]
    }

    fake_find_product_result_one_match_only = {
        "product": [
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "Scourge",
                "idProduct": 1079,
                "rarity": "Common",
            }
        ]
    }

    cardmarket_find_user_articles_result = {
        "article": [
            {
                "comments": "x",
                "condition": "EX",
                "count": 1,
                "idArticle": 371427479,
                "idProduct": 1692,
                "inShoppingCart": False,
                "isAltered": False,
                "isFoil": False,
                "isPlayset": False,
                "isSigned": False,
                "language": {"idLanguage": 1, "languageName": "English"},
                "price": 0.2,
                "seller": {
                    "address": {"country": 1},
                    "avgShippingTime": 1,
                    "email": "x",
                    "idUser": 34018,
                    "isCommercial": 0,
                    "isSeller": True,
                    "legalInformation": "x",
                    "lossPercentage": "0 - 2%",
                    "username": "test",
                },
            },
            {
                "comments": "x",
                "condition": "EX",
                "count": 1,
                "idArticle": 406723464,
                "idProduct": 1692,
                "inShoppingCart": False,
                "isAltered": False,
                "isFoil": False,
                "isPlayset": False,
                "isSigned": False,
                "language": {"idLanguage": 1, "languageName": "English"},
                "price": 1.5,
                "seller": {
                    "address": {"country": 1},
                    "avgShippingTime": 0,
                    "email": "x",
                    "idUser": 655460,
                    "isCommercial": 0,
                    "isSeller": True,
                    "legalInformation": "x",
                    "lossPercentage": "0 - 2%",
                    "username": "test",
                },
            },
        ]
    }

    find_user_articles_result = cardmarket_find_user_articles_result["article"]

    fake_account_data = {
        "account": {
            "username": "test",
            "country": "test",
            "onVacation": True,
            "idDisplayLanguage": "1",
        },
        "message": "Successfully set the account on vacation.",
    }

    def setUp(self):
        self.config = json.loads(
            """
            {
                "app_token": "aaaaa",
                "app_secret": "bbbbb",
                "access_token": "ccccccccccc",
                "access_token_secret": "dddddddddd",
                "price_limit_by_rarity": {
                    "default": "0.25",
                    "common": "0.25",
                    "uncommon": "0.25",
                    "rare": "1.0",
                    "mythic": "0.25",
                    "time shifted": "0.25"
                },
                "discount_by_condition": {
                    "MT": "1.5",
                    "NM": "1",
                    "EX": "0.9",
                    "GD": "0.7",
                    "LP": "0.6",
                    "PL": "0.5",
                    "PO": "0.4"
                },
                "search_filters": {
                    "language": ""
                },
                "sticky_price_char": "!"
            }
            """
        )

        self.patcher = patch("pymkm_app.PyMkmApp.report")
        self.mock_report = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    class MockResponse:
        def __init__(self, json_data, status_code, content):
            self.json_data = json_data
            self.status_code = status_code
            self.content = content
            # TODO: write a test for these
            self.headers = {
                "X-Request-Limit-Count": 1234,
                "X-Request-Limit-Max": 5000,
                "Content-Range": "/100",
            }

        def json(self):
            return self.json_data


class TestPyMkmApp(TestCommon):

    ok_response = TestCommon.MockResponse("test", 200, "testing ok")
    fake_github_releases = TestCommon.MockResponse({"tag_name": "1.0.0"}, 200, "ok")

    @patch("requests.get", return_value=fake_github_releases)
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_main_menu(self, mock_input, mock_stdout, *args):
        app = PyMkmApp(self.config)
        app.start()
        self.assertRegex(mock_stdout.getvalue(), r"╭─── PyMKM")

    @patch(
        "pymkm_app.PyMkmApi.get_product", return_value=TestCommon.fake_product_response,
    )
    @patch("pymkmapi.PyMkmApi.set_stock", return_value=ok_response)
    @patch("pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data)
    @patch(
        "pymkmapi.PyMkmApi.get_articles",
        return_value=TestCommon.find_user_articles_result,
    )
    @patch(
        "pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result,
    )
    @patch("builtins.input", side_effect=["1", "y", "y", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_1(self, mock_open, mock_stdout, *args):
        app = PyMkmApp(self.config)

        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(
                log_record.message, r">> Exited update_stock_prices_to_trend"
            )

    @patch("pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    @patch("pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result)
    @patch("pymkmapi.PyMkmApi.set_stock", return_value=ok_response)
    @patch(
        "pymkmapi.PyMkmApi.find_stock_article", return_value=TestCommon.get_stock_result
    )
    @patch("builtins.input", side_effect=["2", "words", "1", "n", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_2(self, mock_open, mock_stdout, *args):
        app = PyMkmApp(self.config)

        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(log_record.message, r">> Exited update_product_to_trend")

    @patch(
        "pymkmapi.PyMkmApi.get_articles",
        return_value=TestCommon.find_user_articles_result,
    )
    @patch("pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data)
    @patch("pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result)
    @patch(
        "pymkmapi.PyMkmApi.find_product",
        return_value=TestCommon.fake_find_product_result_one_match_of_3,
    )
    @patch("builtins.input", side_effect=["3", "words", "n", "1", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_3(self, mock_stdout, *args):

        app = PyMkmApp(self.config)
        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(
                log_record.message, r">> Exited list_competition_for_product"
            )

    @patch(
        "pymkmapi.PyMkmApi.get_product", return_value=TestCommon.fake_product_response,
    )
    @patch(
        "pymkmapi.PyMkmApi.find_user_articles",
        return_value=TestCommon.find_user_articles_result,
    )
    @patch("pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data)
    @patch("pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result)
    @patch(
        "pymkmapi.PyMkmApi.find_product",
        return_value=TestCommon.fake_find_product_result_one_match_of_3,
    )
    @patch("builtins.input", side_effect=["4", "words", "1", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_4(self, mock_stdout, *args):

        app = PyMkmApp(self.config)
        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(log_record.message, r">> Exited find_deals_from_user")

    @patch("pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result)
    @patch("builtins.input", side_effect=["5", "0"])
    @patch("requests.get", return_value=fake_github_releases)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_menu_option_5(self, mock_stdout, *args):

        app = PyMkmApp(self.config)
        app.start()
        text = mock_stdout.getvalue()
        self.assertRegex(
            mock_stdout.getvalue(), r"Top 20 most expensive articles in stock:"
        )

    @patch("pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data)
    @patch("builtins.input", side_effect=["6", "0"])
    @patch("requests.get", return_value=fake_github_releases)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_menu_option_6(self, mock_stdout, *args):

        app = PyMkmApp(self.config)
        app.start()
        print(mock_stdout.getvalue())
        self.assertRegex(mock_stdout.getvalue(), r"This will show items in your ")

    @patch("pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data)
    @patch("builtins.input", side_effect=["7", "0"])
    @patch("requests.get", return_value=fake_github_releases)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_menu_option_7(self, mock_stdout, *args):

        app = PyMkmApp(self.config)
        app.start()
        print(mock_stdout.getvalue())
        self.assertRegex(mock_stdout.getvalue(), r"{'account':")

    @patch("pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result)
    @patch("pymkmapi.PyMkmApi.delete_stock", return_value=ok_response)
    @patch("builtins.input", side_effect=["8", "y", "0"])
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_8(self, *args):
        app = PyMkmApp(self.config)

        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(log_record.message, r">> Exited clear_entire_stock")

    @patch("pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    @patch("pymkmapi.PyMkmApi.add_stock", return_value=ok_response)
    @patch(
        "pymkmapi.PyMkmApi.find_product",
        return_value=TestCommon.fake_find_product_result_one_match_of_3,
    )
    @patch("builtins.input", side_effect=["9", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        create=True,
        read_data=TestCommon.fake_list_csv,
    )
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_9(self, mock_open, mock_stdout, *args):
        app = PyMkmApp(self.config)

        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(log_record.message, r">> Exited import_from_csv")

    @patch("pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    @patch("pymkmapi.PyMkmApi.add_stock", return_value=ok_response)
    @patch(
        "pymkmapi.PyMkmApi.find_product",
        return_value=TestCommon.fake_find_product_result_no_match,
    )
    @patch("builtins.input", side_effect=["9", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        create=True,
        read_data=TestCommon.fake_list_csv,
    )
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_9_no_match(self, mock_open, mock_stdout, *args):
        app = PyMkmApp(self.config)

        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(log_record.message, r">> Exited import_from_csv")

    @patch("pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    @patch("pymkmapi.PyMkmApi.add_stock", return_value=ok_response)
    @patch(
        "pymkmapi.PyMkmApi.find_product",
        return_value=TestCommon.fake_find_product_result_one_match_only,
    )
    @patch("builtins.input", side_effect=["9", "0"])
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        create=True,
        read_data=TestCommon.fake_list_csv,
    )
    @patch("requests.get", return_value=fake_github_releases)
    def test_menu_option_9_1_match(self, mock_open, mock_stdout, *args):
        app = PyMkmApp(self.config)

        with self.assertLogs(level="DEBUG") as cm:
            app.start()
            log_record = cm.records[len(cm.records) - 1]
            self.assertRegex(log_record.message, r">> Exited import_from_csv")

    def test_get_rounding_limit_for_rarity(self):
        app = PyMkmApp(self.config)
        self.assertEqual(app.get_rounding_limit_for_rarity("rare"), 1.0)
        self.assertEqual(app.get_rounding_limit_for_rarity("time shifted"), 0.25)
        self.assertEqual(app.get_rounding_limit_for_rarity("XX"), 0.25)

    def test_get_discount_for_condition(self):
        app = PyMkmApp(self.config)
        self.assertEqual(app.get_discount_for_condition("MT"), 1.5)
        self.assertEqual(app.get_discount_for_condition("LP"), 0.6)
        with self.assertRaises(KeyError):
            app.get_discount_for_condition("XX")

    @patch(
        "pymkm_app.PyMkmApi.get_product", return_value=TestCommon.fake_product_response,
    )
    @patch("pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result)
    def test_get_price_for_product(self, mock_response, mock_get_stock):
        self.api = PyMkmApi(self.config)
        app = PyMkmApp(self.config)

        fake_product = app.get_stock_as_array(self.api)[0]
        price = app.get_price_for_product(
            fake_product["idProduct"],
            fake_product["product"]["rarity"],
            fake_product["condition"],
            fake_product["isFoil"],
            fake_product["isPlayset"],
            api=self.api,
        )

        self.assertEqual(price, 3.0)


class TestPyMkmApiCalls(TestCommon):

    api = None

    def setUp(self):
        super(TestPyMkmApiCalls, self).setUp()

        self.api = PyMkmApi(self.config)

    def test_file_not_found2(self):
        open_name = "%s.open" % __name__
        with patch("builtins.open", mock_open(read_data="data")) as mocked_open:
            mocked_open.side_effect = FileNotFoundError

            # Assert that an error is logged
            with self.assertRaises(SystemExit):
                with self.assertLogs(level="ERROR") as cm:
                    PyMkmApi()
                    log_record_level = cm.records[0].levelname
                    self.assertEqual(log_record_level, "ERROR")

    def test_get_account(self):
        mock_oauth = Mock(spec=OAuth1Session)

        mock_oauth.get = MagicMock(
            return_value=self.MockResponse("test", 200, "testing ok")
        )
        self.assertEqual(self.api.get_account(mock_oauth), "test")
        mock_oauth.get.assert_called()

        mock_oauth.get = MagicMock(
            return_value=self.MockResponse("", 401, "Unauthorized")
        )
        with self.assertLogs(level="ERROR") as cm:
            self.api.get_account(mock_oauth)
            self.assertGreater(len(cm.records), 0)

    def test_get_stock(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.cardmarket_get_stock_result, 200, "testing ok"
            )
        )
        stock = self.api.get_stock(None, mock_oauth)
        self.assertEqual(stock[0]["comments"], "x")

    def test_get_games(self):
        test_json = json.loads('{"test": "test"}')
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(test_json, 200, "testing ok")
        )
        self.assertEqual(self.api.get_games(mock_oauth), test_json)

    def test_get_expansions(self):
        test_json = json.loads('{"test": "test"}')
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(test_json, 200, "testing ok")
        )
        game_id = 1
        self.assertEqual(self.api.get_expansions(game_id, mock_oauth), test_json)

    def test_get_cards_in_expansion(self):
        test_json = json.loads('{"test": "test"}')
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(test_json, 200, "testing ok")
        )
        expansion_id = 1
        self.assertEqual(
            self.api.get_cards_in_expansion(expansion_id, mock_oauth), test_json
        )

    def test_get_product(self):
        test_json = json.loads('{"test": "test"}')
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(test_json, 200, "testing ok")
        )
        product_id = 1
        self.assertEqual(self.api.get_product(product_id, mock_oauth), test_json)

    def test_find_product(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.fake_product_response, 200, "testing ok"
            )
        )
        search_string = "test"
        result = self.api.find_product(search_string, mock_oauth)
        self.assertEqual(result, TestCommon.fake_product_response)

    def test_find_stock_article(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.cardmarket_find_user_articles_result, 200, "testing ok"
            )
        )
        name = "test"
        game_id = 1
        result = self.api.find_stock_article(name, game_id, mock_oauth)
        self.assertEqual(result[0]["comments"], "x")

    def test_get_articles_in_shoppingcarts(self):
        test_json = json.loads('{"test": "test"}')
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(test_json, 200, "testing ok")
        )

        self.assertEqual(self.api.get_articles_in_shoppingcarts(mock_oauth), test_json)

    def test_get_articles(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.cardmarket_find_user_articles_result, 200, "testing ok"
            )
        )
        product_id = 1

        result = self.api.get_articles(product_id, 0, mock_oauth)
        self.assertEqual(result[0]["comments"], "x")

        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.cardmarket_find_user_articles_result, 206, "partial content"
            )
        )
        product_id = 1

        result = self.api.get_articles(product_id, 0, mock_oauth)
        self.assertEqual(result[0]["comments"], "x")

    def test_find_user_articles(self):

        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.cardmarket_find_user_articles_result, 200, "testing ok"
            )
        )
        user_id = 1
        game_id = 1

        result = self.api.find_user_articles(user_id, game_id, 0, mock_oauth)
        self.assertEqual(result[0]["comments"], "x")

        mock_oauth.get = MagicMock(
            return_value=self.MockResponse(
                TestCommon.cardmarket_find_user_articles_result, 206, "partial content"
            )
        )

        result = self.api.find_user_articles(user_id, game_id, 0, mock_oauth)
        self.assertEqual(result[0]["comments"], "x")

    def test_set_vacation_status(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.put = MagicMock(
            return_value=self.MockResponse(
                TestCommon.fake_account_data, 200, "testing ok"
            )
        )
        vacation_status = True

        result = self.api.set_vacation_status(vacation_status, mock_oauth)
        self.assertEqual(result["message"], "Successfully set the account on vacation.")
        self.assertEqual(result["account"]["onVacation"], vacation_status)

    def test_set_display_language(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.put = MagicMock(
            return_value=self.MockResponse(
                TestCommon.fake_account_data, 200, "testing ok"
            )
        )
        display_language = 1

        result = self.api.set_display_language(display_language, mock_oauth)
        self.assertEqual(
            result["account"]["idDisplayLanguage"], str(display_language).lower()
        )

    def test_add_stock(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.post = MagicMock(
            return_value=self.MockResponse(
                TestCommon.get_stock_result, 200, "testing ok"
            )
        )

        result = self.api.add_stock(TestCommon.get_stock_result, mock_oauth)
        self.assertEqual(len(result), 3)

    def test_set_stock(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.put = MagicMock(
            return_value=self.MockResponse(
                TestCommon.get_stock_result, 200, "testing ok"
            )
        )

        result = self.api.set_stock(TestCommon.get_stock_result, mock_oauth)
        self.assertEqual(len(result), 3)

    def test_delete_stock(self):
        mock_oauth = Mock(spec=OAuth1Session)
        mock_oauth.delete = MagicMock(
            return_value=self.MockResponse(
                TestCommon.get_stock_result, 200, "testing ok"
            )
        )

        result = self.api.delete_stock(TestCommon.get_stock_result, mock_oauth)
        self.assertEqual(len(result), 3)


class TestPyMkmHelperFunctions(unittest.TestCase):
    def setUp(self):
        self.helper = PyMkmHelper()

    def test_calculate_average(self):
        table = [
            ["Yxskaft", "SE", "NM", 1, 1.21],
            ["Frazze11", "SE", "NM", 3, 1.3],
            ["andli826", "SE", "NM", 2, 1.82],
        ]
        self.assertEqual(self.helper.calculate_average(table, 3, 4), 1.46)

    def test_calculate_median(self):
        table = [
            ["Yxskaft", "SE", "NM", 1, 1.21],
            ["Frazze11", "SE", "NM", 3, 1.3],
            ["andli826", "SE", "NM", 2, 1.82],
        ]
        self.assertEqual(self.helper.calculate_median(table, 3, 4), 1.3)
        self.assertEqual(self.helper.calculate_average(table, 3, 4), 1.46)

    def test_calculate_lowest(self):
        table = [
            ["Yxskaft", "SE", "NM", 1, 1.21],
            ["Frazze11", "SE", "NM", 3, 1.3],
            ["andli826", "SE", "NM", 2, 1.82],
        ]
        self.assertEqual(self.helper.get_lowest_price_from_table(table, 4), 1.21)

    def test_round_up_to_limit(self):
        self.assertEqual(self.helper.round_up_to_multiple_of_lower_limit(0.25, 0.99), 1)
        self.assertEqual(self.helper.round_up_to_multiple_of_lower_limit(0.25, 0), 0)
        self.assertEqual(
            self.helper.round_up_to_multiple_of_lower_limit(0.25, 0.1), 0.25
        )

        self.assertEqual(self.helper.round_up_to_multiple_of_lower_limit(0.1, 0.99), 1)
        self.assertEqual(
            self.helper.round_up_to_multiple_of_lower_limit(0.01, 0.011), 0.02
        )
        self.assertEqual(self.helper.round_up_to_multiple_of_lower_limit(0.01, 1), 1)
        self.assertEqual(self.helper.round_up_to_multiple_of_lower_limit(1, 0.1), 1)

    def test_round_down_to_limit(self):
        self.assertEqual(
            self.helper.round_down_to_multiple_of_lower_limit(0.25, 0.99), 0.75
        )
        self.assertEqual(
            self.helper.round_down_to_multiple_of_lower_limit(0.25, 1.01), 1
        )
        self.assertEqual(
            self.helper.round_down_to_multiple_of_lower_limit(0.25, 0.1), 0.25
        )

        self.assertEqual(
            self.helper.round_down_to_multiple_of_lower_limit(0.1, 0.99), 0.9
        )
        self.assertEqual(
            self.helper.round_down_to_multiple_of_lower_limit(0.01, 0.011), 0.01
        )
        self.assertEqual(self.helper.round_down_to_multiple_of_lower_limit(0.01, 1), 1)
        self.assertEqual(self.helper.round_down_to_multiple_of_lower_limit(1, 0.1), 1)

        self.assertEqual(
            self.helper.round_down_to_multiple_of_lower_limit(0.10, 8.44), 8.4
        )

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["y", "n", "p", "n"])
    def test_prompt_bool(self, mock_input, mock_stdout):
        self.assertTrue(self.helper.prompt_bool("test_y"))
        self.assertFalse(self.helper.prompt_bool("test_n"))
        self.helper.prompt_bool("test_error")
        self.assertRegex(mock_stdout.getvalue(), r"\nPlease answer with y\/n\n")

    @patch("builtins.input", side_effect=["y"])
    def test_prompt_string(self, mock_input):
        self.assertEqual(self.helper.prompt_string("test"), "y")


if __name__ == "__main__":
    unittest.main()
