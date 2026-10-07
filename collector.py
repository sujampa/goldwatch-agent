"""
GoldWatch Agent - Historical Data Collector

Responsibilities:
- Check whether today's observation already exists.
- Fetch current gold prices.
- Validate the API response.
- Save validated prices to SQLite.
- Prevent duplicate daily collection.

This module does not:
- Send emails.
- Read Gmail.
- Generate forecasts.
- Modify the RAG project.
"""

from tools.gold_price import get_gold_prices
from data_quality import validate_gold_result
from database import save_gold_result, has_observation_today


def collect_gold_price():
    """
    Execute the safe daily collection pipeline.
    """

    print()
    print("=" * 70)
    print("GOLDWATCH - DAILY DATA COLLECTION")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1: DAILY COLLECTION GUARD
    # ---------------------------------------------------------

    print()
    print("STEP 1 - Checking today's collection status...")

    already_collected_24k = has_observation_today("24K")
    already_collected_22k = has_observation_today("22K")

    if already_collected_24k and already_collected_22k:
        print()
        print("✅ Today's gold prices are already stored.")
        print("No new collection is required.")
        print("Stopping safely to avoid duplicate observations.")

        print("=" * 70)

        return {
            "success": True,
            "stage": "already_collected",
            "inserted": {
                "24K": False,
                "22K": False,
            },
        }

    # ---------------------------------------------------------
    # STEP 2: FETCH
    # ---------------------------------------------------------

    print()
    print("STEP 2 - Fetching gold prices...")

    try:
        gold_result = get_gold_prices()

    except Exception as error:
        print()
        print("❌ PRICE FETCH FAILED")
        print(f"Reason: {error}")

        print("=" * 70)

        return {
            "success": False,
            "stage": "fetch",
            "error": str(error),
        }

    print()
    print("Price retrieved successfully.")

    print(
        f"24K: ₹{gold_result['24K']['price_per_gram']:,.2f}/gram"
    )

    print(
        f"22K: ₹{gold_result['22K']['price_per_gram']:,.2f}/gram"
    )

    # ---------------------------------------------------------
    # STEP 3: VALIDATE
    # ---------------------------------------------------------

    print()
    print("STEP 3 - Validating data...")

    validation_result = validate_gold_result(
        gold_result
    )

    for check in validation_result["checks"]:
        status = "PASS" if check["passed"] else "FAIL"

        print(
            f"[{status}] "
            f"{check['check']}: "
            f"{check['message']}"
        )

    # ---------------------------------------------------------
    # STEP 4: SAFETY GATE
    # ---------------------------------------------------------

    if not validation_result["valid"]:

        print()
        print("❌ DATA REJECTED")
        print("Price will NOT be stored.")

        print()
        print("Reason(s):")

        for error in validation_result["errors"]:
            print(f"- {error}")

        print("=" * 70)

        return {
            "success": False,
            "stage": "validation",
            "error": validation_result["errors"],
        }

    print()
    print("✅ DATA ACCEPTED")

    # ---------------------------------------------------------
    # STEP 5: SAVE
    # ---------------------------------------------------------

    print()
    print("STEP 4 - Saving validated observation...")

    save_result = save_gold_result(
        gold_result
    )

    print()
    print("Database result:")

    print(
        f"24K inserted: {save_result['24K']}"
    )

    print(
        f"22K inserted: {save_result['22K']}"
    )

    # ---------------------------------------------------------
    # STEP 6: FINAL STATUS
    # ---------------------------------------------------------

    inserted_any = (
        save_result["24K"]
        or save_result["22K"]
    )

    print()

    if inserted_any:
        print("✅ New historical observation stored.")
    else:
        print(
            "ℹ️ Observation already exists. "
            "No duplicate created."
        )

    print("=" * 70)

    return {
        "success": True,
        "stage": "complete",
        "inserted": save_result,
        "gold_result": gold_result,
    }


def main():
    """
    Run the daily collector.
    """

    collect_gold_price()


if __name__ == "__main__":
    main()