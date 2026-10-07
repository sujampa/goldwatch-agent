from database import get_connection
from forecast import generate_forecast


FORECAST_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS forecast_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date TEXT NOT NULL,
    target_date TEXT NOT NULL,
    purity TEXT NOT NULL,
    predicted_price REAL NOT NULL,
    predicted_low REAL,
    predicted_high REAL,
    expected_change_percent REAL,
    direction TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (forecast_date, target_date, purity)
)
"""


def initialize_forecast_history_table():
    """
    Create the forecast history table if it does not exist.
    """

    conn = get_connection()

    try:
        conn.execute(FORECAST_HISTORY_TABLE)
        conn.commit()
    finally:
        conn.close()


def save_forecast(
    forecast_date: str,
    target_date: str,
    purity: str,
    predicted_price: float,
    predicted_low: float | None,
    predicted_high: float | None,
    expected_change_percent: float | None,
    direction: str | None,
):
    """
    Save one forecast observation.

    Duplicate forecasts for the same forecast date,
    target date and purity are ignored.
    """

    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO forecast_history (
                forecast_date,
                target_date,
                purity,
                predicted_price,
                predicted_low,
                predicted_high,
                expected_change_percent,
                direction,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                forecast_date,
                target_date,
                purity,
                predicted_price,
                predicted_low,
                predicted_high,
                expected_change_percent,
                direction,
            ),
        )

        conn.commit()

        return cursor.rowcount == 1

    finally:
        conn.close()


def get_forecast(
    purity: str,
    target_date: str,
):
    """
    Retrieve a forecast for a specific purity and target date.
    """

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT
                id,
                forecast_date,
                target_date,
                purity,
                predicted_price,
                predicted_low,
                predicted_high,
                expected_change_percent,
                direction,
                created_at
            FROM forecast_history
            WHERE purity = ?
              AND target_date = ?
            LIMIT 1
            """,
            (purity, target_date),
        ).fetchone()

        return row

    finally:
        conn.close()


def get_recent_forecasts(
    purity: str | None = None,
    limit: int = 10,
):
    """
    Retrieve recent forecast history.
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
                    expected_change_percent,
                    direction,
                    created_at
                FROM forecast_history
                WHERE purity = ?
                ORDER BY forecast_date DESC
                LIMIT ?
                """,
                (purity, limit),
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
                    expected_change_percent,
                    direction,
                    created_at
                FROM forecast_history
                ORDER BY forecast_date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return rows

    finally:
        conn.close()


def print_recent_forecasts():
    """
    Display recent forecasts.
    """

    print("\n" + "=" * 70)
    print("GOLDWATCH - FORECAST HISTORY")
    print("=" * 70)

    rows = get_recent_forecasts(limit=10)

    if not rows:
        print("\nNo forecasts stored yet.")
        print("=" * 70)
        return

    for row in rows:

        (
            forecast_date,
            target_date,
            purity,
            predicted_price,
            predicted_low,
            predicted_high,
            expected_change_percent,
            direction,
            created_at,
        ) = row

        print(f"\n{purity}")
        print(f"Forecast date : {forecast_date}")
        print(f"Target date   : {target_date}")
        print(f"Predicted     : ₹{predicted_price:,.2f}/g")

        if predicted_low is not None:
            print(f"Expected low  : ₹{predicted_low:,.2f}/g")

        if predicted_high is not None:
            print(f"Expected high : ₹{predicted_high:,.2f}/g")

        if expected_change_percent is not None:
            print(
                f"Expected move : "
                f"{expected_change_percent:+.2f}%"
            )

        if direction:
            print(f"Direction     : {direction}")

    print("\n" + "=" * 70)


if __name__ == "__main__":

    print("\nInitializing forecast history...")

    initialize_forecast_history_table()

    print("✅ Forecast history table is ready.")

    print_recent_forecasts()