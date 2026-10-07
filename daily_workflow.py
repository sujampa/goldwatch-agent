from datetime import datetime, timezone
from pathlib import Path

from collector import collect_gold_price
from reports.report_generator import generate_report
from report_validation import validate_report, print_validation_result
from evaluate_forecast import evaluate_forecast
from forecast_history import initialize_forecast_history_table
from forecast_accuracy import initialize_accuracy_table


REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def run_forecast_evaluation():
    """
    Evaluate forecasts for today's observation date.

    If no forecast exists yet, evaluation safely stops.
    """

    today = datetime.now(timezone.utc).date().isoformat()

    print("\n" + "=" * 70)
    print("STEP 1 - FORECAST EVALUATION")
    print("=" * 70)

    for purity in ["24K", "22K"]:

        result = evaluate_forecast(
            purity,
            today,
        )

        status = result["status"]

        if status == "EVALUATED":

            print(
                f"✅ {purity}: forecast evaluated "
                f"with {result['percentage_error']:.2f}% error."
            )

        elif status == "NO_FORECAST":

            print(
                f"ℹ️ {purity}: no forecast available "
                f"for {today}."
            )

        elif status == "NO_ACTUAL":

            print(
                f"ℹ️ {purity}: actual price not available "
                f"for {today}."
            )

        elif status == "ALREADY_EVALUATED":

            print(
                f"ℹ️ {purity}: forecast already evaluated."
            )


def run_collection():
    """
    Collect today's gold price if required.
    """

    print("\n" + "=" * 70)
    print("STEP 2 - GOLD PRICE COLLECTION")
    print("=" * 70)

    result = collect_gold_price()

    return result


def run_report_generation():
    """
    Generate the latest GoldWatch DOCX report.
    """

    print("\n" + "=" * 70)
    print("STEP 3 - REPORT GENERATION")
    print("=" * 70)

    report_path = generate_report()

    if report_path is None:
        print("❌ Report generation failed.")
        return None

    print(f"✅ Report generated:")
    print(report_path)

    return Path(report_path)


def run_report_validation(report_path):
    """
    Validate the generated report before allowing
    the workflow to continue.
    """

    print("\n" + "=" * 70)
    print("STEP 4 - REPORT VALIDATION")
    print("=" * 70)

    result = validate_report(report_path)

    print_validation_result(result)

    return result["valid"]


def main():

    print("\n" + "=" * 70)
    print("GOLDWATCH - DAILY WORKFLOW")
    print("=" * 70)

    print(
        "\nStarting GoldWatch daily workflow..."
    )

    # ---------------------------------------------------------
    # Initialize supporting tables
    # ---------------------------------------------------------

    initialize_forecast_history_table()
    initialize_accuracy_table()

    print(
        "\n✅ Forecast history initialized."
    )

    print(
        "✅ Forecast accuracy initialized."
    )

    # ---------------------------------------------------------
    # STEP 1
    # ---------------------------------------------------------

    run_forecast_evaluation()

    # ---------------------------------------------------------
    # STEP 2
    # ---------------------------------------------------------

    collection_result = run_collection()

    if collection_result is None:

        print(
            "\n❌ Collection returned no result."
        )

        print(
            "Stopping workflow safely."
        )

        return

    # ---------------------------------------------------------
    # STEP 3
    # ---------------------------------------------------------

    report_path = run_report_generation()

    if report_path is None:

        print(
            "\n❌ Cannot continue without a report."
        )

        return

    # ---------------------------------------------------------
    # STEP 4
    # ---------------------------------------------------------

    report_valid = run_report_validation(
        report_path
    )

    if not report_valid:

        print(
            "\n❌ REPORT VALIDATION FAILED."
        )

        print(
            "GoldWatch will NOT continue."
        )

        return

    # ---------------------------------------------------------
    # FINAL STATUS
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("GOLDWATCH DAILY WORKFLOW COMPLETE")
    print("=" * 70)

    print("\n✅ Collection checked")
    print("✅ Report generated")
    print("✅ Report validated")
    print("🔒 No email was sent")
    print("🔒 No external notification was sent")

    print("\nGoldWatch finished safely.")


if __name__ == "__main__":
    main()