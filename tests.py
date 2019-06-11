"""
Python unittest
"""
import io
import json
import logging
import random
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch

import requests
from requests_oauthlib import OAuth1Session

from pymkm_app import PyMkmApp
from pymkm_helper import PyMkmHelper
from pymkmapi import PyMkmApi


class TestCommon(unittest.TestCase):

    fake_stock = [
        {'count': 1, 'idArticle': 410480091, 'idProduct': 1692, 'isFoil': False, 'isSigned': True, 'language': {'idLanguage': 7, 'languageName': 'Japanese'}, 'price': 0.75, 'product': {
            'enName': 'Words of Worship', 'expIcon': '39', 'expansion': 'Onslaught', 'idGame': 1, 'image': './img/items/1/ONS/1692.jpg', 'locName': 'Words of Worship', 'nr': '61', 'rarity': 'Rare'}},
        {'count': 1, 'idArticle': 412259385, 'idProduct': 9145, 'isFoil': False, 'isSigned': True, 'language': {'idLanguage': 4, 'languageName': 'Spanish'}, 'price': 0.25, 'product': {
            'enName': 'Mulch', 'expIcon': '18', 'expansion': 'Stronghold', 'idGame': 1, 'image': './img/items/1/STH/9145.jpg', 'locName': 'Estiércol y paja', 'nr': None, 'rarity': 'Common'}},
        {'count': 1, 'idArticle': 407911824, 'idProduct': 242440, 'isFoil': False, 'isSigned': False, 'language': {'idLanguage': 1, 'languageName': 'English'}, 'price': 0.5, 'product': {'enName': 'Everflowing Chalice',
                                                                                                                                                                                          'expIcon': '164', 'expansion': 'Duel Decks: Elspeth... Tezzeret', 'idGame': 1, 'image': './img/items/1/DDF/242440.jpg', 'locName': 'Everflowing Chalice', 'nr': '60', 'rarity': 'Uncommon'}}
    ]

    def setUp(self):
        self.config = json.loads(
            """
            {
                "app_token": "aaaaa",
                "app_secret": "bbbbb",
                "access_token": "ccccccccccc",
                "access_token_secret": "dddddddddd"
            }
            """
        )

    class MockResponse:
        def __init__(self, json_data, status_code, content):
            self.json_data = json_data
            self.status_code = status_code
            self.content = content
            # TODO: write a test for these
            self.headers = {'X-Request-Limit-Count': 1234,
                            'X-Request-Limit-Max': 5000}

        def json(self):
            return self.json_data


class TestPyMkmApp(TestCommon):
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input', side_effect=['0'])
    def test_main_menu(self, mock_input, mock_stdout):
        app = PyMkmApp(self.config)
        app.start()
        self.assertRegex(mock_stdout.getvalue(), r'─ MENU ─')

    @patch('pymkmapi.PyMkmApi.get_stock', return_value=TestCommon.fake_stock)
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input', side_effect=['4', '0'])
    def test_menu_option_4(self, mock_input, mock_stdout, *args):

        app = PyMkmApp(self.config)
        app.start()
        self.assertRegex(mock_stdout.getvalue(),
                     r'Top 20 most expensive articles in stock:')


class TestPyMkmApiCalls(TestCommon):

    api = None

    def setUp(self):
        super(TestPyMkmApiCalls, self).setUp()

        self.api = PyMkmApi(self.config)

    def test_file_not_found2(self):
        open_name = '%s.open' % __name__
        with patch("builtins.open", mock_open(read_data="data")) as mocked_open:
            mocked_open.side_effect = FileNotFoundError

            # Assert that an error is logged
            with self.assertRaises(SystemExit):
                with self.assertLogs(level='ERROR') as cm:
                    PyMkmApi()
                    log_record_level = cm.records[0].levelname
                    self.assertEqual(log_record_level, 'ERROR')

    def test_getAccount(self):
        mockMkmService = Mock(spec=OAuth1Session)
        mockMkmService.get = MagicMock(
            return_value=self.MockResponse("", 401, 'testing error'))

        # with self.assertRaises(requests.exceptions.ConnectionError):
        #    self.api.get_account(mockMkmService)

        mockMkmService.get = MagicMock(
            return_value=self.MockResponse("test", 200, 'testing ok'))
        self.assertEqual(self.api.get_account(mockMkmService), "test")
        mockMkmService.get.assert_called()


class TestPyMkmHelperFunctions(unittest.TestCase):

    def setUp(self):
        self.helper = PyMkmHelper()

    def test_calculate_average(self):
        table = [
            ['Yxskaft', 'SE', 'NM', 1, 1.21],
            ['Frazze11', 'SE', 'NM', 3, 1.3],
            ['andli826', 'SE', 'NM', 2, 1.82]
        ]
        self.assertEqual(self.helper.calculate_average(table, 3, 4), 1.46)

    def test_calculate_median(self):
        table = [
            ['Yxskaft', 'SE', 'NM', 1, 1.21],
            ['Frazze11', 'SE', 'NM', 3, 1.3],
            ['andli826', 'SE', 'NM', 2, 1.82]
        ]
        self.assertEqual(self.helper.calculate_median(table, 3, 4), 1.3)
        self.assertEqual(self.helper.calculate_average(table, 3, 4), 1.46)

    def test_calculate_lowest(self):
        table = [
            ['Yxskaft', 'SE', 'NM', 1, 1.21],
            ['Frazze11', 'SE', 'NM', 3, 1.3],
            ['andli826', 'SE', 'NM', 2, 1.82]
        ]
        self.assertEqual(self.helper.calculate_lowest(table, 4), 1.21)

    def test_round_up_to_quarter(self):
        self.assertEqual(self.helper.round_up_to_quarter(0.99), 1)
        self.assertEqual(self.helper.round_up_to_quarter(0), 0)
        self.assertEqual(self.helper.round_up_to_quarter(0.1), 0.25)

    def test_round_down_to_quarter(self):
        self.assertEqual(self.helper.round_down_to_quarter(0.99), 0.75)
        self.assertEqual(self.helper.round_down_to_quarter(1.01), 1)
        self.assertEqual(self.helper.round_down_to_quarter(0.1), 0)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input', side_effect=['y', 'n', 'asdf'])
    def test_prompt_bool(self, mock_input, mock_stdout):
        self.assertTrue(self.helper.prompt_bool('test_y'))
        self.assertFalse(self.helper.prompt_bool('test_n'))

        # self.helper.prompt_bool('test_error')
        #self.assertRegex(mock_stdout.getvalue(), r'\nPlease answer with y\/n\n')

    @patch('builtins.input', side_effect=['y'])
    def test_prompt_string(self, mock_input):
        self.assertEqual(self.helper.prompt_string('test'), 'y')


if __name__ == '__main__':
    unittest.main()
