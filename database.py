"""
GoldWatch Agent - Historical Price Database

Responsibilities:
- Store validated 22K and 24K gold prices.
- Store the source observation date.
- Prevent duplicate observations.
- Retrieve historical prices.
- Distinguish source time from retrieval time.

Privacy:
- No Gmail data is stored.
- No email contents are stored.
- No passwords or API keys are stored.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "goldwatch.db"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gold_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            recorded_at TEXT NOT NULL,

            observation_date TEXT NOT NULL,

            source TEXT NOT NULL,

            source_url TEXT NOT NULL,

            currency TEXT NOT NULL,

            unit TEXT NOT NULL,

            purity TEXT NOT NULL,

            price_per_gram REAL NOT NULL,

            api_timestamp TEXT,

            created_at TEXT NOT NULL,

            UNIQUE (
                source,
                api_timestamp,
                purity
            )
        )
        """
    )

    connection.commit()
    connection.close()


def get_observation_date(api_timestamp):
    """
    Extract the UTC calendar date from the source timestamp.

    Example:
        2026-10-02T21:08:02Z
        -> 2026-10-02
    """

    if not api_timestamp:
        raise ValueError(
            "API timestamp is required."
        )

    parsed_timestamp = datetime.fromisoformat(
        api_timestamp.replace("Z", "+00:00")
    )

    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(
            tzinfo=timezone.utc
        )

    return parsed_timestamp.date().isoformat()


def save_gold_price(
    source,
    source_url,
    currency,
    unit,
    purity,
    price_per_gram,
    api_timestamp,
    recorded_at=None,
):
    """
    Save one validated gold-price observation.
    """

    if recorded_at is None:
        recorded_at = datetime.now(
            timezone.utc
        ).isoformat()

    observation_date = get_observation_date(
        api_timestamp
    )

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO gold_prices (
            recorded_at,
            observation_date,
            source,
            source_url,
            currency,
            unit,
            purity,
            price_per_gram,
            api_timestamp,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recorded_at,
            observation_date,
            source,
            source_url,
            currency,
            unit,
            purity,
            float(price_per_gram),
            api_timestamp,
            created_at,
        ),
    )

    connection.commit()

    inserted = cursor.rowcount == 1

    connection.close()

    return inserted


def save_gold_result(gold_result):
    """
    Save both 24K and 22K observations.
    """

    initialize_database()

    source = gold_result["source"]
    source_url = gold_result["source_url"]
    currency = gold_result["currency"]
    unit = gold_result["unit"]
    api_timestamp = gold_result["api_timestamp"]

    saved_24k = save_gold_price(
        source=source,
        source_url=source_url,
        currency=currency,
        unit=unit,
        purity="24K",
        price_per_gram=gold_result[
            "24K"
        ]["price_per_gram"],
        api_timestamp=api_timestamp,
    )

    saved_22k = save_gold_price(
        source=source,
        source_url=source_url,
        currency=currency,
        unit=unit,
        purity="22K",
        price_per_gram=gold_result[
            "22K"
        ]["price_per_gram"],
        api_timestamp=api_timestamp,
    )

    return {
        "24K": saved_24k,
        "22K": saved_22k,
    }


def get_recent_prices(
    purity=None,
    limit=10,
):
    """
    Retrieve recent historical observations.
    """

    connection = get_connection()
    cursor = connection.cursor()

    if purity:

        cursor.execute(
            """
            SELECT
                id,
                recorded_at,
                observation_date,
                source,
                source_url,
                currency,
                unit,
                purity,
                price_per_gram,
                api_timestamp,
                created_at
            FROM gold_prices
            WHERE purity = ?
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (purity, limit),
        )

    else:

        cursor.execute(
            """
            SELECT
                id,
                recorded_at,
                observation_date,
                source,
                source_url,
                currency,
                unit,
                purity,
                price_per_gram,
                api_timestamp,
                created_at
            FROM gold_prices
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_latest_price(purity):
    """
    Get the latest stored observation.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            recorded_at,
            observation_date,
            source,
            source_url,
            currency,
            unit,
            purity,
            price_per_gram,
            api_timestamp,
            created_at
        FROM gold_prices
        WHERE purity = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (purity,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def has_observation_today(
    purity=None,
):
    """
    Check whether an observation was recorded
    today according to the GoldWatch machine's UTC date.

    This checks recorded_at because this function
    controls daily collection frequency.
    """

    today = datetime.now(
        timezone.utc
    ).date().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    if purity:

        cursor.execute(
            """
            SELECT 1
            FROM gold_prices
            WHERE purity = ?
              AND substr(recorded_at, 1, 10) = ?
            LIMIT 1
            """,
            (purity, today),
        )

    else:

        cursor.execute(
            """
            SELECT 1
            FROM gold_prices
            WHERE substr(recorded_at, 1, 10) = ?
            LIMIT 1
            """,
            (today,),
        )

    row = cursor.fetchone()

    connection.close()

    return row is not None


def print_recent_prices(
    limit=10,
):
    """
    Display database history.
    """

    rows = get_recent_prices(
        limit=limit
    )

    print()
    print("=" * 90)
    print("GOLDWATCH - DATABASE HISTORY")
    print("=" * 90)

    if not rows:

        print(
            "No gold-price records found."
        )

        print("=" * 90)

        return

    for row in rows:

        print(
            f"{row['purity']:>3} | "
            f"₹{row['price_per_gram']:,.2f}/g | "
            f"Observation: "
            f"{row['observation_date']} | "
            f"Recorded: "
            f"{row['recorded_at']} | "
            f"{row['source']}"
        )

    print("=" * 90)


if __name__ == "__main__":

    initialize_database()

    print(
        "GoldWatch database initialized."
    )

    print(
        f"Database: {DATABASE_PATH}"
    )

    print_recent_prices()