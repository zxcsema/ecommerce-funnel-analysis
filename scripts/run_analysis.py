import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.metrics import (
    build_user_funnel,
    build_user_table,
    calculate_daily_metrics,
    cart_to_purchase_times,
    daypart_chi_square,
    group_conversion,
    summarize_funnel,
    weekday_weekend_chi_square,
)
from src.processing import (
    EVENT_ORDER,
    RAW_EVENTS_PATH,
    load_events,
    prepare_events,
    save_bar_chart,
    save_line_chart,
    save_time_to_purchase_chart,
)


def main():
    reports_dir = PROJECT_ROOT / "reports"
    tables_dir = reports_dir / "tables"
    figures_dir = reports_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    raw_events = load_events(RAW_EVENTS_PATH)
    rows_before = len(raw_events)
    duplicates = raw_events.duplicated().sum()
    events = prepare_events(raw_events)
    event_counts = events["event"].value_counts().reindex(EVENT_ORDER)

    user_funnel = build_user_funnel(events)
    funnel = summarize_funnel(user_funnel)
    users = build_user_table(user_funnel)
    daily = calculate_daily_metrics(events, users)
    weekday_table = group_conversion(users, "is_weekend")
    weekday_table["period"] = weekday_table["is_weekend"].map(
        {False: "Будни", True: "Выходные"}
    )
    daypart_table = group_conversion(users, "daypart")
    purchases, purchase_time = cart_to_purchase_times(user_funnel)
    weekday_test = weekday_weekend_chi_square(users)
    daypart_test = daypart_chi_square(users)

    funnel_table = pd.DataFrame(
        {
            "stage": ["Просмотр", "Корзина", "Покупка"],
            "users": [
                funnel["view_users"],
                funnel["cart_users"],
                funnel["transaction_users"],
            ],
            "conversion_from_view": [
                1.0,
                funnel["view_to_cart"],
                funnel["view_to_transaction"],
            ],
        }
    )
    funnel_table.to_csv(tables_dir / "funnel_summary.csv", index=False)
    weekday_table[["period", "users", "buyers", "conversion"]].to_csv(
        tables_dir / "weekday_weekend_comparison.csv", index=False
    )
    daypart_table.to_csv(tables_dir / "daypart_comparison.csv", index=False)
    daily.to_csv(tables_dir / "daily_metrics.csv", index=False)

    save_bar_chart(
        ["Просмотр", "Корзина", "Покупка"],
        event_counts.tolist(),
        figures_dir / "event_counts.png",
        "Количество событий каждого типа",
        "Количество событий",
    )
    save_bar_chart(
        funnel_table["stage"],
        funnel_table["users"],
        figures_dir / "funnel.png",
        "Пользовательская воронка",
        "Количество пользователей",
    )
    save_line_chart(
        daily["event_date"],
        daily["active_users"],
        figures_dir / "daily_active_users.png",
        "Активные пользователи по дням",
        "Количество пользователей",
    )
    save_line_chart(
        daily["event_date"],
        daily["events"],
        figures_dir / "daily_events.png",
        "Количество событий по дням",
        "Количество событий",
    )
    save_line_chart(
        daily["event_date"],
        daily["conversion"] * 100,
        figures_dir / "daily_conversion.png",
        "Конверсия по дню первого просмотра",
        "Конверсия, %",
    )
    save_bar_chart(
        weekday_table["period"],
        weekday_table["conversion"] * 100,
        figures_dir / "weekday_weekend_conversion.png",
        "Конверсия в будни и выходные",
        "Конверсия, %",
        "#72B7B2",
    )
    save_bar_chart(
        daypart_table["daypart"].astype(str),
        daypart_table["conversion"] * 100,
        figures_dir / "daypart_conversion.png",
        "Конверсия по времени первого просмотра",
        "Конверсия, %",
        "#72B7B2",
    )
    save_time_to_purchase_chart(
        purchases, figures_dir / "time_to_purchase.png"
    )

    results = {
        "data": {
            "rows_before_cleaning": int(rows_before),
            "duplicates_removed": int(duplicates),
            "rows_after_cleaning": int(len(events)),
            "unique_users": int(events["visitorid"].nunique()),
            "period_start": str(events["event_time"].min()),
            "period_end": str(events["event_time"].max()),
            "event_counts": {
                "view": int(event_counts["view"]),
                "addtocart": int(event_counts["addtocart"]),
                "transaction": int(event_counts["transaction"]),
            },
        },
        "funnel": funnel,
        "purchase_time": purchase_time,
        "weekday_weekend": weekday_test,
        "daypart": daypart_test,
    }
    with (reports_dir / "results.json").open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print(f"Строк до очистки: {rows_before:,}")
    print(f"Удалено полных дубликатов: {duplicates:,}")
    print(f"Строк после очистки: {len(events):,}")
    print(f"Уникальных пользователей: {events['visitorid'].nunique():,}")
    print(f"Период данных: {events['event_time'].min()} — {events['event_time'].max()}")
    print("Количество событий:")
    print(event_counts.to_string())
    print(f"Конверсия из просмотра в корзину: {funnel['view_to_cart']:.3%}")
    print(
        "Конверсия из корзины в покупку: "
        f"{funnel['cart_to_transaction']:.3%}"
    )
    print(
        "Конверсия из просмотра в покупку: "
        f"{funnel['view_to_transaction']:.3%}"
    )
    print(
        "Минимальная ожидаемая частота, будни и выходные: "
        f"{weekday_test['minimum_expected']:.1f}"
    )
    print(f"p-value: {weekday_test['p_value']:.2e}")
    print(
        "Минимальная ожидаемая частота, части суток: "
        f"{daypart_test['minimum_expected']:.1f}"
    )
    print(f"p-value: {daypart_test['p_value']:.2e}")
    print("Результаты сохранены в reports/")


if __name__ == "__main__":
    main()
