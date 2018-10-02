[![Build Status](https://travis-ci.org/andli/pymkm.svg?branch=master)](https://travis-ci.org/andli/pymkm) [![codecov](https://codecov.io/gh/andli/pymkm/branch/master/graph/badge.svg)](https://codecov.io/gh/andli/pymkm) [![Known Vulnerabilities](https://snyk.io/test/github/andli/pymkm/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/andli/pymkm?targetFile=requirements.txt)


# pymkm
Python wrapper for the [cardmarket.com API](https://api.cardmarket.com/ws/documentation/API_2.0:Main_Page) (version 2.0, using OAuth1 and the "Dedicated app" option).

The included sample app can update your stock prices to trend for non-foils, and to a competitive prices for foils, all rounded to nearest .25 €. A confirmation step allows you to check the result before uploading the new prices.

**NOTE:** Use this functionality at your own risk, I take no responsibility for the resulting prices.

The app also keeps track of how many API requests your have left each day.

![Screengrab](https://raw.githubusercontent.com/andli/pymkm/master/screengrab.png)

## how?
1. Install requirements using `pip install -r requirements.txt`
1. Copy `config_template.json` to `config.json` and fill in your API keys.
1. Run `main.py`.
1. Profit.

## supported calls
These calls are implemented so far. They are not fully tested with different edge cases etc. Please submit an issue or pull request if you find problems.
* `get_games`
* `get_expansions`
* `get_cards_in_expansion`
* `get_product`
* `get_account`
* `get_articles_in_shoppingcarts`
* `set_vacation_status`
* `set_display_language`
* `get_stock`
* `set_stock`
* `get_articles`