from pymkm.pymkm_calculators import AbstractPriceCalculator


class DiscountForGoblinsCalculator(AbstractPriceCalculator):
    GOBLIN_FACTOR: float = 0.8

    @classmethod
    def calculate_price(
        cls,
        is_foil: bool,
        is_playset: bool,
        condition: str,
        condition_discount: float,
        rounding_limit: float,
        card_info: dict,
    ) -> float:
        price = card_info["price"]

        if "goblin" in card_info["name"].lower():
            price *= cls.GOBLIN_FACTOR

        return price
