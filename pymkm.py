#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a working app for showcasing the PyMKM module.
"""

__author__ = "Andreas Ehrlund"
__version__ = "2.0.2"
__license__ = "MIT"

from pymkm.pymkm_app import PyMkmApp


def main():
    app = PyMkmApp()
    app.start()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
