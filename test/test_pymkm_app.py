"""
Python unittest
"""
import io
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch

import requests
from requests_oauthlib import OAuth1Session

from pymkm.pymkmapi import PyMkmApi
from pymkm.pymkm_app import PyMkmApp
from test.test_common import TestCommon


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

    @patch(
        "pymkmapi.PyMkmApi.get_orders", return_value=TestCommon.get_orders,
    )
    @patch(
        "pymkmapi.PyMkmApi.get_wantslist_items",
        return_value=TestCommon.get_wantslist_items,
    )
    @patch("pymkmapi.PyMkmApi.get_wantslists", return_value=TestCommon.get_wantslists)
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


if __name__ == "__main__":
    unittest.main()
