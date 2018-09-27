"""
Python unittest
"""
import json
import random
import unittest
from unittest.mock import Mock, MagicMock
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
            self.headers = {'X-Request-Limit-Count': 1234, 'X-Request-Limit-Max': 5000} #TODO: write a test for these

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

    def test_getAccount(self):
        mockMkmService = Mock(spec=OAuth1Session)
        mockMkmService.get = MagicMock(
            return_value=self.MockResponse("", 401, 'testing error'))

        with self.assertRaises(requests.exceptions.ConnectionError):
            self.api.get_account(mockMkmService)
        mockMkmService.get.assert_called()

        mockMkmService.get = MagicMock(
            return_value=self.MockResponse("test", 200, 'testing ok'))
        self.assertEqual(self.api.get_account(mockMkmService), "test")

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

if __name__ == '__main__':
    unittest.main()
