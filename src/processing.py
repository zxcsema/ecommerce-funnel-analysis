from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_EVENTS_PATH = PROJECT_ROOT / "data/raw/events.csv"
EVENT_ORDER = ["view", "addtocart", "transaction"]


def load_events(file_path=None):
    path = Path(file_path) if file_path else RAW_EVENTS_PATH
    if not path.exists():
        raise FileNotFoundError(
            "Файл data/raw/events.csv не найден. "
            "Скачайте events.csv с Kaggle и поместите его в data/raw/."
        )

    return pd.read_csv(
        path,
        usecols=["timestamp", "visitorid", "event", "itemid", "transactionid"],
    )


def prepare_events(events):
    clean_events = events.drop_duplicates().copy()
    clean_events["event_time"] = pd.to_datetime(
        clean_events["timestamp"], unit="ms"
    )
    clean_events["event_date"] = clean_events["event_time"].dt.date
    clean_events = clean_events.sort_values(["visitorid", "event_time"])
    clean_events = clean_events.reset_index(drop=True)
    return clean_events


def save_bar_chart(labels, values, output_path, title, ylabel, color="#4C78A8"):
    plt.figure(figsize=(7, 4))
    bars = plt.bar(labels, values, color=color)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.bar_label(bars, fmt="%.2f" if "Конверсия" in ylabel else "%.0f")
    plt.tight_layout()
    plt.savefig(output_path, dpi=130)
    plt.close()


def save_line_chart(x, y, output_path, title, ylabel):
    plt.figure(figsize=(9, 4))
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel("Дата")
    plt.ylabel(ylabel)
    plt.xticks(rotation=35)
    plt.tight_layout()
    plt.savefig(output_path, dpi=130)
    plt.close()


def save_time_to_purchase_chart(purchases, output_path):
    limit = purchases["hours_to_purchase"].quantile(0.95)
    shown = purchases[purchases["hours_to_purchase"] <= limit]

    plt.figure(figsize=(7, 4))
    plt.hist(shown["hours_to_purchase"], bins=40, color="#E45756")
    plt.title("Время от корзины до покупки")
    plt.xlabel("Часы")
    plt.ylabel("Количество пользователей")
    plt.tight_layout()
    plt.savefig(output_path, dpi=130)
    plt.close()
