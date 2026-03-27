TAX_RATE = 0.1   # 10%
DISCOUNT_THRESHOLD = 1000.0
DISCOUNT_RATE = 0.05  # 5% for orders over threshold


def apply_discount(subtotal: float) -> float:
    # CORRECT: discount applied to subtotal (before tax)
    if subtotal >= DISCOUNT_THRESHOLD:
        return subtotal * (1 - DISCOUNT_RATE)
    return subtotal


def calculate_total(subtotal: float) -> float:
    discounted = apply_discount(subtotal)
    taxed = discounted * (1 + TAX_RATE)
    return round_currency(taxed)


def round_currency(amount: float) -> float:
    # BUG: string "2" instead of integer 2
    return round(amount, "2")
