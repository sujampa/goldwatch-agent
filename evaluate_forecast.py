from database import get_connection
from forecast_history import initialize_forecast_history_table
from forecast_accuracy import initialize_accuracy_table, calculate_error


def get_actual_price(purity: str, target_date: str):
    """
    Get the actual gold price for a specific observation date.
    """

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT
                price_per_gram
            FROM gold_prices
            WHERE purity = ?
              AND observation_date = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (purity, target_date),
        ).fetchone()

        if row is None:
            return None

        return float(row[0])

    finally:
        conn.close()


def get_forecast_for_date(purity: str, target_date: str):
    """
    Get the forecast that was made for a specific target date.
    """

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT
                forecast_date,
                target_date,
                purity,
                predicted_price,
                predicted_low,
                predicted_high
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


def already_evaluated(
    purity: str,
    target_date: str,
) -> bool:
    """
    Check whether a forecast has already been evaluated.
    """

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT id
            FROM forecast_accuracy
            WHERE purity = ?
              AND target_date = ?
            LIMIT 1
            """,
            (purity, target_date),
        ).fetchone()

        return row is not None

    finally:
        conn.close()


def evaluate_forecast(
    purity: str,
    target_date: str,
):
    """
    Compare a stored forecast against the actual
    observed price for the target date.
    """

    forecast = get_forecast_for_date(
        purity,
        target_date,
    )

    if forecast is None:
        return {
            "status": "NO_FORECAST",
            "purity": purity,
            "target_date": target_date,
        }

    if already_evaluated(
        purity,
        target_date,
    ):
        return {
            "status": "ALREADY_EVALUATED",
            "purity": purity,
            "target_date": target_date,
        }

    actual_price = get_actual_price(
        purity,
        target_date,
    )

    if actual_price is None:
        return {
            "status": "NO_ACTUAL",
            "purity": purity,
            "target_date": target_date,
        }

    (
        forecast_date,
        forecast_target_date,
        forecast_purity,
        predicted_price,
        predicted_low,
        predicted_high,
    ) = forecast

    predicted_price = float(predicted_price)

    absolute_error, percentage_error = calculate_error(
        predicted_price,
        actual_price,
    )

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO forecast_accuracy (
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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                forecast_date,
                target_date,
                purity,
                predicted_price,
                predicted_low,
                predicted_high,
                actual_price,
                absolute_error,
                percentage_error,
            ),
        )

        conn.commit()

    finally:
        conn.close()

    return {
        "status": "EVALUATED",
        "purity": purity,
        "target_date": target_date,
        "forecast_date": forecast_date,
        "predicted_price": predicted_price,
        "actual_price": actual_price,
        "absolute_error": absolute_error,
        "percentage_error": percentage_error,
    }


def print_result(result: dict):
    """
    Display forecast evaluation result.
    """

    print("\n" + "=" * 70)
    print("GOLDWATCH - FORECAST EVALUATION")
    print("=" * 70)

    status = result["status"]

    if status == "NO_FORECAST":

        print(
            f"\nNo forecast exists for "
            f"{result['purity']} on {result['target_date']}."
        )

    elif status == "NO_ACTUAL":

        print(
            f"\nForecast exists for "
            f"{result['purity']} on {result['target_date']}, "
            f"but the actual price has not been collected yet."
        )

    elif status == "ALREADY_EVALUATED":

        print(
            f"\nForecast for {result['purity']} "
            f"on {result['target_date']} "
            f"has already been evaluated."
        )

    elif status == "EVALUATED":

        print(f"\nPurity          : {result['purity']}")
        print(f"Forecast date   : {result['forecast_date']}")
        print(f"Target date     : {result['target_date']}")
        print(
            f"Predicted price : "
            f"₹{result['predicted_price']:,.2f}/g"
        )
        print(
            f"Actual price    : "
            f"₹{result['actual_price']:,.2f}/g"
        )
        print(
            f"Absolute error  : "
            f"₹{result['absolute_error']:,.2f}/g"
        )
        print(
            f"Percentage error: "
            f"{result['percentage_error']:.2f}%"
        )

    print("\n" + "=" * 70)


if __name__ == "__main__":

    initialize_forecast_history_table()
    initialize_accuracy_table()

    print(
        "\nChecking today's forecast evaluation..."
    )

    from datetime import datetime, timedelta, timezone

    today = datetime.now(
        timezone.utc
    ).date()

    target_date = today.isoformat()

    for purity in ["24K", "22K"]:

        result = evaluate_forecast(
            purity,
            target_date,
        )

        print_result(result)