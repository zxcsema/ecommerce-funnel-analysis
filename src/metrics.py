import pandas as pd
from scipy.stats import chi2_contingency


DAYPART_ORDER = ["Ночь", "Утро", "День", "Вечер"]


def conversion_rate(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def build_user_funnel(events):
    views = events[events["event"] == "view"]
    views = views.groupby("visitorid", as_index=False)["event_time"].min()
    views = views.rename(columns={"event_time": "view_time"})

    carts = events[events["event"] == "addtocart"]
    carts = carts[["visitorid", "event_time"]]
    carts = carts.merge(views, on="visitorid")
    carts = carts[carts["event_time"] >= carts["view_time"]]
    carts = carts.groupby("visitorid", as_index=False)["event_time"].min()
    carts = carts.rename(columns={"event_time": "cart_time"})

    transactions = events[events["event"] == "transaction"]
    transactions = transactions[["visitorid", "event_time"]]
    transactions = transactions.merge(carts, on="visitorid")
    transactions = transactions[
        transactions["event_time"] >= transactions["cart_time"]
    ]
    transactions = transactions.groupby("visitorid", as_index=False)["event_time"].min()
    transactions = transactions.rename(columns={"event_time": "transaction_time"})

    funnel = views.merge(carts, on="visitorid", how="left")
    funnel = funnel.merge(transactions, on="visitorid", how="left")
    return funnel


def summarize_funnel(user_funnel):
    view_users = len(user_funnel)
    cart_users = user_funnel["cart_time"].notna().sum()
    transaction_users = user_funnel["transaction_time"].notna().sum()

    return {
        "view_users": int(view_users),
        "cart_users": int(cart_users),
        "transaction_users": int(transaction_users),
        "view_to_cart": float(conversion_rate(cart_users, view_users)),
        "cart_to_transaction": float(conversion_rate(transaction_users, cart_users)),
        "view_to_transaction": float(
            conversion_rate(transaction_users, view_users)
        ),
        "lost_before_cart": int(view_users - cart_users),
        "lost_before_transaction": int(cart_users - transaction_users),
    }


def build_user_table(user_funnel):
    users = user_funnel.copy()
    users["purchased"] = users["transaction_time"].notna()
    users["is_weekend"] = users["view_time"].dt.weekday >= 5

    hours = users["view_time"].dt.hour
    users["daypart"] = pd.cut(
        hours,
        bins=[-1, 5, 11, 17, 23],
        labels=DAYPART_ORDER,
    )
    return users


def calculate_daily_metrics(events, users):
    daily = events.groupby("event_date").size().reset_index(name="events")
    active = (
        events.groupby("event_date")["visitorid"]
        .nunique()
        .reset_index(name="active_users")
    )
    daily = daily.merge(active, on="event_date")

    starters = users.copy()
    starters["event_date"] = starters["view_time"].dt.date
    new_users = starters.groupby("event_date").size().reset_index(name="new_users")
    buyers = (
        starters.groupby("event_date")["purchased"]
        .sum()
        .reset_index(name="buyers")
    )
    daily = daily.merge(new_users, on="event_date", how="left")
    daily = daily.merge(buyers, on="event_date", how="left")
    daily[["new_users", "buyers"]] = daily[["new_users", "buyers"]].fillna(0)
    daily[["new_users", "buyers"]] = daily[["new_users", "buyers"]].astype(int)
    daily["conversion"] = daily["buyers"] / daily["new_users"]
    daily["conversion"] = daily["conversion"].fillna(0)
    return daily


def group_conversion(users, group_column):
    grouped = users.groupby(group_column, observed=False)
    result = grouped.size().reset_index(name="users")
    buyers = grouped["purchased"].sum().reset_index(name="buyers")
    result = result.merge(buyers, on=group_column)
    result["buyers"] = result["buyers"].astype(int)
    result["conversion"] = result["buyers"] / result["users"]
    result["conversion"] = result["conversion"].fillna(0)
    return result


def cart_to_purchase_times(user_funnel):
    purchases = user_funnel[user_funnel["transaction_time"].notna()].copy()
    purchases["hours_to_purchase"] = (
        purchases["transaction_time"] - purchases["cart_time"]
    ).dt.total_seconds() / 3600

    median_hours = None
    within_24_hours = 0.0
    if len(purchases) > 0:
        median_hours = float(purchases["hours_to_purchase"].median())
        within_24_hours = float((purchases["hours_to_purchase"] <= 24).mean())

    return purchases, {
        "median_hours": median_hours,
        "within_24_hours": within_24_hours,
    }


def weekday_weekend_chi_square(users):
    table = pd.crosstab(users["is_weekend"], users["purchased"])
    table = table.reindex(index=[False, True], columns=[False, True], fill_value=0)
    statistic, p_value, degrees_of_freedom, expected = chi2_contingency(table)

    weekday_users = int(table.loc[False].sum())
    weekend_users = int(table.loc[True].sum())
    weekday_buyers = int(table.loc[False, True])
    weekend_buyers = int(table.loc[True, True])
    weekday_conversion = conversion_rate(weekday_buyers, weekday_users)
    weekend_conversion = conversion_rate(weekend_buyers, weekend_users)

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "degrees_of_freedom": int(degrees_of_freedom),
        "minimum_expected": float(expected.min()),
        "weekday_users": weekday_users,
        "weekday_buyers": weekday_buyers,
        "weekday_conversion": float(weekday_conversion),
        "weekend_users": weekend_users,
        "weekend_buyers": weekend_buyers,
        "weekend_conversion": float(weekend_conversion),
        "difference_percentage_points": float(
            (weekend_conversion - weekday_conversion) * 100
        ),
    }


def daypart_chi_square(users):
    table = pd.crosstab(users["daypart"], users["purchased"])
    table = table.reindex(index=DAYPART_ORDER, columns=[False, True], fill_value=0)
    statistic, p_value, degrees_of_freedom, expected = chi2_contingency(table)

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "degrees_of_freedom": int(degrees_of_freedom),
        "minimum_expected": float(expected.min()),
    }
