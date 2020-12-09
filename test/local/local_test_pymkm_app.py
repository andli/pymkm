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


@patch("pymkm.pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data)
class TestPyMkmApp(TestCommon):

    @patch("requests.get", return_value=TestCommon.fake_github_releases)
    def test_check_latest_version(self, *args):
        app = PyMkmApp(self.config)
        self.assertIsNone(app.check_latest_version())


    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_stock_update(self, mock_input, mock_stdout, *args):
        app = PyMkmApp()
        app.start(self.parsed_args)
        self.assertRegex(mock_stdout.getvalue(), r"╭─── PyMKM")

    
    def test_get_rounding_limit_for_rarity(self, mock_account):
        app = PyMkmApp(self.config)
        self.assertEqual(app.get_rounding_limit_for_rarity("rare", "1"), 1.0)
        self.assertEqual(app.get_rounding_limit_for_rarity("time shifted", "1"), 0.25)
        self.assertEqual(app.get_rounding_limit_for_rarity("XX", "1"), 0.25)

    def test_get_discount_for_condition(self, mock_account):
        app = PyMkmApp(self.config)
        self.assertEqual(app.get_discount_for_condition("MT"), 1.5)
        self.assertEqual(app.get_discount_for_condition("LP"), 0.6)
        with self.assertRaises(KeyError):
            app.get_discount_for_condition("XX")

    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("builtins.input", side_effect=["0"])
    # def test_main_menu(self, mock_input, mock_stdout, *args):
    #    app = PyMkmApp(self.config)
    #    app.start()
    #    self.assertRegex(mock_stdout.getvalue(), r"╭─── PyMKM")
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_items_async",
    #    return_value=TestCommon.fake_product_list_response,
    # )
    # @patch("pymkm.pymkmapi.PyMkmApi.set_stock", return_value=TestCommon.ok_response)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_articles",
    #    return_value=TestCommon.find_user_articles_result,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result,
    # )
    # @patch("builtins.input", side_effect=["1", "2", "y", "y", "0"])
    # @patch("builtins.open", new_callable=mock_open())
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_1(self, mock_open, mock_stdout, *args):
    #    # update_stock_prices_to_trend
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"update_stock_prices_to_trend")
    #
    # @patch("pymkm.pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # @patch("pymkm.pymkmapi.PyMkmApi.set_stock", return_value=TestCommon.ok_response)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_stock_article",
    #    return_value=TestCommon.get_stock_result,
    # )
    # @patch("builtins.input", side_effect=["2", "words", "y", "y", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_2_1(self, mock_open, mock_stdout, *args):
    #    # update_product_to_trend
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"update_product_to_trend")
    #
    # @patch("pymkm.pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # @patch("pymkm.pymkmapi.PyMkmApi.set_stock", return_value=TestCommon.ok_response)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_stock_article",
    #    return_value=TestCommon.get_stock_result,
    # )
    # @patch("builtins.input", side_effect=["2", "words", "1", "n", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_2(self, mock_open, mock_stdout, *args):
    #    # update_product_to_trend
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"update_product_to_trend")
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_articles",
    #    return_value=TestCommon.find_user_articles_result,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_product",
    #    return_value=TestCommon.fake_find_product_result_one_match_of_3["product"],
    # )
    # @patch("builtins.input", side_effect=["3", "words", "n", "1", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_3(self, mock_stdout, *args):
    #    # list_competition_for_product
    #    app = PyMkmApp(self.config)
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"list_competition_for_product")
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_items_async",
    #    return_value=TestCommon.fake_product_list_response,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_user_articles",
    #    return_value=TestCommon.find_user_articles_result,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_product",
    #    return_value=TestCommon.fake_find_product_result_one_match_of_3,
    # )
    # @patch("builtins.input", side_effect=["4", "words", "1", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_4(self, mock_stdout, *args):
    #    # find_deals_from_user
    #    app = PyMkmApp(self.config)
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"find_deals_from_user")
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # @patch("builtins.input", side_effect=["5", "0"])
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # @patch("sys.stdout", new_callable=io.StringIO)
    # def test_menu_option_5(self, mock_stdout, *args):
    #    # show_top_expensive_articles_in_stock
    #    app = PyMkmApp(self.config)
    #    app.start()
    #    text = mock_stdout.getvalue()
    #    self.assertRegex(
    #        mock_stdout.getvalue(), r"Top 20 most expensive articles in stock:"
    #    )
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_items_async",
    #    return_value=TestCommon.cardmarket_metaproduct_list_response,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_orders", return_value=TestCommon.get_order_items,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_wantslist_items",
    #    return_value=TestCommon.get_wantslist_items,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_wantslists", return_value=TestCommon.get_wantslists
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data
    # )
    # @patch("builtins.input", side_effect=["6", "0"])
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # @patch("sys.stdout", new_callable=io.StringIO)
    # def test_menu_option_6(self, mock_stdout, *args):
    #    # clean_purchased_from_wantslists
    #    app = PyMkmApp(self.config)
    #    app.start()
    #    self.assertRegex(mock_stdout.getvalue(), r"This will show items in your ")
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_account", return_value=TestCommon.fake_account_data
    # )
    # @patch("builtins.input", side_effect=["7", "0"])
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # @patch("sys.stdout", new_callable=io.StringIO)
    # def test_menu_option_7(self, mock_stdout, *args):
    #    # show_account_info
    #    app = PyMkmApp(self.config)
    #    # app.start()
    #    # self.assertRegex(mock_stdout.getvalue(), r"{'account':")
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"show_account_info")
    #
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # @patch("pymkm.pymkmapi.PyMkmApi.delete_stock", return_value=TestCommon.ok_response)
    # @patch("builtins.input", side_effect=["8", "y", "0"])
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_8(self, *args):
    #    # clear_entire_stock
    #    app = PyMkmApp(self.config)
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"clear_entire_stock")
    #
    # @patch("pymkm.pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    # @patch("pymkm.pymkmapi.PyMkmApi.add_stock", return_value=TestCommon.ok_response)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_product",
    #    return_value=TestCommon.fake_product_list_response,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_product",
    #    return_value=TestCommon.fake_find_product_result_one_match_of_3["product"],
    # )
    # @patch("builtins.input", side_effect=["9", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch(
    #    "builtins.open",
    #    new_callable=mock_open,
    #    create=True,
    #    read_data=TestCommon.fake_list_csv,
    # )
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_9(self, mock_open, mock_stdout, *args):
    #    # import_from_csv
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"import_from_csv:")
    #
    # @patch("pymkm.pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    # @patch("pymkm.pymkmapi.PyMkmApi.add_stock", return_value=TestCommon.ok_response)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_product",
    #    return_value=TestCommon.fake_product_list_response,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_product",
    #    return_value=TestCommon.fake_find_product_result_no_match["product"],
    # )
    # @patch("builtins.input", side_effect=["9", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch(
    #    "builtins.open",
    #    new_callable=mock_open,
    #    create=True,
    #    read_data=TestCommon.fake_list_csv,
    # )
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_9_no_match(self, mock_open, mock_stdout, *args):
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"import_from_csv:")
    #
    # @patch("pymkm.pymkm_app.PyMkmApp.get_price_for_product", return_value=1)
    # @patch("pymkm.pymkmapi.PyMkmApi.add_stock", return_value=TestCommon.ok_response)
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_product",
    #    return_value=TestCommon.fake_find_product_result_one_match_only["product"],
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.find_product",
    #    return_value=TestCommon.fake_find_product_result_one_match_only["product"],
    # )
    # @patch("builtins.input", side_effect=["9", "0"])
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch(
    #    "builtins.open",
    #    new_callable=mock_open,
    #    create=True,
    #    read_data=TestCommon.fake_list_csv,
    # )
    # @patch("pymkm.pymkm_app.PyMkmApp.check_latest_version", return_value=None)
    # def test_menu_option_9_1_match(self, mock_open, mock_stdout, *args):
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="DEBUG") as cm:
    #        app.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"import_from_csv:")


    # @patch(
    #    "pymkm.pymkm_app.PyMkmApi.get_product",
    #    return_value=TestCommon.fake_product_response,
    # )
    # @patch(
    #    "pymkm.pymkmapi.PyMkmApi.get_stock", return_value=TestCommon.get_stock_result
    # )
    # def test_get_price_for_product(self, mock_response, *args):
    #    self.api = PyMkmApi(self.config)
    #    app = PyMkmApp(self.config)
    #
    #    fake_product = app.get_stock_as_array(self.api)[0]
    #    price = app.get_price_for_product(
    #        TestCommon.fake_product_response,
    #        fake_product["product"]["rarity"],
    #        fake_product["condition"],
    #        fake_product["isFoil"],
    #        fake_product["isPlayset"],
    #        api=self.api,
    #    )
    #
    #    self.assertEqual(price, 3.0)



    # @patch("requests.post", side_effect=requests.exceptions.Timeout())
    # def test_report(self, mock_post, *args):
    #    app = PyMkmApp(self.config)
    #
    #    with self.assertLogs(level="ERROR") as cm:
    #        self.patcher.stop()
    #        app.report("testcommand")
    #        self.patcher.start()
    #        log_record = cm.records[len(cm.records) - 1]
    #        self.assertRegex(log_record.message, r"Connection error to stats server.")

    # @patch("builtins.input", side_effect=["1"])
    # def test_select_from_list_of_wantslists(self, *args):
    #    app = PyMkmApp(self.config)
    #    list = app.select_from_list_of_wantslists(TestCommon.cardmarket_get_wantslists)
    #    self.assertEqual(list["idWantslist"], 2789285)


#
# @patch("builtins.input", side_effect=["1"])
# def test_select_from_list_of_articles(self, *args):
#    app = PyMkmApp(self.config)
#    article = app.select_from_list_of_articles(TestCommon.get_stock_result)
#    self.assertEqual(article["idArticle"], 410480091)


if __name__ == "__main__":
    unittest.main()
