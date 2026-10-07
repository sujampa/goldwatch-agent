"""
GoldWatch Agent - Trend Analysis Engine

Responsibilities:
- Analyze historical 22K and 24K prices.
- Calculate averages.
- Calculate price changes.
- Calculate percentage changes.
- Estimate basic volatility.
- Identify recent direction.

This module does NOT predict tomorrow's price.
Forecasting will be handled separately.
"""

import statistics

from database import get_recent_prices


MINIMUM_OBSERVATIONS = 2


def calculate_percentage_change(old_price, new_price):
    """
    Calculate percentage change.
    """

    if old_price == 0:
        return None

    return ((new_price - old_price) / old_price) * 100


def calculate_trend(prices):
    """
    Determine the general direction of a sequence of prices.
    """

    if len(prices) < 2:
        return "insufficient_data"

    first_price = prices[-1]
    latest_price = prices[0]

    if latest_price > first_price:
        return "increasing"

    if latest_price < first_price:
        return "decreasing"

    return "sideways"


def analyze_purity(purity, limit=30):
    """
    Analyze historical prices for one purity.
    """

    rows = get_recent_prices(
        purity=purity,
        limit=limit,
    )

    if len(rows) < MINIMUM_OBSERVATIONS:
        return {
            "purity": purity,
            "status": "insufficient_data",
            "observation_count": len(rows),
            "message": (
                f"{purity} requires at least "
                f"{MINIMUM_OBSERVATIONS} observations "
                "for trend analysis."
            ),
        }

    prices = [
        float(row["price_per_gram"])
        for row in rows
    ]

    latest_price = prices[0]
    oldest_price = prices[-1]

    average_price = statistics.mean(prices)

    minimum_price = min(prices)
    maximum_price = max(prices)

    percentage_change = calculate_percentage_change(
        oldest_price,
        latest_price,
    )

    trend = calculate_trend(prices)

    # Standard deviation is only useful with
    # at least two observations.
    volatility = statistics.stdev(prices)

    return {
        "purity": purity,
        "status": "success",
        "observation_count": len(prices),
        "latest_price": latest_price,
        "oldest_price": oldest_price,
        "average_price": average_price,
        "minimum_price": minimum_price,
        "maximum_price": maximum_price,
        "percentage_change": percentage_change,
        "volatility": volatility,
        "trend": trend,
        "latest_timestamp": rows[0]["recorded_at"],
        "oldest_timestamp": rows[-1]["recorded_at"],
        "source": rows[0]["source"],
    }


def display_analysis(result):
    """
    Display trend analysis.
    """

    print()
    print("=" * 70)
    print(
        f"GOLDWATCH - {result['purity']} TREND ANALYSIS"
    )
    print("=" * 70)

    if result["status"] != "success":
        print(result["message"])
        print("=" * 70)
        return

    print(
        f"Observations : "
        f"{result['observation_count']}"
    )

    print(
        f"Latest price : "
        f"₹{result['latest_price']:,.2f}/gram"
    )

    print(
        f"Average      : "
        f"₹{result['average_price']:,.2f}/gram"
    )

    print(
        f"Minimum      : "
        f"₹{result['minimum_price']:,.2f}/gram"
    )

    print(
        f"Maximum      : "
        f"₹{result['maximum_price']:,.2f}/gram"
    )

    print(
        f"Change       : "
        f"{result['percentage_change']:+.2f}%"
    )

    print(
        f"Volatility   : "
        f"₹{result['volatility']:,.2f}/gram"
    )

    print(
        f"Trend        : "
        f"{result['trend'].upper()}"
    )

    print(
        f"Source       : "
        f"{result['source']}"
    )

    print("=" * 70)


def main():
    """
    Analyze both 24K and 22K gold.
    """

    print()
    print("GoldWatch Trend Analysis")

    result_24k = analyze_purity("24K")
    result_22k = analyze_purity("22K")

    display_analysis(result_24k)
    display_analysis(result_22k)


if __name__ == "__main__":
    main()