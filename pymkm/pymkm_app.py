#!/usr/bin/env python3
"""
The PyMKM example app.
"""

__author__ = "Andreas Ehrlund"
__version__ = "1.6.5"
__license__ = "MIT"

import csv
import json
import logging
import pprint
import uuid
import sys

import micromenu
import progressbar
import requests
import tabulate as tb
from pkg_resources import parse_version

from .pymkm_helper import PyMkmHelper
from .pymkmapi import PyMkmApi, api_wrapper, CardmarketError

ALLOW_REPORTING = True


class PyMkmApp:
    logging.basicConfig(stream=sys.stderr, level=logging.WARN)

    def __init__(self, config=None):
        if config is None:
            logging.debug(">> Loading config file")
            try:
                self.config = json.load(open("config.json"))
            except FileNotFoundError:
                logging.error(
                    "You must copy config_template.json to config.json and populate the fields."
                )
                sys.exit(0)

            # if no UUID is present, generate one and add it to the file
            if "uuid" not in self.config:
                self.config["uuid"] = str(uuid.uuid4())
                with open("config.json", "w") as json_config_file:
                    json.dump(self.config, json_config_file, indent=2)
        else:
            self.config = config

        self.DEV_MODE = False
        try:
            self.DEV_MODE = self.config["dev_mode"]
        except Exception as err:
            pass

        self.api = PyMkmApi(config=self.config)

    def report(self, command):
        uuid = self.config["uuid"]

        if ALLOW_REPORTING and not self.DEV_MODE:
            try:
                r = requests.post(
                    "https://andli-stats-server.herokuapp.com/pymkm",
                    json={"command": command, "uuid": uuid, "version": __version__},
                )
            except Exception as err:
                pass

    def check_latest_version(self):
        latest_version = None
        try:
            r = requests.get("https://api.github.com/repos/andli/pymkm/releases/latest")
            latest_version = r.json()["tag_name"]
        except Exception as err:
            logging.error("Connection error with github.com")
        if parse_version(__version__) < parse_version(latest_version):
            return f"Go to Github and download version {latest_version}! It's better!"
        else:
            return None

    def start(self):
        message = self.check_latest_version()

        if hasattr(self, "DEV_MODE") and self.DEV_MODE:
            message = "dev mode"
        menu = micromenu.Menu(f"PyMKM {__version__}", message)

        menu.add_function_item(
            "Update stock prices", self.update_stock_prices_to_trend, {"api": self.api}
        )
        menu.add_function_item(
            "Update price for a product",
            self.update_product_to_trend,
            {"api": self.api},
        )
        menu.add_function_item(
            "List competition for a product",
            self.list_competition_for_product,
            {"api": self.api},
        )
        menu.add_function_item(
            "Find deals from a user", self.find_deals_from_user, {"api": self.api}
        )
        menu.add_function_item(
            "Show top 20 expensive items in stock",
            self.show_top_expensive_articles_in_stock,
            {"num_articles": 20, "api": self.api},
        )
        menu.add_function_item(
            "Wantslists cleanup suggestions",
            self.clean_purchased_from_wantslists,
            {"api": self.api},
        )
        menu.add_function_item(
            "Show account info", self.show_account_info, {"api": self.api}
        )
        menu.add_function_item(
            "Clear entire stock (WARNING)", self.clear_entire_stock, {"api": self.api}
        )
        menu.add_function_item(
            "Import stock from .\list.csv", self.import_from_csv, {"api": self.api}
        )

        menu.show()

    @api_wrapper
    def update_stock_prices_to_trend(self, api):
        """ This function updates all prices in the user's stock to TREND. """
        self.report("update stock price to trend")

        undercut_local_market = PyMkmHelper.prompt_bool(
            "Try to undercut local market? (slower, more requests)"
        )

        uploadable_json = self.calculate_new_prices_for_stock(
            undercut_local_market, api=self.api
        )

        if len(uploadable_json) > 0:

            self.display_price_changes_table(uploadable_json)

            if PyMkmHelper.prompt_bool("Do you want to update these prices?"):
                print("Updating prices...")
                api.set_stock(uploadable_json)
                print("Prices updated.")
            else:
                print("Prices not updated.")
        else:
            print("No prices to update.")

    @api_wrapper
    def update_product_to_trend(self, api):
        """ This function updates one product in the user's stock to TREND. """
        self.report("update product price to trend")

        search_string = PyMkmHelper.prompt_string("Search product name")
        sticky_price_char = self.config["sticky_price_char"]

        def filtered(stock_item):
            return stock_item["comments"].startswith(sticky_price_char)

        # if we find the sticky price marker, filter out articles

        filtered_articles = []
        try:
            articles = api.find_stock_article(search_string, 1)
            filtered_articles = [x for x in articles if not filtered(x)]
        except Exception as err:
            print(err)

        if not filtered_articles:
            print(f"{len(articles)} articles found, no editable prices.")
        else:
            if len(filtered_articles) > 1:
                article = self.select_from_list_of_articles(filtered_articles)
            else:
                article = filtered_articles[0]
                found_string = f"Found: {article['product']['enName']}"
                if article["product"].get("expansion"):
                    found_string += f"[{article['product'].get('expansion')}]."
                if article["isFoil"]:
                    found_string += f"[foil: {article['isFoil']}]."
                if article["comments"]:
                    found_string += f"[comment: {article['comments']}]."
                else:
                    found_string += "."
                print(found_string)

            undercut_local_market = PyMkmHelper.prompt_bool(
                "Try to undercut local market? (slower, more requests)"
            )

            r = self.get_article_with_updated_price(
                article, undercut_local_market, api=self.api
            )

            if r:
                self.draw_price_changes_table([r])

                print(
                    "\nTotal price difference: {}.".format(
                        str(
                            round(
                                sum(item["price_diff"] * item["count"] for item in [r]),
                                2,
                            )
                        )
                    )
                )

                if PyMkmHelper.prompt_bool("Do you want to update these prices?"):
                    # Update articles on MKM
                    print("Updating prices...")
                    api.set_stock([r])
                    print("Price updated.")
                else:
                    print("Prices not updated.")
            else:
                print("No prices to update.")

    @api_wrapper
    def list_competition_for_product(self, api):
        self.report("list competition for product")
        print("Note: does not support playsets, booster displays etc (yet).")

        search_string = PyMkmHelper.prompt_string("Search product name")
        is_foil = PyMkmHelper.prompt_bool("Foil?")

        try:
            result = api.find_product(
                search_string,
                **{
                    # 'exact ': 'true',
                    "idGame": 1,
                    "idLanguage": 1,
                    # TODO: Add Partial Content support
                    # TODO: Add language support
                },
            )
        except CardmarketError as err:
            print(err.mkm_msg())
            logging.debug(err.mkm_msg())
        else:
            if result:
                products = result["product"]

                stock_list_products = [
                    x["idProduct"] for x in self.get_stock_as_array(api=self.api)
                ]
                products = [
                    x for x in products if x["idProduct"] in stock_list_products
                ]

                if len(products) == 0:
                    print("No matching cards in stock.")
                else:
                    if len(products) > 1:
                        product = self.select_from_list_of_products(
                            [i for i in products if i["categoryName"] == "Magic Single"]
                        )
                    elif len(products) == 1:
                        product = products[0]

                    self.show_competition_for_product(
                        product["idProduct"], product["enName"], is_foil, api=self.api
                    )
            else:
                print("No results found.")

    @api_wrapper
    def find_deals_from_user(self, api):
        self.report("find deals from user")

        search_string = PyMkmHelper.prompt_string("Enter username")

        try:
            result = api.find_user_articles(search_string)
        except CardmarketError as err:
            print(err.mkm_msg())
            logging.debug(err.mkm_msg())
        else:
            filtered_articles = [x for x in result if x.get("price") > 1]
            # language from configured filter
            language_filter_string = self.config["search_filters"]["language"]
            if language_filter_string:
                language_filter_code = api.get_language_code_from_string(
                    language_filter_string
                )
                if language_filter_code:
                    filtered_articles = [
                        x
                        for x in filtered_articles
                        if x.get("language").get("idLanguage") == language_filter_code
                    ]

            sorted_articles = sorted(
                filtered_articles, key=lambda x: x["price"], reverse=True
            )
            print(
                f"User '{search_string}' has {len(sorted_articles)} articles that meet the criteria."
            )
            num_searches = int(
                PyMkmHelper.prompt_string(
                    f"Searching top X expensive cards for deals, choose X (1-{len(sorted_articles)})"
                )
            )
            if 1 <= num_searches <= len(sorted_articles):
                table_data = []

                index = 0
                bar = progressbar.ProgressBar(max_value=num_searches)
                for article in sorted_articles[:num_searches]:
                    condition = article.get("condition")
                    language = article.get("language").get("languageName")
                    foil = article.get("isFoil")
                    playset = article.get("isPlayset")
                    price = float(article["price"])

                    p = api.get_product(article["idProduct"])
                    name = p["product"]["enName"]
                    expansion = p["product"].get("expansion")
                    if expansion:
                        expansion_name = expansion.get("enName")
                    else:
                        expansion_name = "N/A"
                    if foil:
                        market_price = p["product"]["priceGuide"]["TRENDFOIL"]
                    else:
                        market_price = p["product"]["priceGuide"]["TREND"]
                    if market_price > 0:
                        price_diff = price - market_price
                        percent_deal = round(-100 * (price_diff / market_price))
                        if price_diff < -1 or percent_deal >= 10:
                            table_data.append(
                                [
                                    name,
                                    expansion_name,
                                    condition,
                                    language,
                                    "\u2713" if foil else "",
                                    "\u2713" if playset else "",
                                    price,
                                    market_price,
                                    price_diff,
                                    percent_deal,
                                ]
                            )

                    index += 1
                    bar.update(index)
                bar.finish()

                if table_data:
                    print("Found some interesting prices:")
                    print(
                        tb.tabulate(
                            sorted(table_data, key=lambda x: x[9], reverse=True),
                            headers=[
                                "Name",
                                "Expansion",
                                "Condition",
                                "Language",
                                "Foil",
                                "Playset",
                                "Price",
                                "Market price",
                                "Market diff",
                                "Deal %",
                            ],
                            tablefmt="simple",
                        )
                    )
                else:
                    print("Found no deals. :(")
            else:
                print("Invalid number.")

    @api_wrapper
    def show_top_expensive_articles_in_stock(self, num_articles, api):
        self.report("show top expensive in stock")

        stock_list = self.get_stock_as_array(api=self.api)
        table_data = []
        total_price = 0

        for article in stock_list:
            name = article["product"]["enName"]
            expansion = article.get("product").get("expansion")
            foil = article.get("isFoil")
            playset = article.get("isPlayset")
            language_code = article.get("language")
            language_name = language_code.get("languageName")
            price = article.get("price")
            table_data.append(
                [
                    name,
                    expansion,
                    "\u2713" if foil else "",
                    "\u2713" if playset else "",
                    language_name if language_code != 1 else "",
                    price,
                ]
            )
            total_price += price
        if len(stock_list) > 0:
            print(
                "Top {} most expensive articles in stock:\n".format(str(num_articles))
            )
            print(
                tb.tabulate(
                    sorted(table_data, key=lambda x: x[5], reverse=True)[:num_articles],
                    headers=[
                        "Name",
                        "Expansion",
                        "Foil",
                        "Playset",
                        "Language",
                        "Price",
                    ],
                    tablefmt="simple",
                )
            )
            print("\nTotal stock value: {}".format(str(total_price)))
        return None

    @api_wrapper
    def clean_purchased_from_wantslists(self, api):
        self.report("clean wantslists")
        print("This will show items in your wantslists you have already received.")

        wantslists_lists = []
        try:
            print("Gettings wantslists from Cardmarket...")
            result = api.get_wantslists()
            wantslists = {
                i["idWantslist"]: i["name"] for i in result if i["game"]["idGame"] == 1
            }
            wantslists_lists = {
                k: api.get_wantslist_items(k)["item"] for k, v in wantslists.items()
            }

            print("Gettings received orders from Cardmarket...")
            received_orders = api.get_orders("buyer", "received", start=1)
        except Exception as err:
            print(err)

        if wantslists_lists and received_orders:
            purchased_product_ids = []
            purchased_products = []
            for (
                order
            ) in received_orders:  # TODO: foil in purchase removes non-foil in wants
                purchased_product_ids.extend(
                    [i["idProduct"] for i in order.get("article")]
                )
                purchased_products.extend(
                    {
                        "id": i["idProduct"],
                        "foil": i.get("isFoil"),
                        "count": i["count"],
                        "date": order["state"]["dateReceived"],
                    }
                    for i in order.get("article")
                )
            purchased_products = sorted(
                purchased_products, key=lambda t: t["date"], reverse=True
            )

            total_number_of_items = sum([len(x) for x in wantslists_lists.values()])
            index = 0
            print("Matching received purchases with wantslists...")
            bar = progressbar.ProgressBar(max_value=total_number_of_items)
            matches = []
            for key, articles in wantslists_lists.items():

                for article in articles:
                    a_type = article.get("type")
                    a_foil = article.get("isFoil") == True
                    product_matches = []

                    if a_type == "metaproduct":
                        metaproduct = api.get_metaproduct(article.get("idMetaproduct"))
                        metaproduct_product_ids = [
                            i["idProduct"] for i in metaproduct["product"]
                        ]
                        product_matches = [
                            i
                            for i in purchased_products
                            if i["id"] in metaproduct_product_ids
                            and i["foil"] == a_foil
                        ]
                    else:
                        a_product_id = article.get("idProduct")
                        product_matches = [
                            i
                            for i in purchased_products
                            if i["id"] == a_product_id and i["foil"] == a_foil
                        ]

                    if product_matches:
                        match = {
                            "wantlist_id": key,
                            "wantlist_name": wantslists[key],
                            "date": product_matches[0]["date"],
                            "is_foil": a_foil,
                            "count": sum([x.get("count") for x in product_matches]),
                        }
                        if a_type == "product":
                            match.update(
                                {
                                    "product_id": a_product_id,
                                    "product_name": article.get("product").get(
                                        "enName"
                                    ),
                                    "expansion_name": article.get("product").get(
                                        "expansionName"
                                    ),
                                }
                            )
                        elif a_type == "metaproduct":
                            match.update(
                                {
                                    "metaproduct_id": article.get("idMetaproduct"),
                                    "product_name": article.get("metaproduct").get(
                                        "enName"
                                    ),
                                    "expansion_name": article.get("metaproduct").get(
                                        "expansionName"
                                    ),
                                }
                            )
                        matches.append(match)
                    index += 1
                    bar.update(index)
            bar.finish()

            print(
                tb.tabulate(
                    [
                        [
                            item["wantlist_name"],
                            item["count"],
                            "\u2713" if item["is_foil"] else "",
                            item["product_name"],
                            item["expansion_name"],
                            item["date"],
                        ]
                        for item in matches
                    ],
                    headers=[
                        "Wantlist",
                        "# bought",
                        "Foil",
                        "Name",
                        "Expansion",
                        "Date (last) received",
                    ],
                    tablefmt="simple",
                )
            )

    @api_wrapper
    def show_account_info(self, api):
        self.report("show account info")

        pp = pprint.PrettyPrinter()
        pp.pprint(api.get_account())

    @api_wrapper
    def clear_entire_stock(self, api):
        self.report("clear entire stock")

        stock_list = self.get_stock_as_array(api=self.api)
        if PyMkmHelper.prompt_bool(
            "Do you REALLY want to clear your entire stock ({} items)?".format(
                len(stock_list)
            )
        ):

            # for article in stock_list:
            # article['count'] = 0
            delete_list = [
                {"count": x["count"], "idArticle": x["idArticle"]} for x in stock_list
            ]

            api.delete_stock(delete_list)
            print("Stock cleared.")
        else:
            print("Aborted.")

    @api_wrapper
    def import_from_csv(self, api):
        self.report("import from csv")

        print(
            "Note the required format: Card, Set name, Quantity, Foil, Language (with header row)."
        )
        print("Cards are added in condition NM.")
        problem_cards = []
        with open("list.csv", newline="") as csvfile:
            csv_reader = csvfile.readlines()
            index = 0
            bar = progressbar.ProgressBar(max_value=(sum(1 for row in csv_reader)) - 1)
            csvfile.seek(0)
            for row in csv_reader:
                row = row.rstrip()
                row_array = row.split(",")
                if index > 0:
                    row_array = [x.strip('"') for x in row_array]
                    (name, set_name, count, foil, language, *other) = row_array
                    foil = True if foil.lower() == "foil" else False
                    if not self.match_card_and_add_stock(
                        api, name, set_name, count, foil, language, *other
                    ):
                        problem_cards.append(row_array)

                bar.update(index)
                index += 1
            bar.finish()
        if len(problem_cards) > 0:
            try:
                with open(
                    "failed_imports.csv", "w", newline="", encoding="utf-8"
                ) as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerows(problem_cards)
                print(
                    f"Wrote {len(problem_cards)} failed imports to failed_imports.csv"
                )
                print("Report failures as an issue in the pymkm GitHub repo, please!")
            except Exception as err:
                print(err.value)
        else:
            print("All cards added successfully")

    # End of menu item functions ============================================

    def match_card_and_add_stock(
        self, api, name, set_name, count, foil, language, *other
    ):
        if all(v != "" for v in [name, set_name, count]):
            try:
                possible_products = api.find_product(name, idGame="1")["product"]
            except CardmarketError as err:
                print(err.mkm_msg())
                logging.debug(err.mkm_msg())
            except Exception as err:
                return False
            else:
                product_match = [
                    x
                    for x in possible_products
                    if self.card_equals(x["enName"], x["expansionName"], name, set_name)
                    and x["categoryName"] == "Magic Single"
                ]
                if len(product_match) == 0:
                    # no viable match
                    return False
                elif len(product_match) == 1:
                    language_id = (
                        1 if language == "" else api.languages.index(language) + 1
                    )
                    price = self.get_price_for_product(
                        product_match[0]["idProduct"],
                        product_match[0]["rarity"],
                        product_match[0].get("condition"),
                        foil,
                        False,
                        language_id=language_id,
                        api=self.api,
                    )
                    card = {
                        "idProduct": product_match[0]["idProduct"],
                        "idLanguage": language_id,
                        "count": count,
                        "price": str(price),
                        "condition": "NM",
                        "isFoil": ("true" if foil else "false"),
                    }
                    api.add_stock([card])
                    return True
                else:
                    # no single matching card
                    return False
        else:
            # incomplete data from card scanner
            return False

    def card_equals(self, db_cardname, db_setname, local_cardname, local_setname):
        # TODO: add some sort of string distance like Levenshtein
        filtered_db_cardname = db_cardname.replace(",", "")
        filtered_db_cardname = filtered_db_cardname.replace("Æ", "Ae")

        if db_setname != local_setname:
            return False
        else:
            # filter for flip card / split card names
            if filtered_db_cardname == local_cardname or (
                "/" in filtered_db_cardname
                and filtered_db_cardname.startswith(local_cardname)
            ):
                return True
            else:
                return False

    def select_from_list_of_wantslists(self, wantslists):
        index = 1
        filtered_wantslists = [
            i for i in wantslists["wantslist"] if i["game"]["idGame"] == 1
        ]
        for wl in filtered_wantslists:
            print(f"{index}: {wl['name']} [{wl['itemCount']}]")
            index += 1
        choice = int(input("Choose wantslist: "))
        return wantslists[choice - 1]

    def select_from_list_of_products(self, products):
        index = 1
        for product in products:
            print(
                "{}: {} [{}] {}".format(
                    index,
                    product["enName"],
                    product["expansionName"],
                    product["rarity"],
                )
            )
            index += 1
        choice = int(input("Choose card: "))
        return products[choice - 1]

    def select_from_list_of_articles(self, articles):
        index = 1
        for article in articles:
            product = article["product"]
            print(
                f'{index}: {product["enName"]}[{product["expansion"]}], foil: {article["isFoil"]}, comment: {article["comments"]}'
            )
            index += 1
        choice = int(input("Choose card: "))
        return articles[choice - 1]

    def show_competition_for_product(self, product_id, product_name, is_foil, api):
        print("Found product: {}".format(product_name))
        table_data_local, table_data = self.get_competition(api, product_id, is_foil)
        if table_data_local:
            self.print_product_top_list("Local competition:", table_data_local, 4, 20)
        if table_data:
            self.print_product_top_list("Top 20 cheapest:", table_data, 4, 20)
        else:
            print("No prices found.")

    def get_competition(self, api, product_id, is_foil):
        # TODO: Add support for playsets
        # TODO: Add support for card condition
        account = api.get_account()["account"]
        country_code = account["country"]
        articles = api.get_articles(
            product_id,
            **{
                "isFoil": str(is_foil).lower(),
                "isAltered": "false",
                "isSigned": "false",
                "minCondition": "EX",
                "country": country_code,
                "idLanguage": 1,
            },
        )
        table_data = []
        table_data_local = []
        for article in articles:
            username = article["seller"]["username"]
            if article["seller"]["username"] == account["username"]:
                username = "-> " + username
            item = [
                username,
                article["seller"]["address"]["country"],
                article["condition"],
                article["count"],
                article["price"],
            ]
            if article["seller"]["address"]["country"] == country_code:
                table_data_local.append(item)
            table_data.append(item)
        return table_data_local, table_data

    def print_product_top_list(self, title_string, table_data, sort_column, rows):
        print(70 * "-")
        print("{} \n".format(title_string))
        print(
            tb.tabulate(
                sorted(table_data, key=lambda x: x[sort_column], reverse=False)[:rows],
                headers=["Username", "Country", "Condition", "Count", "Price"],
                tablefmt="simple",
            )
        )
        print(70 * "-")
        print(
            "Total average price: {}, Total median price: {}, Total # of articles: {}\n".format(
                str(PyMkmHelper.calculate_average(table_data, 3, 4)),
                str(PyMkmHelper.calculate_median(table_data, 3, 4)),
                str(len(table_data)),
            )
        )

    def calculate_new_prices_for_stock(self, undercut_local_market, api):
        stock_list = self.get_stock_as_array(api=self.api)
        # HACK: filter out a foil product
        sticky_price_char = self.config["sticky_price_char"]
        # if we find the sticky price marker, filter out articles
        def filtered(stock_item):
            return stock_item["comments"].startswith(sticky_price_char)

        filtered_stock_list = [x for x in stock_list if not filtered(x)]

        result_json = []
        total_price = 0
        index = 0

        bar = progressbar.ProgressBar(max_value=len(filtered_stock_list))
        for article in filtered_stock_list:
            updated_article = self.get_article_with_updated_price(
                article, undercut_local_market, api=self.api
            )
            if updated_article:
                result_json.append(updated_article)
                total_price += updated_article.get("price")
            else:
                total_price += article.get("price")
            index += 1
            bar.update(index)
        bar.finish()

        print("Total stock value: {}".format(str(round(total_price, 2))))
        if len(stock_list) != len(filtered_stock_list):
            print(
                f"Note: {len(stock_list) - len(filtered_stock_list)} items filtered out because of sticky prices."
            )
        return result_json

    def get_article_with_updated_price(
        self, article, undercut_local_market=False, api=None
    ):
        # TODO: compare prices also for signed cards, like foils
        # keep prices for signed cards fixed
        if not article.get("isSigned"):

            new_price = self.get_price_for_product(
                article["idProduct"],
                article["product"].get("rarity"),
                article.get("condition"),
                article.get("isFoil", False),
                article.get("isPlayset"),
                language_id=article["language"]["idLanguage"],
                undercut_local_market=undercut_local_market,
                api=self.api,
            )
            if new_price:
                price_diff = new_price - article["price"]
                if price_diff != 0:
                    return {
                        "name": article["product"]["enName"],
                        "foil": article.get("isFoil", False),
                        "playset": article.get("isPlayset"),
                        "old_price": article["price"],
                        "price": new_price,
                        "price_diff": price_diff,
                        "idArticle": article["idArticle"],
                        "count": article["count"],
                    }

    def get_rounding_limit_for_rarity(self, rarity):
        rounding_limit = float(self.config["price_limit_by_rarity"]["default"])

        try:
            rounding_limit = float(self.config["price_limit_by_rarity"][rarity.lower()])
        except KeyError as err:
            print(f"ERROR: Unknown rarity '{rarity}'. Using default rounding.")
        return rounding_limit

    def get_discount_for_condition(self, condition):
        try:
            discount = float(self.config["discount_by_condition"][condition])
        except KeyError as err:
            print(f"ERROR: Unknown condition '{condition}'.")
            raise err
        else:
            return discount

    def get_price_for_product(
        self,
        product_id,
        rarity,
        condition,
        is_foil,
        is_playset,
        language_id=1,
        undercut_local_market=False,
        api=None,
    ):
        rounding_limit = self.get_rounding_limit_for_rarity(rarity)

        try:
            response = api.get_product(product_id)
        except Exception as err:
            print("No response from API.")
            sys.exit(0)

        if response:
            if not is_foil:
                trend_price = response["product"]["priceGuide"]["TREND"]
            else:
                trend_price = response["product"]["priceGuide"]["TRENDFOIL"]

            # Set competitive price for region
            if undercut_local_market:
                table_data_local, table_data = self.get_competition(
                    api, product_id, is_foil
                )

                if len(table_data_local) > 0:
                    # Undercut if there is local competition
                    lowest_in_country = PyMkmHelper.get_lowest_price_from_table(
                        table_data_local, 4
                    )
                    new_price = max(
                        rounding_limit,
                        min(trend_price, lowest_in_country - rounding_limit),
                    )
                else:
                    # No competition in our country, set price a bit higher.
                    new_price = trend_price * 1.2

            else:  # don't try to undercut local market
                new_price = trend_price

            if new_price is None:
                raise ValueError("No price found!")
            else:
                if is_playset:
                    new_price = 4 * new_price

                old_price = new_price
                # Apply condition discount
                if condition:
                    new_price = new_price * self.get_discount_for_condition(condition)

                # Round
                new_price = PyMkmHelper.round_up_to_multiple_of_lower_limit(
                    rounding_limit, new_price
                )

                return new_price
        else:
            print("No results.")

    def display_price_changes_table(self, changes_json):
        # table breaks because of progress bar rendering
        print("\nBest diffs:\n")
        sorted_best = sorted(changes_json, key=lambda x: x["price_diff"], reverse=True)[
            :10
        ]
        self.draw_price_changes_table(i for i in sorted_best if i["price_diff"] > 0)
        print("\nWorst diffs:\n")
        sorted_worst = sorted(changes_json, key=lambda x: x["price_diff"])[:10]
        self.draw_price_changes_table(i for i in sorted_worst if i["price_diff"] < 0)

        print(
            "\nTotal price difference: {}.".format(
                str(
                    round(
                        sum(item["price_diff"] * item["count"] for item in sorted_best),
                        2,
                    )
                )
            )
        )

    def draw_price_changes_table(self, sorted_best):
        print(
            tb.tabulate(
                [
                    [
                        item["count"],
                        item["name"],
                        "\u2713" if item["foil"] else "",
                        "\u2713" if item["playset"] else "",
                        item["old_price"],
                        item["price"],
                        item["price_diff"],
                    ]
                    for item in sorted_best
                ],
                headers=[
                    "Count",
                    "Name",
                    "Foil",
                    "Playset",
                    "Old price",
                    "New price",
                    "Diff",
                ],
                tablefmt="simple",
            )
        )

    def get_stock_as_array(self, api):
        try:
            d = api.get_stock()
        except Exception as err:
            print("No response from API.")
            sys.exit(0)
        else:
            keys = [
                "idArticle",
                "idProduct",
                "product",
                "count",
                "comments",
                "price",
                "condition",
                "isFoil",
                "isPlayset",
                "isSigned",
                "language",
            ]  # TODO: [language][languageId]
            stock_list = [
                {x: y for x, y in article.items() if x in keys} for article in d
            ]
            return stock_list
