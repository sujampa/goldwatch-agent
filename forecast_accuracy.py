from pathlib import Path
import sqlite3
from datetime import datetime, timezone

from database import get_connection
from forecast import generate_forecast


ACCURACY_TABLE = """
CREATE TABLE IF NOT EXISTS forecast_accuracy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date TEXT NOT NULL,
    target_date TEXT NOT NULL,
    purity TEXT NOT NULL,
    predicted_price REAL NOT NULL,
    predicted_low REAL,
    predicted_high REAL,
    actual_price REAL NOT NULL,
    absolute_error REAL NOT NULL,
    percentage_error REAL NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (forecast_date, target_date, purity)
)
"""


def initialize_accuracy_table():
    """
    Create the forecast accuracy table if it does not exist.
    """

    conn = get_connection()

    try:
        conn.execute(ACCURACY_TABLE)
        conn.commit()
    finally:
        conn.close()


def calculate_error(predicted_price: float, actual_price: float) -> tuple[float, float]:
    """
    Calculate absolute and percentage prediction error.
    """

    absolute_error = abs(actual_price - predicted_price)

    if actual_price == 0:
        percentage_error = 0.0
    else:
        percentage_error = (
            absolute_error / actual_price
        ) * 100

    return absolute_error, percentage_error


def get_accuracy_records(purity: str | None = None):
    """
    Return stored forecast accuracy records.
    """

    conn = get_connection()

    try:
        if purity:
            rows = conn.execute(
                """
                SELECT
                    forecast_date,
                    target_date,
                    purity,
                    predicted_price,
                    predicted_low,
                    predicted_high,
                    actual_price,
                    absolute_error,
                    percentage_error,
                    created_at
                FROM forecast_accuracy
                WHERE purity = ?
                ORDER BY target_date DESC
                """,
                (purity,),
            ).fetchall()

        else:
            rows = conn.execute(
                """
                SELECT
                    forecast_date,
                    target_date,
                    purity,
                    predicted_price,
                    predicted_low,
                    predicted_high,
                    actual_price,
                    absolute_error,
                    percentage_error,
                    created_at
                FROM forecast_accuracy
                ORDER BY target_date DESC
                """
            ).fetchall()

        return rows

    finally:
        conn.close()


def calculate_accuracy_summary(purity: str):
    """
    Calculate average prediction error for a purity.
    """

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS prediction_count,
                AVG(percentage_error) AS average_percentage_error,
                MIN(percentage_error) AS minimum_percentage_error,
                MAX(percentage_error) AS maximum_percentage_error
            FROM forecast_accuracy
            WHERE purity = ?
            """,
            (purity,),
        ).fetchone()

        return {
            "purity": purity,
            "prediction_count": row[0],
            "average_percentage_error": row[1],
            "minimum_percentage_error": row[2],
            "maximum_percentage_error": row[3],
        }

    finally:
        conn.close()


def print_accuracy_summary():
    """
    Display forecast accuracy statistics.
    """

    print("\n" + "=" * 70)
    print("GOLDWATCH - FORECAST ACCURACY")
    print("=" * 70)

    for purity in ["24K", "22K"]:

        summary = calculate_accuracy_summary(purity)

        print(f"\n{purity}")

        print(
            f"Predictions evaluated: "
            f"{summary['prediction_count']}"
        )

        if summary["prediction_count"] == 0:
            print("No predictions have been evaluated yet.")
            continue

        print(
            f"Average error: "
            f"{summary['average_percentage_error']:.2f}%"
        )

        print(
            f"Minimum error: "
            f"{summary['minimum_percentage_error']:.2f}%"
        )

        print(
            f"Maximum error: "
            f"{summary['maximum_percentage_error']:.2f}%"
        )

    print("=" * 70)


if __name__ == "__main__":

    print("\nInitializing forecast accuracy tracking...")

    initialize_accuracy_table()

    print("✅ Forecast accuracy table is ready.")

    print_accuracy_summary()