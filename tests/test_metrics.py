import pandas as pd

from src.metrics import (
    build_user_funnel,
    build_user_table,
    conversion_rate,
)
from src.processing import prepare_events


BASE = pd.Timestamp("2024-01-01 00:00:00")


def make_events(rows):
    data = []
    for visitorid, hours, event in rows:
        event_time = BASE + pd.Timedelta(hours=hours)
        data.append(
            {
                "timestamp": int(event_time.timestamp() * 1000),
                "visitorid": visitorid,
                "event": event,
                "itemid": visitorid * 10,
                "transactionid": visitorid if event == "transaction" else pd.NA,
            }
        )
    return prepare_events(pd.DataFrame(data))


def test_cart_before_view_is_not_in_funnel():
    events = make_events(
        [(1, 0, "addtocart"), (1, 1, "view"), (1, 2, "transaction")]
    )
    funnel = build_user_funnel(events)
    assert funnel.loc[0, "cart_time"] is pd.NaT


def test_purchase_without_cart_is_not_in_funnel():
    events = make_events([(1, 0, "view"), (1, 1, "transaction")])
    funnel = build_user_funnel(events)
    assert funnel.loc[0, "transaction_time"] is pd.NaT


def test_conversion_rate():
    assert conversion_rate(2, 8) == 0.25
    assert conversion_rate(2, 0) == 0


def test_weekend_and_weekday_use_first_view():
    rows = [
        (1, 24 * 4 + 23, "view"),
        (1, 24 * 5 + 1, "addtocart"),
        (2, 24 * 5 + 10, "view"),
    ]
    users = build_user_table(build_user_funnel(make_events(rows)))
    flags = users.set_index("visitorid")["is_weekend"].to_dict()
    assert flags == {1: False, 2: True}


def test_four_dayparts_are_assigned():
    rows = [
        (1, 5, "view"),
        (2, 6, "view"),
        (3, 12, "view"),
        (4, 18, "view"),
    ]
    users = build_user_table(build_user_funnel(make_events(rows)))
    assert users["daypart"].astype(str).tolist() == [
        "Ночь",
        "Утро",
        "День",
        "Вечер",
    ]
