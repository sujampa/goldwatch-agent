"""
GoldWatch Agent - Database Integration Test

Pipeline:
1. Fetch gold prices.
2. Validate the data.
3. Save only validated data.
4. Display database history.

Safety:
- Invalid data is never saved.
- Stale data is never saved.
"""

from tools.gold_price import get_gold_prices
from data_quality import validate_gold_result
from database import save_gold_result, print_recent_prices


def main():
    print()
    print("=" * 70)
    print("GOLDWATCH - SAFE DATABASE PIPELINE")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1: FETCH
    # ---------------------------------------------------------

    print()
    print("STEP 1 - Fetching gold prices...")

    try:
        gold_result = get_gold_prices()

        print("Price retrieved successfully.")

        print(
            f"24K: ₹{gold_result['24K']['price_per_gram']:,.2f}/gram"
        )

        print(
            f"22K: ₹{gold_result['22K']['price_per_gram']:,.2f}/gram"
        )

    except Exception as error:
        print()
        print("❌ PRICE FETCH FAILED")
        print(error)
        return

    # ---------------------------------------------------------
    # STEP 2: VALIDATE
    # ---------------------------------------------------------

    print()
    print("STEP 2 - Running data quality checks...")

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
    # STEP 3: SAFETY GATE
    # ---------------------------------------------------------

    print()

    if not validation_result["valid"]:
        print("❌ DATA REJECTED")
        print()
        print("The gold price was NOT saved to the database.")

        print()
        print("Reason(s):")

        for error in validation_result["errors"]:
            print(f"- {error}")

        print()
        print("=" * 70)

        return

    print("✅ DATA ACCEPTED")
    print("All validation checks passed.")

    # ---------------------------------------------------------
    # STEP 4: SAVE
    # ---------------------------------------------------------

    print()
    print("STEP 3 - Saving validated prices...")

    save_result = save_gold_result(
        gold_result
    )

    print()
    print("Database result:")
    print(
        f"24K saved: {save_result['24K']}"
    )
    print(
        f"22K saved: {save_result['22K']}"
    )

    # ---------------------------------------------------------
    # STEP 5: DISPLAY HISTORY
    # ---------------------------------------------------------

    print()
    print("STEP 4 - Database history")

    print_recent_prices()

    print()
    print("=" * 70)
    print("GOLDWATCH SAFE PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()