[![Build Status](https://travis-ci.org/andli/pymkm.svg?branch=master)](https://travis-ci.org/andli/pymkm)

# pymkm
Python wrapper for the [cardmarket.com API](https://api.cardmarket.com/ws/documentation/API_2.0:Main_Page) (version 2.0, using OAuth1 and the "Dedicated app" option).

## how?
1. Install requirements using `pip install -r requirements.txt`
1. Copy `config_template.json` to `config.json` and fill in your API keys.

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