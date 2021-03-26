"""
Python unittest
"""
import io
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch

from pymkm.pymkm_app import PyMkmApp
from test.local_test_common import LocalTestCommon


class TestPyMkmApp(LocalTestCommon):
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["0"])
    def test_app_starts_and_connects_to_Cardmarket(self, mock_input, mock_stdout, *args):
        self.assertEqual(True, True)
        app = PyMkmApp()
        app.start(self.parsed_args)
        self.assertRegex(mock_stdout.getvalue(), r"╭─── PyMKM")

    # This thest does live changes to the account, disabled for now
    # @patch("sys.stdout", new_callable=io.StringIO)
    # @patch("builtins.input", side_effect=["backupstock", "y", "restorestock", "y", "0"])
    # def test_stock_update(self, mock_stdin, mock_stdout, *args):
    #    self.assertEqual(True, True)
    #    app = PyMkmApp()
    #    app.start(self.parsed_args)


#
#    out = mock_stdout.getvalue()
#    self.assertRegex(out, r"API calls used today")
#    # self.assertRegex(out, r"Restoring cached stock...")
#    # self.assertRegex(out, r"Done.")


if __name__ == "__main__":
    unittest.main()
