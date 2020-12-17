#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a working app for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "2.1.1"
__license__ = "MIT"

import argparse
from pymkm.pymkm_app import PyMkmApp


def main():
    parser = argparse.ArgumentParser(description="pymkm command line interface.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--update_stock",
        action="store_true",
        help="Update stock prices. Use --partial if needed.",
    )
    parser.add_argument(
        "--partial",
        metavar="<number>",
        type=int,
        default=0,
        help="Used for partial updates of for example stock.",
    )
    parser.add_argument(
        "--price_check_wantslist",
        metavar="<wantslist name>",
        type=str,
        help="Run the Track price data to csv option.",
    )
    parser.add_argument(
        "--cached",
        type=bool,
        default=False,
        help="Use cached values if available (defaults to False).",
    )

    args = parser.parse_args()

    app = PyMkmApp()
    app.start(args)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
