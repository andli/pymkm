[![Build Status](https://travis-ci.org/andli/pymkm.svg?branch=master)](https://travis-ci.org/andli/pymkm) [![codecov](https://codecov.io/gh/andli/pymkm/branch/master/graph/badge.svg)](https://codecov.io/gh/andli/pymkm) [![Known Vulnerabilities](https://snyk.io/test/github/andli/pymkm/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/andli/pymkm?targetFile=requirements.txt) ![.github/workflows/main.yml](https://github.com/andli/pymkm/workflows/.github/workflows/main.yml/badge.svg?branch=master)

See the [Changelog](CHANGELOG.md) for what's new.

# 📙 PyMKM

Python wrapper for the [cardmarket.com API](https://api.cardmarket.com/ws/documentation/API_2.0:Main_Page) (version 2.0, using OAuth1 and the "Dedicated app" option).

The included sample app can update your stock prices to trend for non-foils, and to a competitive prices for foils, all rounded to nearest configurable value per rarity (default .25 €). A confirmation step allows you to check the result before uploading the new prices.

The app can import a .csv list of cards to your stock. It can also be used to clear your entire stock.
The app also keeps track of how many API requests your have left each day, and can do partial updates if you have more than 5000 articles to update.

**NOTE:** Use all functionality at your own risk, I take no responsibility for the resulting prices or wiped stock. See 'price calculation' below for more details.

**NOTE 2:** This app collects a tiny amount of usage data. The purpose is to allow me to see what people use the most and to focus on improving that. If you want to opt out from this, please change `"reporting": true` to `false` in `config.json`.

```
╭─── PyMKM 1.7.0 ────────────────────────────────────────╮
│ 1: Update stock prices                                 │
│ 2: Update price for a product                          │
│ 3: List competition for a product                      │
│ 4: Find deals from a user                              │
│ 5: Show top 20 expensive items in stock                │
│ 6: Wantslists cleanup suggestions                      │
│ 7: Show account info                                   │
│ 8: Clear entire stock (WARNING)                        │
│ 9: Import stock from .\list.csv                        │
│ 0: Exit                                                │
├────────────────────────────────────────────────────────┤
│ Remaining API calls today: 66/5000                     │
╰────────────────────────────────────────────────────────╯
Action number: 1
Try to undercut local market? (slower, more requests) [y/N]:

100% (74 of 74) |#########################################| Elapsed Time: 0:00:21 Time:  0:00:21
Total stock value: 49.25
Note: 2 items filtered out because of sticky prices.

Best diffs:

  Count  Name             Foil    Playset      Old price    New price    Diff
-------  ---------------  ------  ---------  -----------  -----------  ------
      1  Manaweft Sliver                            1.25          1.5    0.25

Worst diffs:

  Count  Name                              Foil    Playset      Old price    New price    Diff
-------  --------------------------------  ------  ---------  -----------  -----------  ------
      1  Shield of the Oversoul                                      1            0.75   -0.25
      1  Battle Sliver                             ✓                 1            0.75   -0.25
      2  Predatory Sliver                          ✓                 2            1.75   -0.25
      1  Kalemne, Disciple of Iroas (V.1)                            0.75         0.5    -0.25
      1  Foreboding Ruins                                            1.5          1.25   -0.25

Total price difference: -1.25.
Do you want to update these prices? [y/N]:
```

## 🔨 How

1. Install requirements using `pip install -r requirements.txt`
1. Copy `config_template.json` to `config.json` and fill in your API keys.
1. Run `pymkm.py`.
1. Profit.

## 📈 Price calculation

The prices for non-foils are the "trend" prices supplied by Cardmarket. I only look at English cards for now.
Cardmarket does not however supply trend prices for foils, so my algorithm is this:

_NOTE: This is a rough algorithm, designed to be safe and not to sell aggressively._

1. Filter out foils, English, not altered, not signed, minimum Good condition.
1. Set price to lowest + (median - lowest / 4), rounded to closest rouding limit.
1. Undercut price in seller's own country by the rounding limit if not contradicting 2)
1. Never go below the rounding limit for foils

Base prices (€) and discounts for lower grading (decimal %) can be set in `config.json`.

## 🔓 Locking prices

Should you want to avoid updating certain articles in your stock, set the starting character of the comment for that article to `!` (possible to change which character in `config.json`).

## ⚙️ Config parameters
| Variable     | Value                                                                                                        |
|--------------|--------------------------------------------------------------------------------------------------------------|
| language     | Specify a language to find deals from a specific user\.                                                                          |
| isAltered    | Determines if the card is altered\.                                                                          |
| isSigned     | Determines if the card is signed\.                                                                           |
| minCondition | Determines the minimal condition of a card\. \(see below for additional information\)                        |
| userType     | Only articles from sellers with the specified user type are returned\. \(private, commercial, powerseller\)  |
| idLanguage   | Only articles that match the given language are returned\. \(see below for additional information\)          |

#### minCondition
| Abbreviation | Condition                                      |
|--------------|------------------------------------------------|
| MT           | Mint                                           |
| NM           | Near Mint \(default value when not specified\) |
| EX           | Excellent                                      |
| GD           | Good                                           |
| LP           | Light\-played                                  |
| PL           | Played                                         |
| PO           | Poor                                           |

#### idLanguage
| ID | Language            |
|----|---------------------|
| 1  | English             |
| 2  | French              |
| 3  | German              |
| 4  | Spanish             |
| 5  | Italian             |
| 6  | Simplified Chinese  |
| 7  | Japanese            |
| 8  | Portuguese          |
| 9  | Russian             |
| 10 | Korean              |
| 11 | Traditional Chinese |


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

```
Action number: 3
Note: does not support playsets, booster displays etc (yet).
Search product name:
temple gar
Foil? [y/N]:

Found product: Temple Garden
----------------------------------------------------------------------
Local competition:

Username     Country    Condition      Count    Price
-----------  ---------  -----------  -------  -------
Karand       SE         NM                 1        6
-> testuser  SE         NM                 1       13
----------------------------------------------------------------------
Total average price: 9.5, Total median price: 9.5, Total # of articles: 2

----------------------------------------------------------------------
Top 20 cheapest:

Username         Country    Condition      Count    Price
---------------  ---------  -----------  -------  -------
syresatve        GR         NM                 1     4.9
Tromeck          ES         NM                 1     4.99
    <cut out rows to save vertical space in README.md>
peiraikos        GR         NM                 1     5.95
finespoo         FI         NM                 2     5.98
----------------------------------------------------------------------
Total average price: 9.82, Total median price: 7.79, Total # of articles: 320
```

## ✔️ Supported calls

These calls are implemented so far. They are not fully tested with different edge cases etc. Please submit an issue or pull request if you find problems.

- `get_games`
- `get_expansions`
- `get_cards_in_expansion`
- `get_product`
- `get_account`
- `get_articles_in_shoppingcarts`
- `set_vacation_status`
- `set_display_language`
- `get_stock`
- `set_stock`
- `add_stock`
- `delete_stock`
- `get_articles`
- `find_product`
- `find_stock_article`
- `find_user_articles`
