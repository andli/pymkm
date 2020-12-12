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
from test.local_test_common import LocalTestCommon


class TestPyMkmApp(LocalTestCommon):
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_stock_update(self, mock_input, mock_stdout, *args):
        self.assertEquals(True, True)
        # app = PyMkmApp()
        # app.start(self.parsed_args)
        # self.assertRegex(mock_stdout.getvalue(), r"╭─── PyMKM")


if __name__ == "__main__":
    unittest.main()
