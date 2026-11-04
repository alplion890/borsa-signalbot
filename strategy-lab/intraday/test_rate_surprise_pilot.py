"""Research integrity checks, independent of downloaded price/event files."""
import pandas as pd
import pytest

from . import rate_surprise_pilot as pilot


def test_release_time_observes_us_dst():
    assert pilot.utc_event_time("2024-01-31 14:00").hour == 19
    assert pilot.utc_event_time("2024-07-31 14:00").hour == 18


def test_costs_are_explicit_price_sensitivities():
    result = pilot.trade_returns(1.25, 1.24, -1)
    assert result["gross_bps"] == pytest.approx(80)
    assert result["assumed_1pip_bps"] == pytest.approx(79.2)


def test_selection_uses_only_selection_period_and_skips_missing_bar(tmp_path, monkeypatch):
    events = pd.DataFrame({
        "date_time": ["2023-01-25 14:00", "2025-01-29 14:00", "2025-03-19 14:00"],
        "MP1": [0.1, 0.1, 0.1], "Unscheduled": [0, 0, 0],
    })
    values = {}
    for i, row in events.iterrows():
        t = pilot.utc_event_time(row.date_time)
        values[t + pd.Timedelta(minutes=30)] = 1.25
        values[t + pd.Timedelta(hours=3)] = 1.24 if i == 0 else 1.26
        values[t + pd.Timedelta(minutes=30, hours=24)] = 1.26 if i == 0 else 1.23
    # Paired exclusion: the third event's 24h bar is missing even though CLOSE exists.
    del values[pilot.utc_event_time(events.iloc[2].date_time) + pd.Timedelta(minutes=30, hours=24)]
    prices = pd.DataFrame({"open": pd.Series(values)})
    (tmp_path / "fed_usmpd.xlsx").write_bytes(b"synthetic input")
    (tmp_path / "PROTOCOL.md").write_text("synthetic protocol")
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot, "OUT", tmp_path)
    monkeypatch.setattr(pilot, "load_prices", lambda symbol: (prices, []))
    monkeypatch.setattr(pd, "read_excel", lambda *a, **kw: events)
    result = pilot.run()
    assert result["selected_hold_using_2022_2024_only"] == "CLOSE"
    holdout = [r for r in result["summary"] if r["period"] == "holdout"]
    assert {r["n_independent_events"] for r in holdout} == {1}
    assert next(r for r in holdout if r["hold"] == "CLOSE")["mean_gross_bps"] < 0
    trades = pd.read_csv(tmp_path / "pilot_trades.csv")
    assert len(trades) == 8  # Two events x two symbols x two hold variants.
    assert (pd.to_datetime(trades.entry_at) > pd.to_datetime(trades.signal_window_end)).all()
