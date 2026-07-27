import pandas as pd

from src.processing import load_events, prepare_events


def test_load_events_reads_required_columns(tmp_path):
    path = tmp_path / "events.csv"
    path.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433120400000,1,view,101,\n",
        encoding="utf-8",
    )
    events = load_events(path)
    assert list(events.columns) == [
        "timestamp",
        "visitorid",
        "event",
        "itemid",
        "transactionid",
    ]


def test_prepare_events_removes_duplicates():
    events = pd.DataFrame(
        {
            "timestamp": [1433120400000, 1433120400000],
            "visitorid": [1, 1],
            "event": ["view", "view"],
            "itemid": [101, 101],
            "transactionid": [pd.NA, pd.NA],
        }
    )
    assert len(prepare_events(events)) == 1


def test_prepare_events_converts_and_sorts_time():
    events = pd.DataFrame(
        {
            "timestamp": [1433121000000, 1433120400000],
            "visitorid": [1, 1],
            "event": ["addtocart", "view"],
            "itemid": [101, 101],
            "transactionid": [pd.NA, pd.NA],
        }
    )
    clean = prepare_events(events)
    assert pd.api.types.is_datetime64_any_dtype(clean["event_time"])
    assert clean["event_time"].is_monotonic_increasing
