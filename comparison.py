"""
GoldWatch Agent - Date-Aware Price Comparison

Responsibilities:
- Compare gold prices using observation dates.
- Never treat retrieval date as the gold-price date.
- Calculate ₹ change and percentage change.
- Refuse comparison when a previous observation is unavailable.
"""

from database import get_recent_prices


def calculate_percentage_change(
    previous_price,
    current_price,
):
    """
    Calculate percentage change.
    """

    if previous_price == 0:
        return None

    return (
        (current_price - previous_price)
        / previous_price
    ) * 100


def get_comparison(purity):
    """
    Compare the two most recent observations
    for a given purity.
    """

    rows = get_recent_prices(
        purity=purity,
        limit=2,
    )

    if len(rows) < 2:
        return {
            "purity": purity,
            "status": "insufficient_data",
            "message": (
                f"Only {len(rows)} observation found "
                f"for {purity}. "
                "At least two observations are required."
            ),
        }

    latest = rows[0]
    previous = rows[1]

    # Make sure the observations represent
    # different source dates.
    if (
        latest["observation_date"]
        == previous["observation_date"]
    ):
        return {
            "purity": purity,
            "status": "same_observation_date",
            "message": (
                f"The two latest {purity} records "
                f"both belong to "
                f"{latest['observation_date']}. "
                "A different observation date is "
                "required for comparison."
            ),
        }

    current_price = latest["price_per_gram"]
    previous_price = previous["price_per_gram"]

    price_change = (
        current_price - previous_price
    )

    percentage_change = calculate_percentage_change(
        previous_price,
        current_price,
    )

    if price_change > 0:
        direction = "increase"

    elif price_change < 0:
        direction = "decrease"

    else:
        direction = "unchanged"

    return {
        "purity": purity,
        "status": "success",

        "current_price": current_price,
        "previous_price": previous_price,

        "price_change": price_change,
        "percentage_change": percentage_change,

        "direction": direction,

        "current_observation_date":
            latest["observation_date"],

        "previous_observation_date":
            previous["observation_date"],

        "current_recorded_at":
            latest["recorded_at"],

        "previous_recorded_at":
            previous["recorded_at"],

        "source": latest["source"],
    }


def display_comparison(comparison):
    """
    Display the comparison.
    """

    print()
    print("=" * 70)
    print(
        f"GOLDWATCH - "
        f"{comparison['purity']} PRICE COMPARISON"
    )
    print("=" * 70)

    if comparison["status"] != "success":

        print(comparison["message"])

        print("=" * 70)

        return

    print(
        f"Previous observation : "
        f"{comparison['previous_observation_date']}"
    )

    print(
        f"Previous price       : "
        f"₹{comparison['previous_price']:,.2f}/gram"
    )

    print()

    print(
        f"Current observation  : "
        f"{comparison['current_observation_date']}"
    )

    print(
        f"Current price        : "
        f"₹{comparison['current_price']:,.2f}/gram"
    )

    print()

    print(
        f"Change               : "
        f"₹{comparison['price_change']:+,.2f}/gram"
    )

    print(
        f"Change %             : "
        f"{comparison['percentage_change']:+.2f}%"
    )

    print(
        f"Direction            : "
        f"{comparison['direction'].upper()}"
    )

    print(
        f"Source               : "
        f"{comparison['source']}"
    )

    print("=" * 70)


def main():
    """
    Compare both 24K and 22K.
    """

    print()
    print("GoldWatch Date-Aware Comparison")

    comparison_24k = get_comparison("24K")
    comparison_22k = get_comparison("22K")

    display_comparison(comparison_24k)
    display_comparison(comparison_22k)


if __name__ == "__main__":
    main()