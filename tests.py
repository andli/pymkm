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


class TestPyMkmApiCalls(unittest.TestCase):
    """ This is one of potentially many TestCases """

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


if __name__ == '__main__':
    unittest.main()
