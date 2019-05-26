"""
Python unittest
"""
import json
import random
import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import requests
from requests_oauthlib import OAuth1Session
from pymkm import PyMKM
from helper import PyMKM_Helper


class TestPyMkmApiCalls(unittest.TestCase):

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

    api = None

    def setUp(self):
        config = json.loads(
            """
                {
                    "app_token": "aaaaa",
                    "app_secret": "bbbbb",
                    "access_token": "ccccccccccc",
                    "access_token_secret": "dddddddddd"
                }
            """
        )

        self.api = PyMKM(config)

    def test_file_not_found2(self):
        open_name = '%s.open' % __name__
        with patch("builtins.open", mock_open(read_data="data")) as mocked_open:
            mocked_open.side_effect = FileNotFoundError
            
            with self.assertRaises(FileNotFoundError):
                api = PyMKM()
            #mocked_open.return_value = StringIO('foo')

    def test_getAccount(self):
        mockMkmService = Mock(spec=OAuth1Session)
        mockMkmService.get = MagicMock(
            return_value=self.MockResponse("", 401, 'testing error'))

        #with self.assertRaises(requests.exceptions.ConnectionError):
        #    self.api.get_account(mockMkmService)

        mockMkmService.get = MagicMock(
            return_value=self.MockResponse("test", 200, 'testing ok'))
        self.assertEqual(self.api.get_account(mockMkmService), "test")
        mockMkmService.get.assert_called()


class TestPyMkmHelperFunctions(unittest.TestCase):

    def setUp(self):
        self.helper = PyMKM_Helper()

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


if __name__ == '__main__':
    unittest.main()
