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


@patch("pymkm.pymkmapi.PyMkmApi.set_api_quota_attributes", new_callable=MagicMock())
class MockRequest:
    def __init__(self, url):
        self.url = url


class MockResponse:

    request = None

    def __init__(self, json_data, status_code, content):
        self.json_data = json_data
        self.status_code = status_code
        self.content = content
        self.request = MockRequest("test url")
        # TODO: write a test for these
        self.headers = {
            "X-Request-Limit-Count": 1234,
            "X-Request-Limit-Max": 5000,
            "Content-Range": "/100",
        }

    def json(self):
        return self.json_data


class TestCommon(unittest.TestCase):

    cardmarket_get_stock_result = {
        "article": [
            {
                "count": 1,
                "idArticle": 410480091,
                "idProduct": 1692,
                "isFoil": False,
                "isPlayset": False,
                "comments": "x",
                "isSigned": True,
                "language": {"idLanguage": 7, "languageName": "Japanese"},
                "price": 0.75,
                "condition": "NM",
                "product": {
                    "enName": "Words of Worship",
                    "expIcon": "39",
                    "expansion": "Onslaught",
                    "idGame": 1,
                    "image": "./img/items/1/ONS/1692.jpg",
                    "locName": "Words of Worship",
                    "nr": "61",
                    "rarity": "Rare",
                },
            },
            {
                "count": 1,
                "idArticle": 412259385,
                "idProduct": 9145,
                "isFoil": True,
                "isPlayset": False,
                "comments": "! poop",
                "isSigned": True,
                "language": {"idLanguage": 4, "languageName": "Spanish"},
                "price": 0.25,
                "condition": "NM",
                "product": {
                    "enName": "Mulch words",
                    "expIcon": "18",
                    "expansion": "Stronghold",
                    "idGame": 1,
                    "image": "./img/items/1/STH/9145.jpg",
                    "locName": "Estiércol y paja",
                    "nr": None,
                    "rarity": "Common",
                },
            },
            {
                "count": 1,
                "idArticle": 407911824,
                "idProduct": 1079,
                "isFoil": False,
                "isPlayset": False,
                "comments": "!",
                "isSigned": False,
                "language": {"idLanguage": 1, "languageName": "English"},
                "price": 0.5,
                "condition": "NM",
                "product": {
                    "enName": "Everflowing Chalice",
                    "expIcon": "164",
                    "expansion": "Duel Decks: Elspeth... Tezzeret",
                    "idGame": 1,
                    "image": "./img/items/1/DDF/242440.jpg",
                    "locName": "Everflowing Chalice",
                    "nr": "60",
                    "rarity": "Uncommon",
                },
            },
        ]
    }

    get_stock_result = cardmarket_get_stock_result["article"]

    fake_product_response = {
        "product": {
            "categoryName": "Magic Single",
            "countArticles": 876,
            "countFoils": 46,
            "countReprints": 1,
            "idProduct": 1692,
            "enName": "Words of Worship",
            "expansion": {
                "enName": "Onslaught",
                "expansionIcon": 39,
                "idExpansion": 41,
            },
            "gameName": "Magic the Gathering",
            "idGame": "1",
            "idMetaproduct": 6716,
            "priceGuide": {
                "AVG": 3.18,
                "LOW": 0.29,
                "LOWEX": 0.8,
                "LOWFOIL": 0.8,
                "SELL": 2.18,
                "TREND": 2.11,
                "TRENDFOIL": 2.07,
            },
        }
    }

    fake_product_list_response = [
        {
            "product": {
                "idProduct": 363551,
                "categoryName": "Magic Single",
                "enName": "Temple Garden",
                "gameName": "Magic the Gathering",
                "idGame": 1,
                "idMetaproduct": 8115,
                "priceGuide": {"TREND": 1},
            }
        },
        {
            "product": {
                "idProduct": 363554,
                "categoryName": "Magic Single",
                "enName": "Overgrown Tomb",
                "gameName": "Magic the Gathering",
                "idGame": 1,
                "idMetaproduct": 8044,
                "priceGuide": {"TREND": 1},
            }
        },
        {
            "product": {
                "idProduct": 1692,
                "categoryName": "Magic Single",
                "enName": "Yidaro, Wandering Mo...ster (V.2)",
                "gameName": "Magic the Gathering",
                "idGame": 1,
                "idMetaproduct": 300608,
                "priceGuide": {"TREND": 1},
            }
        },
    ]

    cardmarket_metaproduct_list_response = [
        {
            "metaproduct": {"enName": "Balthor the Defiled", "idMetaproduct": 429},
            "product": [{"idProduct": 2187, "idMetaproduct": 429}],
        },
        {
            "metaproduct": {
                "enName": "'Chainer, Nightmare Adept'",
                "idMetaproduct": 278802,
            },
            "product": [{"idProduct": 392362, "idMetaproduct": 278802}],
        },
    ]

    fake_list_csv = """Card,Set Name,Quantity,Foil,Language
Dragon Breath,Scourge,1,Foil,French"""

    fake_find_product_result_no_match = {
        "product": [
            {
                "categoryName": "Magic Single",
                "enName": "Dragon BreathXX",
                "expansionName": "Scourge",
                "idProduct": 9145,
                "rarity": "Rare",
            },
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "ScourgeXX",
                "idProduct": 9145,
                "rarity": "Rare",
            },
        ]
    }

    fake_find_product_result_one_match_of_3 = {
        "product": [
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "Scourge",
                "idProduct": 1079,
                "rarity": "Common",
            },
            {
                "categoryName": "Magic Single",
                "enName": "Dragon BreathXX",
                "expansionName": "Scourge",
                "idProduct": 9145,
                "rarity": "Rare",
            },
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "ScourgeXX",
                "idProduct": 1692,
                "rarity": "Rare",
            },
        ]
    }

    fake_find_product_result_one_match_only = {
        "product": [
            {
                "categoryName": "Magic Single",
                "enName": "Dragon Breath",
                "expansionName": "Scourge",
                "idProduct": 1079,
                "rarity": "Common",
            }
        ]
    }

    cardmarket_find_user_articles_result = {
        "article": [
            {
                "comments": "x",
                "condition": "EX",
                "count": 1,
                "idArticle": 371427479,
                "idProduct": 1692,
                "inShoppingCart": False,
                "isAltered": False,
                "isFoil": False,
                "isPlayset": False,
                "isSigned": False,
                "language": {"idLanguage": 1, "languageName": "English"},
                "price": 0.2,
                "seller": {
                    "address": {"country": 1},
                    "avgShippingTime": 1,
                    "email": "x",
                    "idUser": 34018,
                    "isCommercial": 0,
                    "isSeller": True,
                    "legalInformation": "x",
                    "lossPercentage": "0 - 2%",
                    "username": "test",
                },
            },
            {
                "comments": "!x",
                "condition": "EX",
                "count": 1,
                "idArticle": 406723464,
                "idProduct": 1692,
                "inShoppingCart": False,
                "isAltered": False,
                "isFoil": False,
                "isPlayset": False,
                "isSigned": False,
                "language": {"idLanguage": 1, "languageName": "English"},
                "price": 1.5,
                "seller": {
                    "address": {"country": 1},
                    "avgShippingTime": 0,
                    "email": "x",
                    "idUser": 655460,
                    "isCommercial": 0,
                    "isSeller": True,
                    "legalInformation": "x",
                    "lossPercentage": "0 - 2%",
                    "username": "test",
                },
            },
        ]
    }

    find_user_articles_result = cardmarket_find_user_articles_result["article"]

    fake_account_data = {
        "account": {
            "username": "test",
            "country": "test",
            "onVacation": True,
            "idDisplayLanguage": "1",
        },
        "message": "Successfully set the account on vacation.",
    }

    cardmarket_get_wantslists = {
        "wantslist": [
            {
                "game": {
                    "abbreviation": "MtG",
                    "idGame": 1,
                    "name": "Magic the Gathering",
                },
                "idWantslist": 2789285,
                "itemCount": 3,
                "name": "0 prio",
            },
            {
                "game": {
                    "abbreviation": "MtG",
                    "idGame": 1,
                    "name": "Magic the Gathering",
                },
                "idWantslist": 6106824,
                "itemCount": 36,
                "name": "cmd-musthave",
            },
        ]
    }

    get_wantslists = cardmarket_get_wantslists["wantslist"]

    cardmarket_get_wantslist_items = {
        "wantslist": {
            "idWantslist": 2789285,
            "game": {"idGame": 1, "name": "Magic the Gathering", "abbreviation": "MtG"},
            "name": "0 prio",
            "itemCount": 2,
            "item": [
                {
                    "idWant": "5ec4f6cf456a56266329f79c",
                    "count": 1,
                    "wishPrice": 0,
                    "fromPrice": 0.95,
                    "mailAlert": "false",
                    "type": "product",
                    "idProduct": 1637,
                    "product": {
                        "idProduct": 1637,
                        "idMetaproduct": 344,
                        "countReprints": 1,
                        "enName": "Aurification",
                        "locName": "Aurification",
                        "localization": [],
                        "website": "\\/en\\/Magic\\/Products\\/Singles\\/Onslaught\\/Aurification",
                        "image": "\\/\\/static.cardmarket.com\\/img\\/40b5efd939eda860937c1901755cb6fd\\/items\\/1\\/ONS\\/1637.jpg",
                        "gameName": "Magic the Gathering",
                        "categoryName": "Magic Single",
                        "idGame": 1,
                        "number": "6",
                        "rarity": "Rare",
                        "expansionName": "Onslaught",
                        "expansionIcon": 39,
                        "countArticles": 521,
                        "countFoils": 55,
                    },
                    "idLanguage": [1],
                    "minCondition": "NM",
                    "isFoil": "null",
                    "isSigned": "null",
                    "isAltered": "null",
                },
                {
                    "idWant": "5ecae829456a5605da4796dc",
                    "count": 4,
                    "wishPrice": 0,
                    "fromPrice": 0.1,
                    "mailAlert": "false",
                    "type": "product",
                    "idProduct": 431849,
                    "product": {
                        "idProduct": 431849,
                        "idMetaproduct": 208641,
                        "countReprints": 5,
                        "enName": "Gray Merchant of Asphodel",
                        "locName": "Gray Merchant of Asphodel",
                        "localization": [],
                        "website": "\\/en\\/Magic\\/Products\\/Singles\\/Theros-Beyond-Death-Promos\\/Gray-Merchant-of-Asphodel",
                        "image": "\\/\\/static.cardmarket.com\\/img\\/1e821b1745c6b8fa1ceeea8d3c975631\\/items\\/1\\/PTHB\\/431849.jpg",
                        "gameName": "Magic the Gathering",
                        "categoryName": "Magic Single",
                        "idGame": 1,
                        "number": "355",
                        "rarity": "Uncommon",
                        "expansionName": "Theros Beyond Death: Promos",
                        "expansionIcon": 179,
                        "countArticles": 1225,
                        "countFoils": 366,
                    },
                    "idLanguage": [1],
                    "minCondition": "NM",
                    "isFoil": "null",
                    "isSigned": "null",
                    "isAltered": "null",
                },
            ],
        },
        "links": [
            {"rel": "self", "href": "\\/wantslist\\/2789285", "method": "GET"},
            {"rel": "manage_items", "href": "\\/wantslist\\/2789285", "method": "PUT"},
            {
                "rel": "delete_list",
                "href": "\\/wantslist\\/2789285",
                "method": "DELETE",
            },
        ],
    }

    get_wantslist_items = cardmarket_get_wantslist_items["wantslist"]
    cardmarket_get_order_items = {
        "order": [
            {
                "idOrder": 22935635,
                "isBuyer": True,
                "seller": {"idUser": 764949, "username": "Versus-GC",},
                "buyer": {"idUser": 787453, "username": "andli826",},
                "state": {
                    "state": "evaluated",
                    "dateBought": "2020-05-16T00:49:51+0200",
                    "datePaid": "2020-05-16T00:49:58+0200",
                    "dateSent": "2020-05-18T18:11:48+0200",
                    "dateReceived": "2020-06-01T15:48:58+0200",
                },
                "shippingMethod": {
                    "idShippingMethod": 11425980,
                    "name": "Letter (Correio Normal)",
                    "price": 1.7,
                    "isLetter": True,
                    "isInsured": False,
                },
                "trackingNumber": "",
                "temporaryEmail": "",
                "isPresale": False,
                "shippingAddress": {"name": "Andreas Ehrlund",},
                "note": "",
                "articleCount": 4,
                "evaluation": {
                    "evaluationGrade": 1,
                    "itemDescription": 1,
                    "packaging": 1,
                    "comment": "Very nice quality cards!",
                },
                "article": [
                    {
                        "idArticle": 778922254,
                        "idProduct": 1637,
                        "language": {"idLanguage": 1, "languageName": "English"},
                        "comments": "",
                        "price": 1.5,
                        "count": 1,
                        "inShoppingCart": False,
                        "priceEUR": 1.5,
                        "priceGBP": 1.5,
                        "product": {
                            "idGame": 1,
                            "enName": "Aurification",
                            "locName": "Aurification",
                            "image": "//static.cardmarket.com/img/c21340a8e384bef0513bfcc9dbdf37e5/items/1/KTK/269545.jpg",
                            "expansion": "Onslaught",
                            "nr": "6",
                            "expIcon": 39,
                            "rarity": "Rare",
                        },
                        "condition": "EX",
                        "isFoil": False,
                        "isSigned": False,
                        "isPlayset": False,
                        "isAltered": False,
                    },
                    {
                        "idArticle": 778922259,
                        "idProduct": 296748,
                        "language": {"idLanguage": 1, "languageName": "English"},
                        "comments": "",
                        "price": 1.5,
                        "count": 1,
                        "inShoppingCart": False,
                        "priceEUR": 1.5,
                        "priceGBP": 1.5,
                        "product": {
                            "idGame": 1,
                            "enName": "Throne of the God-Pharaoh",
                            "locName": "Throne of the God-Pharaoh",
                            "image": "//static.cardmarket.com/img/aac5e13f076472092ab1297934042e21/items/1/AKH/296748.jpg",
                            "expansion": "Amonkhet",
                            "nr": "237",
                            "expIcon": 396,
                            "rarity": "Rare",
                        },
                        "condition": "EX",
                        "isFoil": False,
                        "isSigned": False,
                        "isPlayset": False,
                        "isAltered": False,
                    },
                ],
                "articleValue": 11,
                "totalValue": 12.7,
            }
        ]
    }
    get_order_items = cardmarket_get_order_items["order"]

    cardmarket_example_error_message = {
        "mkm_error_description": "Provide a search string for non-exact searches with at least 4 characters.",
        "internal_error_code": "null",
        "post_data_field": "null",
        "http_status_code": "400",
        "http_status_code_description": "Bad Request",
    }
    bad_request_response = MockResponse(
        cardmarket_example_error_message, 400, "Bad request"
    )
    ok_response = MockResponse("test", 200, "testing ok")
    fake_github_releases = MockResponse({"tag_name": "1.0.0"}, 200, "ok")

    def setUp(self):
        logging.disable(logging.CRITICAL)
        # CONFIG
        with open("test/test_config.json", "r") as f:
            self.config = json.load(f)

        self.patcher = patch("pymkm.pymkm_app.PyMkmApp.report")
        self.mock_report = self.patcher.start()

        self.patcher2 = patch("pymkm.pymkmapi.PyMkmApi.set_api_quota_attributes")
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()


if __name__ == "__main__":
    unittest.main()
