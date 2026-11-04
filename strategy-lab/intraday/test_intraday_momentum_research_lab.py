"""Literatur tabanli seans momentum testinin zaman kontrolleri."""
import pandas as pd

from .intraday_momentum_research_lab import SESSIONS, VARIANTS, session_observations


def test_search_space_is_four_variants_per_asset():
    assert len(SESSIONS) == 4
    assert len(VARIANTS) == 4


def test_nq_session_tracks_new_york_dst():
    # Yaz saatinde NY 09:30 = 13:30 UTC.
    pieces = [pd.date_range(day + pd.Timedelta(hours=13, minutes=30),
                            day + pd.Timedelta(hours=20), freq="5min")
              for day in pd.date_range("2026-05-01", periods=25, freq="B")]
    idx = pieces[0].append(pieces[1:])
    frame = pd.DataFrame({"open": 1.0, "high": 1.1, "low": 0.9,
                          "close": 1.0, "volume": 1.0}, index=idx)
    out = session_observations(frame, SESSIONS["NQ"])
    assert not out.empty
    assert (out.index.hour == 19).all()
    assert (out.index.minute == 30).all()
