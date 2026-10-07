"""
GoldWatch Agent - Gold Price Tool

Responsibilities:
- Retrieve explicit 24K and 22K gold prices.
- Validate the API response structure.
- Handle temporary network failures safely.

Source:
GoldPrice.dev
"""

import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import requests


KARAT_API_URL = (
    "https://api.goldprice.dev/v1/carat?currency=INR"
)

SOURCE_NAME = "GoldPrice.dev"

REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def _to_decimal(value, field_name):
    """
    Convert an API value to Decimal safely.
    """

    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(
            f"Invalid value for {field_name}: {value}"
        ) from error

    if result <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return result


def _request_gold_data():
    """
    Request gold data with retries.

    Returns:
        Parsed JSON response.
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = requests.get(
                KARAT_API_URL,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

            return response.json()

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.JSONDecodeError,
        ) as error:

            last_error = error

            if attempt < MAX_RETRIES:
                print(
                    f"API request failed "
                    f"(attempt {attempt}/{MAX_RETRIES}). "
                    f"Retrying..."
                )

                time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        f"Unable to retrieve gold prices after "
        f"{MAX_RETRIES} attempts: {last_error}"
    )


def get_gold_prices():
    """
    Retrieve and validate 24K and 22K gold prices.

    Returns:
        Dictionary containing validated gold prices.
    """

    try:
        data = _request_gold_data()

        required_fields = [
            "currency",
            "timestamp",
            "price_gram_24k",
            "price_gram_22k",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:
            raise ValueError(
                "Missing required API fields: "
                + ", ".join(missing_fields)
            )

        if data["currency"] != "INR":
            raise ValueError(
                f"Unexpected currency: {data['currency']}"
            )

        price_24k = _to_decimal(
            data["price_gram_24k"],
            "price_gram_24k",
        )

        price_22k = _to_decimal(
            data["price_gram_22k"],
            "price_gram_22k",
        )

        if price_22k >= price_24k:
            raise ValueError(
                "22K price cannot be greater than or equal "
                "to 24K price."
            )

        retrieved_at = datetime.now(
            timezone.utc
        ).isoformat()

        return {
            "source": SOURCE_NAME,
            "source_url": KARAT_API_URL,
            "currency": data["currency"],
            "unit": "gram",
            "retrieved_at": retrieved_at,
            "api_timestamp": data["timestamp"],
            "24K": {
                "price_per_gram": price_24k,
            },
            "22K": {
                "price_per_gram": price_22k,
            },
        }

    except Exception as error:
        raise RuntimeError(
            f"Unable to retrieve gold prices: {error}"
        ) from error


def display_gold_prices(gold_result):
    """
    Display retrieved gold prices.
    """

    print()
    print("=" * 70)
    print("GOLDWATCH - CURRENT GOLD PRICE")
    print("=" * 70)

    print(
        f"24K Gold : "
        f"₹{gold_result['24K']['price_per_gram']:,.2f} / gram"
    )

    print(
        f"22K Gold : "
        f"₹{gold_result['22K']['price_per_gram']:,.2f} / gram"
    )

    print()
    print(f"Source      : {gold_result['source']}")
    print(f"API time    : {gold_result['api_timestamp']}")
    print(f"Retrieved   : {gold_result['retrieved_at']}")

    print()
    print(
        "Important: These are purity-adjusted metal values, "
        "not final jewellery prices."
    )

    print("=" * 70)


if __name__ == "__main__":
    try:
        result = get_gold_prices()
        display_gold_prices(result)

    except Exception as error:
        print()
        print("❌ Gold price retrieval failed.")
        print(error)