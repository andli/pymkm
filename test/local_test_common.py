"""
Python unittest
"""
import io
import json
import logging
import unittest

from unittest.mock import MagicMock, Mock, mock_open, patch

from pymkm.pymkm_app import PyMkmApp
from pymkm.pymkmapi import PyMkmApi


class LocalTestCommon(unittest.TestCase):
    class ArgsObject(object):
        pass

    parsed_args = ArgsObject()
    parsed_args.cached = False
    parsed_args.partial = 0
    parsed_args.price_check_wantslist = None
    parsed_args.update_stock = None

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
