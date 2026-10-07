"""
GoldWatch Agent - Data Quality & Freshness Guardrail

Responsibilities:
- Validate gold-price API results.
- Check required fields.
- Check 22K/24K relationships.
- Check timestamp validity.
- Detect stale data.

This module does not:
- Send emails.
- Read Gmail.
- Generate forecasts.
"""

from datetime import datetime, timezone


# Maximum allowed age of API data.
# This can be changed later based on the source's update frequency.
MAX_DATA_AGE_HOURS = 24


def parse_timestamp(timestamp):
    """
    Convert an ISO timestamp into a timezone-aware datetime.
    """

    if not timestamp:
        raise ValueError("Timestamp is missing.")

    try:
        parsed = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
    except ValueError as error:
        raise ValueError(
            f"Invalid timestamp format: {timestamp}"
        ) from error

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def check_required_fields(gold_result):
    """
    Check whether all required fields are present.
    """

    required_fields = [
        "source",
        "source_url",
        "currency",
        "unit",
        "retrieved_at",
        "api_timestamp",
        "24K",
        "22K",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in gold_result
    ]

    if missing_fields:
        return False, (
            "Missing required fields: "
            + ", ".join(missing_fields)
        )

    return True, "Required fields present."


def check_currency_and_unit(gold_result):
    """
    Ensure the API returned INR per gram.
    """

    if gold_result["currency"] != "INR":
        return False, (
            f"Unexpected currency: "
            f"{gold_result['currency']}"
        )

    if gold_result["unit"] != "gram":
        return False, (
            f"Unexpected unit: "
            f"{gold_result['unit']}"
        )

    return True, "Currency and unit are valid."


def check_prices(gold_result):
    """
    Validate 22K and 24K prices.
    """

    try:
        price_24k = float(
            gold_result["24K"]["price_per_gram"]
        )

        price_22k = float(
            gold_result["22K"]["price_per_gram"]
        )
    except (KeyError, TypeError, ValueError):
        return False, "Gold prices are invalid."

    if price_24k <= 0:
        return False, "24K price must be greater than zero."

    if price_22k <= 0:
        return False, "22K price must be greater than zero."

    if price_22k >= price_24k:
        return False, (
            "22K price must be lower than 24K price."
        )

    return True, "Gold prices are valid."


def check_timestamp_freshness(gold_result):
    """
    Check whether the API timestamp is recent enough.
    """

    try:
        api_time = parse_timestamp(
            gold_result["api_timestamp"]
        )
    except (KeyError, ValueError) as error:
        return False, str(error)

    now = datetime.now(timezone.utc)

    age = now - api_time

    # Future timestamps are suspicious.
    if age.total_seconds() < 0:
        return False, (
            "API timestamp is in the future."
        )

    age_hours = age.total_seconds() / 3600

    if age_hours > MAX_DATA_AGE_HOURS:
        return False, (
            f"API data is stale. "
            f"Age: {age_hours:.2f} hours. "
            f"Maximum allowed: "
            f"{MAX_DATA_AGE_HOURS} hours."
        )

    return True, (
        f"API data is fresh. "
        f"Age: {age_hours:.2f} hours."
    )


def validate_gold_result(gold_result):
    """
    Run all GoldWatch data-quality checks.

    Returns:

    {
        "valid": True/False,
        "checks": [...],
        "errors": [...]
    }
    """

    checks = []
    errors = []

    validations = [
        (
            "Required fields",
            check_required_fields(gold_result),
        ),
    ]

    # Stop early if the structure itself is invalid.
    for name, result in validations:
        passed, message = result

        checks.append({
            "check": name,
            "passed": passed,
            "message": message,
        })

        if not passed:
            errors.append(message)

    if errors:
        return {
            "valid": False,
            "checks": checks,
            "errors": errors,
        }

    additional_validations = [
        (
            "Currency and unit",
            check_currency_and_unit(gold_result),
        ),
        (
            "Gold prices",
            check_prices(gold_result),
        ),
        (
            "Timestamp freshness",
            check_timestamp_freshness(gold_result),
        ),
    ]

    for name, result in additional_validations:
        passed, message = result

        checks.append({
            "check": name,
            "passed": passed,
            "message": message,
        })

        if not passed:
            errors.append(message)

    return {
        "valid": len(errors) == 0,
        "checks": checks,
        "errors": errors,
    }


def display_validation(validation_result):
    """
    Display validation results.
    """

    print()
    print("=" * 70)
    print("GOLDWATCH - DATA QUALITY CHECK")
    print("=" * 70)

    for check in validation_result["checks"]:
        status = "PASS" if check["passed"] else "FAIL"

        print(
            f"[{status}] "
            f"{check['check']}: "
            f"{check['message']}"
        )

    print()

    if validation_result["valid"]:
        print("FINAL RESULT: DATA ACCEPTED")
    else:
        print("FINAL RESULT: DATA REJECTED")

        print()
        print("Errors:")

        for error in validation_result["errors"]:
            print(f"- {error}")

    print("=" * 70)


if __name__ == "__main__":
    from tools.gold_price import get_gold_prices

    print()
    print("Fetching gold price for validation...")

    try:
        gold_result = get_gold_prices()

        validation_result = validate_gold_result(
            gold_result
        )

        display_validation(validation_result)

    except Exception as error:
        print()
        print("=" * 70)
        print("GOLDWATCH - VALIDATION ERROR")
        print("=" * 70)
        print(error)
        print("=" * 70)