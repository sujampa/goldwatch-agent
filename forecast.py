"""
GoldWatch Agent - Forecast Engine

Responsibilities:
- Generate a conservative statistical forecast.
- Use historical gold prices from SQLite.
- Calculate a forecast range.
- Calculate expected percentage movement.
- Refuse to forecast when historical data is insufficient.

Important:
- Llama is NOT used to generate numerical predictions.
- This is a baseline statistical model.
- Forecasts are estimates, not guarantees.
"""

import statistics

from database import get_recent_prices


# Minimum number of historical observations required.
MINIMUM_OBSERVATIONS = 5

# Number of observations used by the model.
HISTORY_WINDOW = 7

# Multiplier used to create the initial forecast range.
VOLATILITY_MULTIPLIER = 1.0


def calculate_percentage_change(old_price, new_price):
    """
    Calculate percentage change.
    """

    if old_price == 0:
        return None

    return ((new_price - old_price) / old_price) * 100


def classify_direction(change_percentage):
    """
    Classify expected movement.
    """

    if change_percentage > 0.10:
        return "increase"

    if change_percentage < -0.10:
        return "decrease"

    return "sideways"


def generate_forecast(purity):
    """
    Generate a statistical baseline forecast.

    The model uses:
    - Recent average price
    - Recent price volatility
    - Latest price
    """

    rows = get_recent_prices(
        purity=purity,
        limit=HISTORY_WINDOW,
    )

    if len(rows) < MINIMUM_OBSERVATIONS:
        return {
            "purity": purity,
            "status": "insufficient_data",
            "observation_count": len(rows),
            "required_observations": MINIMUM_OBSERVATIONS,
            "message": (
                f"Not enough historical data for {purity}. "
                f"At least {MINIMUM_OBSERVATIONS} "
                "observations are required."
            ),
        }

    prices = [
        float(row["price_per_gram"])
        for row in rows
    ]

    latest_price = prices[0]

    average_price = statistics.mean(prices)

    volatility = statistics.stdev(prices)

    # Recent directional movement.
    oldest_price = prices[-1]

    recent_change_percentage = calculate_percentage_change(
        oldest_price,
        latest_price,
    )

    # Simple baseline:
    # blend the latest price with the historical average.
    forecast_midpoint = (
        latest_price * 0.7
        + average_price * 0.3
    )

    range_size = (
        volatility * VOLATILITY_MULTIPLIER
    )

    forecast_low = max(
        0,
        forecast_midpoint - range_size,
    )

    forecast_high = (
        forecast_midpoint + range_size
    )

    expected_change_percentage = (
        calculate_percentage_change(
            latest_price,
            forecast_midpoint,
        )
    )

    lower_change_percentage = (
        calculate_percentage_change(
            latest_price,
            forecast_low,
        )
    )

    upper_change_percentage = (
        calculate_percentage_change(
            latest_price,
            forecast_high,
        )
    )

    direction = classify_direction(
        expected_change_percentage
    )

    return {
        "purity": purity,
        "status": "success",
        "observation_count": len(prices),
        "latest_price": latest_price,
        "average_price": average_price,
        "volatility": volatility,
        "forecast_low": forecast_low,
        "forecast_midpoint": forecast_midpoint,
        "forecast_high": forecast_high,
        "lower_change_percentage": lower_change_percentage,
        "expected_change_percentage": expected_change_percentage,
        "upper_change_percentage": upper_change_percentage,
        "direction": direction,
        "latest_timestamp": rows[0]["recorded_at"],
        "source": rows[0]["source"],
    }


def display_forecast(result):
    """
    Display forecast results.
    """

    print()
    print("=" * 70)
    print(
        f"GOLDWATCH - {result['purity']} FORECAST"
    )
    print("=" * 70)

    if result["status"] != "success":

        print(result["message"])

        print(
            f"Observations available: "
            f"{result['observation_count']}"
        )

        print(
            f"Observations required: "
            f"{result['required_observations']}"
        )

        print("=" * 70)

        return

    print(
        f"Observations    : "
        f"{result['observation_count']}"
    )

    print(
        f"Current price   : "
        f"₹{result['latest_price']:,.2f}/gram"
    )

    print(
        f"Forecast low    : "
        f"₹{result['forecast_low']:,.2f}/gram"
    )

    print(
        f"Forecast midpoint: "
        f"₹{result['forecast_midpoint']:,.2f}/gram"
    )

    print(
        f"Forecast high   : "
        f"₹{result['forecast_high']:,.2f}/gram"
    )

    print(
        f"Expected change : "
        f"{result['expected_change_percentage']:+.2f}%"
    )

    print(
        f"Expected range  : "
        f"{result['lower_change_percentage']:+.2f}% "
        f"to "
        f"{result['upper_change_percentage']:+.2f}%"
    )

    print(
        f"Direction       : "
        f"{result['direction'].upper()}"
    )

    print()
    print(
        "CAUTION: This is a statistical estimate, "
        "not a guaranteed prediction or financial advice."
    )

    print("=" * 70)


def main():
    """
    Generate forecasts for 24K and 22K gold.
    """

    print()
    print("GoldWatch Forecast Engine")

    forecast_24k = generate_forecast("24K")
    forecast_22k = generate_forecast("22K")

    display_forecast(forecast_24k)
    display_forecast(forecast_22k)


if __name__ == "__main__":
    main()