import datetime as dt

import pytest

from . import market_events

NOW = dt.datetime(2026, 9, 28, 15, 30, tzinfo=dt.timezone.utc)


def context():
    return {'sources': ['BLS calendar'], 'economic_calendar': [
        {'time_utc': NOW.isoformat(), 'event': 'Employment Situation'},
        {'time_utc': (NOW + dt.timedelta(hours=5)).isoformat(), 'event': 'Later'}
    ], 'recent_news': [
        {'published_utc': (NOW - dt.timedelta(days=1)).isoformat(), 'headline': 'Old'},
        {'published_utc': (NOW + dt.timedelta(minutes=1)).isoformat(), 'headline': 'Future'}
    ]}


def test_only_nearby_events_without_old_or_future_news():
    result = market_events.events(context(), NOW)
    assert len(result) == 1
    assert 'Beklenti/gerceklesen bu kaynakta yok' in result[0][1]
    assert 'PC TAKVİMİ' in result[0][1]
    assert 'LIVE sinyal değildir' in result[0][1]


def test_success_dedupes_and_failure_can_retry(tmp_path):
    state = tmp_path / 'events.json'
    def fail(text):
        raise RuntimeError('failed')
    with pytest.raises(RuntimeError):
        market_events.run(now=NOW, state_path=state, collect=lambda _: context(), send=fail)
    assert not state.exists()
    sent = []
    kwargs = dict(now=NOW, state_path=state, collect=lambda _: context(), send=sent.append)
    assert len(market_events.run(**kwargs)) == 1
    assert market_events.run(**kwargs) == []
    assert len(sent) == 1


def test_outside_window_does_not_fetch(tmp_path):
    assert market_events.run(now=NOW - dt.timedelta(hours=10), state_path=tmp_path / 'x',
                             collect=lambda _: pytest.fail('unexpected fetch')) == []


def test_london_window_and_uk_macro_label(tmp_path):
    london = dt.datetime(2026, 9, 30, 8, 0, tzinfo=dt.timezone.utc)  # 11:00 TR
    data = {'sources': [], 'economic_calendar': [], 'recent_news': [
        {'published_utc': london.isoformat(), 'headline': 'UK inflation rises in August',
         'source': 'Investing.com Forex RSS', 'url': 'https://www.investing.com/news/forex-news/uk-cpi'},
    ]}
    sent = []
    market_events.run(now=london, state_path=tmp_path / 'london.json',
                      collect=lambda _: data, send=sent.append)
    assert len(sent) == 1
    assert 'İngiltere ekonomik verisi' in sent[0]
    assert 'LIVE sinyal' in sent[0]


def test_trade_war_headline_is_not_a_market_alert():
    data = {'sources': ['BBC Business RSS'], 'economic_calendar': [], 'recent_news': [
        {'published_utc': NOW.isoformat(),
         'headline': 'US ban on Canadian alcohol and dairy takes effect as trade war drags on',
         'source': 'BBC Business RSS', 'url': 'https://example.com/story'},
        {'published_utc': NOW.isoformat(),
         'headline': 'US stock market crash triggers circuit breaker',
         'source': 'BBC Business RSS', 'url': 'https://example.com/market'},
    ]}
    result = market_events.events(data, NOW)
    assert len(result) == 1
    assert 'Piyasa genelinde sert hareket' in result[0][1]
    assert 'stock market crash' not in result[0][1]
    assert 'PC HABERİ • RSS' in result[0][1]


def test_collect_uses_trading_rss_and_excludes_opinion(monkeypatch):
    import requests
    from . import market_context

    xml = b'''<rss><channel>
      <item><title>US job openings fall in August</title>
        <pubDate>2026-09-29 14:30:34</pubDate>
        <link>https://www.investing.com/news/economic-indicators/job-openings</link></item>
      <item><title>Fed rate outlook could lift stocks</title>
        <pubDate>2026-09-29 14:30:34</pubDate>
        <link>https://www.investing.com/news/forex-news/outlook</link></item>
    </channel></rss>'''

    class Response:
        content = xml

        def raise_for_status(self):
            pass

    called = []
    def get(url, **kwargs):
        called.append(url)
        return Response()

    monkeypatch.setattr(market_context, 'collect',
                        lambda _: {'economic_calendar': [], 'recent_news': [], 'sources': []})
    monkeypatch.setattr(requests, 'get', get)
    result = market_events.collect_context(NOW)
    assert len(called) == 5
    assert len(result['recent_news']) == 3
    assert all(item['headline'] == 'US job openings fall in August'
               for item in result['recent_news'])


def test_official_central_bank_feed_excludes_unrelated_notice():
    assert market_events._category('ECB amends monetary policy implementation guidelines',
                                   'ECB resmî duyurular') is None
    assert market_events._category('Monetary policy decisions',
                                   'ECB resmî duyurular') == 'ECB para politikası kararı'
    assert market_events._category('Bank of England announces new office space',
                                   'BoE resmî duyurular') is None
    assert market_events._category('Bank Rate maintained at 3.75%',
                                   'BoE resmî duyurular') == 'BoE faiz kararı'


def test_future_release_preview_is_not_treated_as_released_data():
    assert market_events._news_category(
        'ADP jobs data, GDP, core PCE, and oil inventories due Wednesday') is None
