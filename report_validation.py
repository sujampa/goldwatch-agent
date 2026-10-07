from pathlib import Path
from docx import Document


REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def validate_report(report_path: str | Path) -> dict:
    """
    Validate a generated GoldWatch DOCX report.

    Returns:
        {
            "valid": True/False,
            "checks": {...},
            "errors": [...]
        }
    """

    report_path = Path(report_path)

    checks = {}
    errors = []

    # ---------------------------------------------------------
    # CHECK 1: File exists
    # ---------------------------------------------------------

    if report_path.exists():
        checks["file_exists"] = True
    else:
        checks["file_exists"] = False
        errors.append("Report file does not exist.")

        return {
            "valid": False,
            "checks": checks,
            "errors": errors,
        }

    # ---------------------------------------------------------
    # CHECK 2: Correct file type
    # ---------------------------------------------------------

    if report_path.suffix.lower() == ".docx":
        checks["correct_file_type"] = True
    else:
        checks["correct_file_type"] = False
        errors.append("Report is not a DOCX file.")

    # ---------------------------------------------------------
    # CHECK 3: DOCX can be opened
    # ---------------------------------------------------------

    try:
        document = Document(report_path)
        checks["docx_readable"] = True

    except Exception as exc:

        checks["docx_readable"] = False
        errors.append(f"Could not read DOCX: {exc}")

        return {
            "valid": False,
            "checks": checks,
            "errors": errors,
        }

    # ---------------------------------------------------------
    # Extract paragraph text
    # ---------------------------------------------------------

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    full_text = "\n".join(paragraphs)

    # ---------------------------------------------------------
    # CHECK 4: Report contains meaningful text
    # ---------------------------------------------------------

    if len(full_text) > 50:
        checks["report_contains_text"] = True
    else:
        checks["report_contains_text"] = False
        errors.append("Report contains too little text.")

    # ---------------------------------------------------------
    # CHECK 5: GoldWatch title
    # ---------------------------------------------------------

    if "GOLDWATCH DAILY REPORT" in full_text:
        checks["title_present"] = True
    else:
        checks["title_present"] = False
        errors.append("GoldWatch report title is missing.")

    # ---------------------------------------------------------
    # CHECK 6: Gold price section
    # ---------------------------------------------------------

    if "Latest Available Gold Price" in full_text:
        checks["price_section_present"] = True
    else:
        checks["price_section_present"] = False
        errors.append("Latest Available Gold Price section is missing.")

    # ---------------------------------------------------------
    # CHECK 7: Price source
    # ---------------------------------------------------------

    if "GoldPrice.dev" in full_text:
        checks["source_present"] = True
    else:
        checks["source_present"] = False
        errors.append("Gold price source is missing.")

    # ---------------------------------------------------------
    # CHECK 8: Price timestamp
    # ---------------------------------------------------------

    if "Source timestamp:" in full_text:
        checks["source_timestamp_present"] = True
    else:
        checks["source_timestamp_present"] = False
        errors.append("Source timestamp is missing.")

    # ---------------------------------------------------------
    # CHECK 9: Retrieval timestamp
    # ---------------------------------------------------------

    if "Retrieved by GoldWatch:" in full_text:
        checks["retrieval_timestamp_present"] = True
    else:
        checks["retrieval_timestamp_present"] = False
        errors.append("GoldWatch retrieval timestamp is missing.")

    # ---------------------------------------------------------
    # CHECK 10: Comparison section
    # ---------------------------------------------------------

    if "Price Comparison" in full_text:
        checks["comparison_section_present"] = True
    else:
        checks["comparison_section_present"] = False
        errors.append("Price Comparison section is missing.")

    # ---------------------------------------------------------
    # CHECK 11: Forecast section
    # ---------------------------------------------------------

    if "Tomorrow's Outlook" in full_text:
        checks["forecast_section_present"] = True
    else:
        checks["forecast_section_present"] = False
        errors.append("Tomorrow's Outlook section is missing.")

    # ---------------------------------------------------------
    # CHECK 12: Forecast safety notice
    # ---------------------------------------------------------

    safety_phrases = [
        "not guaranteed",
        "statistical estimate",
    ]

    safety_found = any(
        phrase.lower() in full_text.lower()
        for phrase in safety_phrases
    )

    if safety_found:
        checks["safety_notice_present"] = True
    else:
        checks["safety_notice_present"] = False
        errors.append("Forecast safety notice is missing.")

    # ---------------------------------------------------------
    # CHECK 13: 24K section
    # ---------------------------------------------------------

    if "24K" in full_text:
        checks["24k_section_present"] = True
    else:
        checks["24k_section_present"] = False
        errors.append("24K price section is missing.")

    # ---------------------------------------------------------
    # CHECK 14: 22K section
    # ---------------------------------------------------------

    if "22K" in full_text:
        checks["22k_section_present"] = True
    else:
        checks["22k_section_present"] = False
        errors.append("22K price section is missing.")

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    valid = len(errors) == 0

    return {
        "valid": valid,
        "checks": checks,
        "errors": errors,
    }


def print_validation_result(result: dict):
    """
    Display validation results.
    """

    print("\n" + "=" * 70)
    print("GOLDWATCH - REPORT VALIDATION")
    print("=" * 70)

    print()

    for check_name, passed in result["checks"].items():

        readable_name = check_name.replace("_", " ").title()

        if passed:
            print(f"✅ {readable_name}")
        else:
            print(f"❌ {readable_name}")

    print()

    if result["valid"]:

        print("FINAL RESULT: ✅ REPORT VALID")

    else:

        print("FINAL RESULT: ❌ REPORT INVALID")

        print("\nProblems found:")

        for error in result["errors"]:
            print(f"  - {error}")

    print("=" * 70)


def find_latest_report() -> Path | None:
    """
    Find the newest GoldWatch DOCX report.
    """

    reports = list(
        REPORTS_DIR.glob("GoldWatch_Report_*.docx")
    )

    if not reports:
        return None

    return max(
        reports,
        key=lambda path: path.stat().st_mtime
    )


if __name__ == "__main__":

    latest_report = find_latest_report()

    if latest_report is None:

        print("❌ No GoldWatch report found.")
        raise SystemExit(1)

    print("\nChecking report:")
    print(latest_report)

    result = validate_report(latest_report)

    print_validation_result(result)

    if not result["valid"]:
        raise SystemExit(1)