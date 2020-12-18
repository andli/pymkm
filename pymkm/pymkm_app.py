#!/usr/bin/env python3
"""
The PyMKM example app.
"""

__author__ = "Andreas Ehrlund"
__version__ = "2.2.0"
__license__ = "MIT"

import csv
import json
import logging
import logging.handlers
import pprint
import uuid
import sys
import re
import pkg_resources

import micromenu
import progressbar
import requests
import tabulate as tb

from datetime import datetime
from pkg_resources import parse_version

from .pymkm_helper import PyMkmHelper, timeit
from .pymkmapi import PyMkmApi, CardmarketError


class PyMkmApp:
    logger = None

    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh = logging.handlers.RotatingFileHandler(
            f"log_pymkm.log", maxBytes=500000, backupCount=2
        )
        fh.setLevel(logging.WARNING)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setLevel(logging.ERROR)  # This gets outputted to stdout
        sh.setFormatter(formatter)
        self.logger.addHandler(sh)

        # Check that dependencies are ok
        micromenu_version = parse_version(
            pkg_resources.get_distribution("micromenu").version
        )
        needed_micromenu_version = micromenu_version
        with open("requirements.txt", "r") as file:
            for line in file.readlines():
                if line.startswith("micromenu"):
                    needed_micromenu_version = parse_version(
                        re.search(r"([\d.]+)", line).group(1)
                    )
        if micromenu_version < needed_micromenu_version:
            print("Dependencies for PyMkm need updating, run:")
            print("pip install --upgrade -r requirements.txt")
            sys.exit(0)

        if config is None:
            self.logger.debug(">> Loading config file")
            try:
                with open("config.json", "r") as config_file:
                    self.config = json.load(config_file)

                # Sync missing attributes to active config
                with open("config_template.json", "r") as template_config_file:
                    template_config = json.load(template_config_file)
                # template_config.update(self.config)
                PyMkmHelper.update_recursive(self.config, template_config)
                # self.config = template_config
            except FileNotFoundError:
                self.logger.error(
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

        fh.setLevel(self.config["log_level"])
        self.logger.setLevel(self.config["log_level"])
        self.api = PyMkmApi(config=self.config)
        print("Fetching Cardmarket account data...")
        self.account = self.get_account_data(
            self.api, log_time_label="Fetching account data"
        )

    @timeit
    def get_account_data(self, api, **kwargs):
        return api.get_account()["account"]

    def check_latest_version(self):
        latest_version = None
        try:
            r = requests.get(
                "https://api.github.com/repos/andli/pymkm/releases/latest"
            ).json()
            latest_version = r["tag_name"]
        except Exception as err:
            self.logger.error("Connection error with github.com")
        if parse_version(__version__) < parse_version(latest_version):
            return f"Go to Github and download version {latest_version}! It's better!"
        else:
            return None

    def start(self, args=None):

        if "--cached" not in sys.argv:  # if command line args have not been passed
            while True:
                stock_status = ""
                num_stock = PyMkmHelper.read_from_cache(
                    self.config["local_cache_filename"], "stock"
                )

                num_already_checked = PyMkmHelper.read_from_cache(
                    self.config["local_cache_filename"], "partial_updated"
                )

                if num_stock and not num_already_checked:
                    stock_status = f"({len(num_stock)} items)"
                if num_stock and num_already_checked:
                    stock_status = f"({len(num_already_checked)}/{len(num_stock)} done)"

                top_message = self.check_latest_version()

                if hasattr(self, "DEV_MODE") and self.DEV_MODE:
                    top_message = "dev mode"
                menu = micromenu.Menu(
                    f"PyMKM {__version__}", top_message, cycle=False, min_width=50,
                )

                menu.add_message_bottom_row(
                    f"{self.account['name']['firstName']} {self.account['name']['lastName']} ({self.account['username']})"
                )
                menu.add_message_bottom_row(
                    f"API calls used today: {self.api.requests_count}/{self.api.requests_max}"
                )

                menu.add_function_item(
                    f"Update stock prices {stock_status}",
                    self.update_stock_prices_to_trend,
                    {"api": self.api, "cli_called": False},
                    uid="updatestockprices",
                )
                menu.add_function_item(
                    "Update price for a product",
                    self.update_product_to_trend,
                    {"api": self.api},
                    uid="update1product",
                )
                menu.add_function_item(
                    "Find deals from a user",
                    self.find_deals_from_user,
                    {"api": self.api},
                    uid="finddeals",
                )
                menu.add_function_item(
                    f"Show top {self.config['show_top_x_expensive_items']} expensive items in stock",
                    self.show_top_expensive_articles_in_stock,
                    {
                        "num_articles": self.config["show_top_x_expensive_items"],
                        "api": self.api,
                    },
                    uid="showtopx",
                )
                menu.add_function_item(
                    "Wantslists cleanup suggestions",
                    self.clean_purchased_from_wantslists,
                    {"api": self.api},
                    uid="wantslistscleanup",
                )
                menu.add_function_item(
                    "Clear partial updates",
                    self.clear_partial_updates,
                    {"api": self.api},
                    uid="clearpartial",
                )
                menu.add_function_item(
                    "Clear entire stock",
                    self.clear_entire_stock,
                    {"api": self.api},
                    uid="clearstock",
                )
                menu.add_function_item(
                    f"Import stock from {self.config['csv_import_filename']}",
                    self.import_from_csv,
                    {"api": self.api},
                    uid="importcsv",
                )
                menu.add_function_item(
                    f"Track price data to {self.config['csv_prices_filename']}",
                    self.track_prices_to_csv,
                    {"api": self.api},
                    uid="trackprices",
                )
                if self.DEV_MODE:
                    menu.add_divider()
                    menu.add_function_item(
                        f"⚠ Check product id",
                        self.check_product_id,
                        {"api": self.api},
                        uid="checkpid",
                    )
                    menu.add_function_item(
                        f"⚠ Add fake stock",
                        self.add_fake_stock,
                        {"api": self.api},
                        uid="addfakestock",
                    )
                    menu.add_function_item(
                        f"⚠ Backup stock",
                        self.stock_backup_to_cache,
                        {"api": self.api},
                        uid="backupstock",
                    )
                    menu.add_function_item(
                        f"⚠ Restore stock",
                        self.stock_restore_from_cache,
                        {"api": self.api},
                        uid="restorestock",
                    )
                if self.api.requests_count < self.api.requests_max:
                    break_signal = menu.show()
                else:
                    menu.print_menu()
                    self.logger.error("Out of quota, exiting app.")
                    sys.exit(0)
                if break_signal:
                    break
        else:
            # command line interface
            if args.price_check_wantslist:
                self.track_prices_to_csv(
                    self.api, args.price_check_wantslist, args.cached
                )
            if args.update_stock:
                self.update_stock_prices_to_trend(
                    self.api, args.update_stock, args.cached, args.partial
                )

    def check_product_id(self, api):
        """ Dev function check on a product id. """
        pid = int(PyMkmHelper.prompt_string("pid"))
        product_json = api.get_product(pid)
        if "reprint" in product_json["product"]:
            del product_json["product"]["reprint"]
        del product_json["product"]["links"]
        pp = pprint.PrettyPrinter()
        pp.pprint(product_json)

    def stock_backup_to_cache(self, api):
        if PyMkmHelper.prompt_bool("Sure?"):
            print("Backing up cached stock...")
            PyMkmHelper.store_to_cache(
                self.config["local_cache_filename"],
                "stock_backup",
                PyMkmHelper.read_from_cache(
                    self.config["local_cache_filename"], "stock"
                ),
            )
            print("Done.")

    def stock_restore_from_cache(self, api):
        if PyMkmHelper.prompt_bool("Sure?"):
            print("Restoring cached stock...")
            PyMkmHelper.store_to_cache(
                self.config["local_cache_filename"],
                "stock",
                PyMkmHelper.read_from_cache(
                    self.config["local_cache_filename"], "stock_backup"
                ),
            )

            new_stock = PyMkmHelper.read_from_cache(
                self.config["local_cache_filename"], "stock"
            )

            for article in new_stock:
                del article["idArticle"]

            api.add_stock(new_stock)

            print("Done.")

    def add_fake_stock(self, api):
        """ Dev function to add fake stock. """
        range_start = int(PyMkmHelper.prompt_string("Range pid start"))
        range_end = int(PyMkmHelper.prompt_string("Range pid end"))
        if PyMkmHelper.prompt_bool("Sure?"):
            print("Adding fake stock...")
            product_list = []
            for product_no in range(range_start, range_end):
                product_list.append(
                    {
                        "idProduct": product_no,
                        "idLanguage": 1,
                        "count": 1,
                        "price": 1,
                        "comments": "TEST ARTICLE DO NOT BUY",
                        "condition": "PO",
                        "isFoil": "false",
                    }
                )

            api.add_stock(product_list)

    def get_stock_as_file_to_cache(self, api, log_time_label="Fetching stock as file"):
        # print("Fetching stock gzip file...")
        stock = api.get_stock_file()

        unused_attributes = [
            "Exp.",
            "Exp. Name",
            "Altered?",
            "onSale",
            "idCurrency",
            "Currency Code",
        ]

        regular_stock_keys_mapping = {
            "idArticle": "idArticle",
            "idProduct": "idProduct",
            "Amount": "count",
            "Comments": "comments",
            "Price": "price",
            "Condition": "condition",
            "Foil?": "isFoil",
            "Playset?": "isPlayset",
            "Signed?": "isSigned",
            "Language": "idLanguage",
        }
        stock_list = [
            {
                regular_stock_keys_mapping[x]: y
                for x, y in article.items()
                if x in regular_stock_keys_mapping
            }
            for article in stock
        ]
        # construct the 'product' entity for each article
        for article in stock_list:
            for k, v in article.items():
                try:
                    article[k] = PyMkmHelper.string_to_float_or_int(v)
                except ValueError as err:
                    article[k] = v
                    continue

            def map_stock_item(to_string, from_string):
                try:
                    return {
                        to_string: next(
                            x[from_string]
                            for x in stock
                            if int(x["idArticle"]) == article["idArticle"]
                        )
                    }
                except StopIteration:
                    return {to_string: ""}

            product_item = {}
            product_item.update(map_stock_item("enName", "English Name"))
            product_item.update(map_stock_item("locName", "Local Name"))
            product_item.update(map_stock_item("expansion", "Exp. Name"))

            article["product"] = product_item

        print("Stock fetched (using gzipped data).")

        PyMkmHelper.store_to_cache(
            self.config["local_cache_filename"], "stock", stock_list
        )
        return PyMkmHelper.read_from_cache(self.config["local_cache_filename"], "stock")

    def clean_json_for_upload(self, not_uploadable_json):
        for entry in not_uploadable_json:
            del entry["price_diff"]
            del entry["old_price"]
            del entry["name"]
        return not_uploadable_json

    def update_stock_prices_to_trend(self, api, cli_called, cached=None, partial=0):
        """ This function updates all prices in the user's stock to TREND. """

        stock_list = self.get_stock_as_array(
            self.api, cli_called, cached, log_time_label="Fetching stock"
        )

        if stock_list:

            already_checked_articles = PyMkmHelper.read_from_cache(
                self.config["local_cache_filename"], "partial_updated"
            )

            if already_checked_articles:
                print(
                    f"{len(already_checked_articles)} articles found in previous updates, ignoring those."
                )

            partial_stock_update_size = 0
            if partial > 0:
                partial_stock_update_size = partial
            elif not cli_called:
                partial_status_string = ""
                if already_checked_articles:
                    partial_status_string = (
                        f"({len(already_checked_articles)}/{len(stock_list)} done)"
                    )
                partial_stock_update_size = PyMkmHelper.prompt_string(
                    f"Partial update? {partial_status_string} \n"
                    + "If so, enter number of cards (or press Enter to update all remaining stock)"
                )

                if partial_stock_update_size != "":
                    partial_stock_update_size = int(partial_stock_update_size)
                else:
                    partial_stock_update_size = 0

            if cli_called or not self.config["enable_undercut_local_market"]:
                undercut_local_market = False
            else:
                undercut_local_market = PyMkmHelper.prompt_bool(
                    "Try to undercut local market? (slower, more requests)"
                )

            (
                uploadable_json,
                checked_articles,
                num_filtered_articles,
            ) = self.calculate_new_prices_for_stock(
                stock_list,
                undercut_local_market,
                partial_stock_update_size,
                already_checked_articles,
                api=self.api,
            )

            cache_size = 0
            if checked_articles:  # TODO: subtract the sticky prices
                cache_size = PyMkmHelper.append_to_cache(
                    self.config["local_cache_filename"],
                    "partial_updated",
                    checked_articles,
                )
                if cache_size + num_filtered_articles == len(stock_list):
                    print(f"Entire stock updated in partial updates.")
                    PyMkmHelper.clear_cache(
                        self.config["local_cache_filename"], "partial_updated"
                    )

            if len(uploadable_json) > 0:

                self.display_price_changes_table(uploadable_json)

                if cli_called or PyMkmHelper.prompt_bool(
                    "Do you want to update these prices?"
                ):
                    print("Updating prices...")
                    api.set_stock(uploadable_json)
                    print("Prices updated.")
                else:
                    print("Prices not updated.")
            else:
                print("No prices to update.")
        else:
            print("No stock to update.")

        self.logger.debug("-> update_stock_prices_to_trend: Done")

    def __filter_sticky(self, article_list):
        sticky_price_char = self.config["sticky_price_char"]
        # if we find the sticky price marker, filter out articles
        def filtered(stock_item):
            if stock_item.get("comments"):
                return stock_item.get("comments").startswith(sticky_price_char)
            else:
                return False

        filtered_articles = [x for x in article_list if not filtered(x)]
        return filtered_articles

    def __filter_language_data(self, article_list):
        for article in article_list:
            article["idLanguage"] = article["language"]["idLanguage"]
            del article["language"]
        return article_list

    def update_product_to_trend(self, api):
        """ This function updates one product in the user's stock to TREND. """

        search_string = PyMkmHelper.prompt_string("Search product name")

        articles = None
        try:
            articles = api.find_stock_article(search_string, 1)
        except Exception as err:
            self.logger.error(err)

        if articles:
            filtered_articles = self.__filter_sticky(articles)
            filtered_articles = self.__filter_language_data(articles)

            ### --- refactor?

            if not filtered_articles:
                print(f"{len(articles)} articles found, no editable prices.")
            else:
                if len(filtered_articles) > 1:
                    article = self.select_from_list_of_articles(filtered_articles)
                else:
                    article = filtered_articles[0]
                    found_string = f"Found: {article['product']['enName']} "
                    if article["product"].get("expansion"):
                        found_string += f"[{article['product'].get('expansion')}] "
                    if article["isFoil"]:
                        found_string += f"[foil: {article['isFoil']}] "
                    if article["comments"]:
                        found_string += f"[comment: {article['comments']}] "
                    else:
                        found_string += "."
                    print(found_string)

                undercut_local_market = False
                if self.config["enable_undercut_local_market"]:
                    undercut_local_market = PyMkmHelper.prompt_bool(
                        "Try to undercut local market? (slower, more requests)"
                    )

                product = self.api.get_product(article["idProduct"])
                r = self.update_price_for_article(
                    article, product, undercut_local_market, api=self.api
                )

                if r:
                    self.draw_price_changes_table([r])

                    print(
                        "\nTotal price difference: {}.".format(
                            str(
                                round(
                                    sum(
                                        item["price_diff"] * item["count"]
                                        for item in [r]
                                    ),
                                    2,
                                )
                            )
                        )
                    )

                    if PyMkmHelper.prompt_bool("Do you want to update these prices?"):
                        # Update articles on MKM
                        print("Updating prices...")
                        api.set_stock(self.clean_json_for_upload([r]))
                        print("Price updated.")
                    else:
                        print("Prices not updated.")
                else:
                    print("No prices to update.")

        self.logger.debug("-> update_product_to_trend: Done")

    def find_deals_from_user(self, api):
        search_string = PyMkmHelper.prompt_string("Enter username")

        try:
            print("Fetching user's stock...")
            result = api.find_user_articles(search_string)
        except CardmarketError as err:
            self.logger.error(err.mkm_msg())
            print(err.mkm_msg())
        else:
            if result:
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
                            if x.get("language").get("idLanguage")
                            == language_filter_code
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

                    products_to_get = []
                    index = 0
                    bar = progressbar.ProgressBar(max_value=num_searches)
                    bar.update(index)
                    products_to_get = [
                        x["idProduct"] for x in sorted_articles[:num_searches]
                    ]
                    products = api.get_items_async("products", products_to_get)

                    # remove any None results (probably caused by being booster boxes etc)
                    products = [x for x in products if x != None]

                    for article in sorted_articles[:num_searches]:
                        try:
                            p = next(
                                x
                                for x in products
                                if x["product"]["idProduct"] == article["idProduct"]
                            )
                        except StopIteration:
                            # Stock item not found in update batch, continuing
                            continue
                        name = p["product"]["enName"]
                        expansion = p["product"].get("expansion")
                        price = float(article["price"])
                        if expansion:
                            expansion_name = expansion.get("enName")
                        else:
                            expansion_name = "N/A"
                        if article.get("isFoil"):
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
                                        article.get("condition"),
                                        article.get("language").get("languageName"),
                                        "\u2713" if article.get("isFoil") else "",
                                        "\u2713" if article.get("isPlayset") else "",
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
        self.logger.debug("-> find_deals_from_user: Done")

    def show_top_expensive_articles_in_stock(self, num_articles, api):
        stock_list = self.get_stock_as_array(api=self.api)

        table_data = []
        total_price = 0

        for article in stock_list:
            name = article["product"]["enName"]
            expansion = article.get("product").get("expansion")
            foil = article.get("isFoil")
            playset = article.get("isPlayset")
            condition = article.get("condition")
            language_code = article.get("idLanguage")
            if isinstance(language_code, int):
                language_name = PyMkmApi.languages[int(language_code)]
            else:
                language_name = language_code.get("languageName")
            price = float(article.get("price"))
            table_data.append(
                [
                    name,
                    expansion,
                    "\u2713" if foil else "",
                    "\u2713" if playset else "",
                    language_name,
                    condition,
                    price,
                ]
            )
            total_price += price
        if len(table_data) > 0:
            print(
                f"Top {str(num_articles)} most expensive articles in stock (total {len(stock_list)} items):\n"
            )
            print(
                tb.tabulate(
                    sorted(table_data, key=lambda x: x[6], reverse=True)[:num_articles],
                    headers=[
                        "Name",
                        "Expansion",
                        "Foil",
                        "Playset",
                        "Language",
                        "Condition",
                        "Price",
                    ],
                    tablefmt="simple",
                )
            )
            print("\nTotal stock value: {}".format(str(total_price)))
        return None

    def track_prices_to_csv(self, api, wantslist_name=None, cached=False):
        wantslists, wantslists_lists = self.get_wantslists_data(api, cached)
        if wantslist_name is None:
            selected_list = self.select_from_list_of_wantslists(wantslists)
            selected_list_id = selected_list["idWantslist"]
        else:
            selected_list_id = next(
                x["idWantslist"] for x in wantslists if x["name"] == wantslist_name
            )

        # TODO: fails for metaproduct
        products_to_get = [
            x["idProduct"]
            for x in wantslists_lists[selected_list_id]
            if x["type"] == "product"
        ]
        for x in wantslists_lists[selected_list_id]:
            if x["type"] == "metaproduct":
                self.logger.warning(
                    f"Wantslist contains metaproduct ({x['metaproduct']['enName']}) which cannot be used to get prices."
                )

        updated_products = []
        try:
            updated_products = api.get_items_async("products", products_to_get)
        except Exception as err:
            self.logger.error(err)

        # Write to CSV:
        if len(updated_products) > 0:
            # if blank, then header: datetime, productid, priceguide labels
            example_priceguide = updated_products[0]["product"]["priceGuide"]
            priceguide_header_items = [k for k in example_priceguide.keys()]
            header_list = [
                "datetime",
                "product id",
                "name",
                "expansion",
            ]
            header_list.extend(priceguide_header_items)
            data_array = []
            for product in updated_products:
                price_data_exploded = [
                    k for k in product["product"]["priceGuide"].values()
                ]
                data_row = [
                    datetime.now().isoformat(" "),
                    product["product"]["idProduct"],
                    product["product"]["enName"],
                    product["product"]["expansion"]["enName"],
                ]
                data_row.extend(price_data_exploded)
                data_array.append(data_row)

            self.write_to_csv(header_list, data_array)

    def write_to_csv(self, header_list, data_array):
        if len(data_array) > 0:
            try:
                with open(
                    self.config["csv_prices_filename"],
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as csv_a, open(self.config["csv_prices_filename"], "r",) as csv_r:
                    csv_reader = csv.reader(csv_r)
                    row_count = sum(1 for row in csv_reader)
                    csv_writer = csv.writer(csv_a, delimiter=";")
                    if row_count == 0:
                        csv_writer.writerow(header_list)
                    csv_writer.writerows(data_array)
                self.logger.debug(
                    f"write_to_csv:: {len(data_array)} lines written to {self.config['csv_prices_filename']}."
                )
                print(
                    f"Wrote {len(data_array)} price updates to {self.config['csv_prices_filename']}."
                )
            except Exception as err:
                print(err.value)

    def clean_purchased_from_wantslists(self, api):
        print("This will show items in your wantslists you have already received.")

        wantslists, wantslists_lists = self.get_wantslists_data(
            api, log_time_label="Fetching wantslists"
        )

        received_orders = None
        try:
            print("Getting received orders from Cardmarket...")
            received_orders = api.get_orders("buyer", "received", start=1)
        except Exception as err:
            print(err)

        if wantslists_lists and received_orders:
            purchased_products = []
            for order in received_orders:
                # TODO: foil in purchase removes non-foil in wants
                def article_equals(a, b):
                    if a["idProduct"] == b["idProduct"] and a.get("isFoil") == b.get(
                        "isFoil"
                    ):
                        return True
                    else:
                        return False

                for article in order.get("article"):
                    if not any(article_equals(article, x) for x in purchased_products):
                        purchased_products.append(
                            {
                                "idProduct": article["idProduct"],
                                "foil": article.get("isFoil"),
                                "count": article["count"],
                                "date": order["state"]["dateReceived"],
                            }
                        )
                    else:
                        try:
                            hit = next(
                                x
                                for x in purchased_products
                                if article_equals(article, x)
                            )
                            hit["count"] += article["count"]
                        except StopIteration:
                            # Should not happen
                            continue

            # purchased_products = sorted(
            #     purchased_products, key=lambda t: t["date"], reverse=True
            # )

            total_number_of_items = sum([len(x) for x in wantslists_lists.values()])
            print("Matching received purchases with wantslists...")
            bar = progressbar.ProgressBar(max_value=total_number_of_items)
            matches = []
            for key, articles in wantslists_lists.items():
                current_wantslist = next(
                    (x for x in wantslists if x["idWantslist"] == key), None
                )

                metaproducts_article_list = [
                    x for x in articles if x.get("type") == "metaproduct"
                ]
                metaproducts_to_get = [
                    x["idMetaproduct"] for x in metaproducts_article_list
                ]
                metaproduct_list = api.get_items_async(
                    "metaproducts", metaproducts_to_get, bar
                )
                metaproduct_list = [x for x in metaproduct_list if x]

                for article in articles:
                    a_type = article.get("type")
                    a_foil = article.get("isFoil") == True
                    product_matches = []

                    if a_type == "metaproduct":
                        try:
                            metaproduct = next(
                                x
                                for x in metaproduct_list
                                if x["metaproduct"]["idMetaproduct"]
                                == article["idMetaproduct"]
                            )
                        except StopIteration:
                            # Stock item not found in update batch, continuing
                            continue

                        metaproduct_product_ids = [
                            i["idProduct"] for i in metaproduct["product"]
                        ]
                        product_matches = [
                            i
                            for i in purchased_products
                            if i["idProduct"] in metaproduct_product_ids
                            and i["foil"] == a_foil
                        ]
                    else:
                        product_matches = [
                            i
                            for i in purchased_products
                            if i["idProduct"] == article.get("idProduct")
                            and i["foil"] == a_foil
                        ]

                    if product_matches:
                        match = {
                            "wantlist_id": key,
                            "wantlist_name": current_wantslist["name"],
                            "date": product_matches[0]["date"],
                            "is_foil": a_foil,
                            "count": sum([x.get("count") for x in product_matches]),
                        }
                        if a_type == "product":
                            match.update(
                                {
                                    "product_id": article.get("idProduct"),
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
            bar.finish()

            if matches:
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
            else:
                print("No cleanup needed.")
        else:
            print("No wantslists or received orders.")

    def clear_partial_updates(self, api):
        print("Clearing partial update data...")
        PyMkmHelper.clear_cache(self.config["local_cache_filename"], "partial_updated")
        self.logger.debug("-> clear_partial_updates: done")
        print("Done.")

    def clear_entire_stock(self, api):

        stock_list = self.get_stock_as_array(
            api=self.api, log_time_label="Fetching stock"
        )
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

            print("Clearing stock...")
            api.delete_stock(delete_list)
            self.logger.debug("-> clear_entire_stock: done")

            PyMkmHelper.clear_cache(self.config["local_cache_filename"], "stock")
        else:
            print("Aborted.")

    def import_from_csv(self, api):
        print(
            "Note the required format: Card, Set name, Quantity, Foil, Language (with header row)."
        )
        problem_cards = []
        with open(self.config["csv_import_filename"], newline="") as csvfile:
            csv_reader = csvfile.readlines()
            index = 0
            card_rows = (sum(1 for row in csv_reader)) - 1
            bar = progressbar.ProgressBar(max_value=card_rows)
            self.logger.debug(f"-> import_from_csv: {card_rows} cards in csv file.")
            csvfile.seek(0)
            for row in csv_reader:
                row = row.rstrip()
                row_array = row.split(",")
                if index > 0:
                    row_array = [x.strip('"') for x in row_array]
                    try:
                        (name, set_name, count, foil, language, *other) = row_array
                    except Exception as err:
                        problem_cards.append(row_array)
                    else:
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
                self.logger.debug(
                    f"import_from_csv:: {len(problem_cards)} failed imports."
                )
                print(
                    f"Wrote {len(problem_cards)} failed imports to failed_imports.csv"
                )
                print("Report failures as an issue in the pymkm GitHub repo, please!")
            except Exception as err:
                print(err.value)
        else:
            print("All cards added successfully")

    # End of menu item functions ============================================

    @timeit
    def get_wantslists_data(self, api, cached=False, **kwargs):
        # Check for cached wantslists
        local_wantslists_cache = None
        local_wantslists_cache = PyMkmHelper.read_from_cache(
            self.config["local_cache_filename"], "wantslists"
        )
        local_wantslists_lists_cache = None
        local_wantslists_lists_cache = PyMkmHelper.read_from_cache(
            self.config["local_cache_filename"], "wantslists_lists"
        )

        if local_wantslists_cache:
            if cached or PyMkmHelper.prompt_bool(
                f"Cached wantslists ({len(local_wantslists_cache)} items) found, use it? (if not, then it will be cleared)"
            ):
                return local_wantslists_cache, local_wantslists_lists_cache
            else:
                PyMkmHelper.clear_cache(
                    self.config["local_cache_filename"], "wantslists"
                )
                PyMkmHelper.clear_cache(
                    self.config["local_cache_filename"], "wantslists_lists"
                )
                return self.get_wantslists_data(api)
        else:  # no local cache
            wantslists = []
            wantslists_lists = {}
            try:
                print("Gettings wantslists from Cardmarket...")
                wantslists = api.get_wantslists()
                wantslists_lists = {
                    item["idWantslist"]: api.get_wantslist_items(item["idWantslist"])[
                        "item"
                    ]
                    for item in wantslists
                }
            except Exception as err:
                print(err)

            PyMkmHelper.store_to_cache(
                self.config["local_cache_filename"], "wantslists", wantslists
            )
            PyMkmHelper.store_to_cache(
                self.config["local_cache_filename"],
                "wantslists_lists",
                wantslists_lists,
            )

            return wantslists, wantslists_lists

    def match_card_and_add_stock(
        self, api, name, set_name, count, foil, language, *other
    ):
        if all(v != "" for v in [name, set_name, count]):
            try:
                possible_products = api.find_product(name, idGame="1")  # ["product"]
            except CardmarketError as err:
                self.logger.error(err.mkm_msg())
                print(err.mkm_msg())
            except Exception as err:
                return False
            else:
                if len(possible_products) == 0:
                    # no viable match
                    return False
                else:
                    product_match = [
                        x
                        for x in possible_products
                        if x["categoryName"] == "Magic Single"
                        and self.card_equals(
                            x["enName"], x["expansionName"], name, set_name
                        )
                    ]
                    if len(product_match) == 1:
                        language_id = (
                            1 if language == "" else api.languages.index(language) + 1
                        )
                        product = api.get_product(product_match[0]["idProduct"])
                        price = self.get_price_for_product(
                            product,
                            product_match[0]["rarity"],
                            self.config["csv_import_condition"],
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
                            "condition": self.config["csv_import_condition"],
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
        for wantlist in wantslists:
            print(f"{index}: {wantlist['name']} ({wantlist['game']['abbreviation']})")
            index += 1
        choice = int(input("Choose wantslist: "))
        return wantslists[choice - 1]

    def select_from_list_of_products(self, products):
        index = 1
        for product in products:
            print(f"{index}: {product['enName']}")
            index += 1
        choice = ""
        while not isinstance(choice, int) or choice > len(products):
            try:
                choice = int(input("Choose card: "))
            except ValueError as err:
                print("Not a number.")
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

    def calculate_new_prices_for_stock(
        self,
        stock_list,
        undercut_local_market,
        partial_stock_update_size,
        already_checked_articles,
        api,
    ):
        filtered_stock_list = self.__filter_sticky(stock_list)

        sticky_count = len(stock_list) - len(filtered_stock_list)

        # articles_in_shoppingcarts = api.get_articles_in_shoppingcarts()

        if already_checked_articles:
            filtered_stock_list = [
                x
                for x in filtered_stock_list
                if x["idArticle"] not in already_checked_articles
            ]
            if len(filtered_stock_list) == 0:
                PyMkmHelper.clear_cache(
                    self.config["local_cache_filename"], "partial_updated"
                )
                print(
                    f"Entire stock updated in partial updates. Partial update data cleared."
                )
                return [], []
        if partial_stock_update_size:
            filtered_stock_list = filtered_stock_list[:partial_stock_update_size]

        result_json = []
        checked_articles = []
        total_price = 0

        # index = 0
        bar = progressbar.ProgressBar(max_value=len(filtered_stock_list))
        # bar.update(index)

        products_to_get = [x["idProduct"] for x in filtered_stock_list]
        product_list = api.get_items_async(
            "products", products_to_get, bar
        )  # TODO: pass bar in here?
        product_list = [x for x in product_list if x]

        for article in filtered_stock_list:
            try:
                product = next(
                    x
                    for x in product_list
                    if x["product"]["idProduct"] == article["idProduct"]
                )
            except StopIteration:
                # Stock item not found in update batch, continuing
                self.logger.error(
                    f"aid {article['idArticle']} pid {article['idProduct']} - {article['product']['enName']} {article['product']['expansion']} failed to find a product"
                )
                continue

            checked_articles.append(article.get("idArticle"))
            updated_article = self.update_price_for_article(
                article, product, undercut_local_market, api=self.api
            )
            if updated_article:
                result_json.append(updated_article)
                total_price += updated_article.get("price")
            else:
                total_price += article.get("price")
            # index += 1
            bar.update()
        bar.finish()

        print("Value in this update: {}".format(str(round(total_price, 2))))
        if len(stock_list) != len(filtered_stock_list):
            print(f"Note: {sticky_count} items filtered out because of sticky prices.")
        return result_json, checked_articles, sticky_count

    def update_price_for_article(
        self, article, product, undercut_local_market=False, api=None
    ):
        language_id = PyMkmHelper.string_to_float_or_int(article["idLanguage"])

        new_price = self.get_price_for_product(
            product,
            product["product"].get("rarity"),
            article.get("condition"),
            article.get("isFoil", False),
            article.get("isPlayset", False),
            language_id=language_id,
            undercut_local_market=undercut_local_market,
            api=self.api,
        )
        if new_price:
            price_diff = new_price - article["price"]
            if price_diff != 0:
                # table data created here
                return {
                    "name": article["product"]["enName"],
                    "expansion": article["product"]["expansion"],
                    "isFoil": article.get("isFoil", False),
                    "isPlayset": article.get("isPlayset", False),
                    "idLanguage": language_id,
                    "condition": article["condition"],
                    "old_price": article["price"],
                    "price": new_price,
                    "price_diff": price_diff,
                    "idArticle": article["idArticle"],
                    "count": article["count"],
                }

    def get_rounding_limit_for_rarity(self, rarity, product_id):
        rounding_limit = float(self.config["price_limit_by_rarity"]["default"])

        try:
            rounding_limit = float(self.config["price_limit_by_rarity"][rarity.lower()])
        except KeyError as err:
            self.logger.warning(f"Unknown rarity '{rarity}' (pid: {product_id}).")
        return rounding_limit

    def get_discount_for_condition(self, condition):
        try:
            discount = float(self.config["discount_by_condition"][condition])
        except KeyError as err:
            self.logger.error(f"Unknown condition '{condition}'.")
            raise err
        else:
            return discount

    def get_price_for_product(
        self,
        product,
        rarity,
        condition,
        is_foil,
        is_playset,
        language_id=1,
        undercut_local_market=False,
        api=None,
    ):
        rounding_limit = self.get_rounding_limit_for_rarity(
            rarity, product["product"]["idProduct"]
        )

        if not is_foil:
            trend_price = product["product"]["priceGuide"]["TREND"]
        else:
            trend_price = product["product"]["priceGuide"]["TRENDFOIL"]

        # Set competitive price for region
        if undercut_local_market:
            table_data_local, table_data = self.get_competition(
                api, product["product"]["idProduct"], is_foil
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

            return round(new_price, 2)

    def display_price_changes_table(self, changes_json):
        num_items = self.config["show_num_best_worst_items"]

        print("\nBest diffs:\n")
        sorted_best = sorted(changes_json, key=lambda x: x["price_diff"], reverse=True)[
            :num_items
        ]
        self.draw_price_changes_table(i for i in sorted_best if i["price_diff"] > 0)
        print("\nWorst diffs:\n")
        sorted_worst = sorted(changes_json, key=lambda x: x["price_diff"])[:num_items]
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
                        item["expansion"],
                        "\u2713" if item["isFoil"] else "",
                        "\u2713" if item["isPlayset"] else "",
                        item["condition"],
                        PyMkmApi.languages[item["idLanguage"]],
                        item["old_price"],
                        item["price"],
                        item["price_diff"],
                    ]
                    for item in sorted_best
                ],
                headers=[
                    "Count",
                    "Name",
                    "Expansion",
                    "Foil",
                    "Playset",
                    "Condition",
                    "Language",
                    "Old price",
                    "New price",
                    "Diff",
                ],
                tablefmt="simple",
            )
        )

    @timeit
    def get_stock_as_array(
        self, api, cli_called=False, cached=None, **kwargs,
    ):
        self.logger.debug("--> Fetching stock")
        print(f"Fetching stock...")

        # Check for cached stock
        local_stock_cache = None
        local_stock_cache = PyMkmHelper.read_from_cache(
            self.config["local_cache_filename"], "stock"
        )

        if not cli_called:
            if not local_stock_cache:
                return self.get_stock_as_file_to_cache(self.api)
            else:
                if PyMkmHelper.prompt_bool(
                    f"Cached stock ({len(local_stock_cache)} items) found, use it?"
                ):
                    return local_stock_cache
                else:
                    return self.get_stock_as_file_to_cache(self.api)
        else:
            if cached:
                return local_stock_cache
            else:
                return self.get_stock_as_file_to_cache(self.api)

