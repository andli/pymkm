[![Build Status](https://travis-ci.org/andli/pymkm.svg?branch=master)](https://travis-ci.org/andli/pymkm) [![codecov](https://codecov.io/gh/andli/pymkm/branch/master/graph/badge.svg)](https://codecov.io/gh/andli/pymkm) [![Known Vulnerabilities](https://snyk.io/test/github/andli/pymkm/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/andli/pymkm?targetFile=requirements.txt)

See the [Changelog](CHANGELOG.md) for what's new.

# 📙 PyMKM

Python wrapper for the [cardmarket.com API](https://api.cardmarket.com/ws/documentation/API_2.0:Main_Page) (version 2.0, using OAuth1 and the "Dedicated app" option).

The included sample app can update your stock prices to trend for non-foils, and to a competitive prices for foils, all rounded to nearest configurable value per rarity (default .25 €). A confirmation step allows you to check the result before uploading the new prices.

The app can import a .csv list of cards to your stock. It can also be used to clear your entire stock.
The app also keeps track of how many API requests your have left each day.

**NOTE:** Use all functionality at your own risk, I take no responsibility for the resulting prices or wiped stock. See 'price calculation' below for more details.

**NOTE 2:** From version 1.1.0 this app collects a tiny amount (`{'command': 'import from csv', 'version': '1.1.0'}`) of usage data. If you want to opt out from this, please change `ALLOW_REPORTING = True` to `False` in `pymkm_app.py`. The purpose is to allow me to see what people use the most and to focus on improving that.

![Screengrab](https://raw.githubusercontent.com/andli/pymkm/master/screengrab.png)

## 🔓 Locking prices

Should you want to avoid updating certain articles in your stock, set the starting character of the comment for that article to `!` (possible to change which character in `config.json`).

## 📄 CSV importing

If you scan cards using an app like Delver Lens or the TCG Player app, this feature can help you do bulk import of that list.

Drop your list of cards into a file called `list.csv` in the root directory (there is an example file included in this repo). The file has to follow this format (including the header row):

```
Card,Set Name,Quantity,Foil,Language
Dragon Breath,Scourge,1,Foil,French
```

Remove all quotation marks and extra commas in card names.

Any cards that fail to import are written to a new .csv file called `failed_imports.csv`.

## 📊 Competition view

This feature allows you to get a better view of how you should price individual cards depending on your local market and also the whole market:

![Competition](https://raw.githubusercontent.com/andli/pymkm/master/competition.png)

## 🔨 How

1. Install requirements using `pip install -r requirements.txt`
1. Copy `config_template.json` to `config.json` and fill in your API keys.
1. Run `main.py`.
1. Profit.

## 📈 Price calculation

The prices for non-foils are the "trend" prices supplied by Cardmarket. I only look at English cards for now.
Cardmarket does not however supply trend prices for foils, so my algorithm is this:

_NOTE: This is a rough algorithm, designed to be safe and not to sell aggressively._

1. Filter out foils, English, not altered, not signed, minimum Good condition.
1. Set price to lowest + (median - lowest / 4), rounded to closest rouding limit.
1. Undercut price in seller's own country by the rounding limit if not contradicting 2)
1. Never go below the rounding limit for foils

## ✔️ Supported calls

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
* `add_stock`
* `delete_stock`
* `get_articles`
* `find_product`
* `find_stock_article`
* `find_user_articles`
