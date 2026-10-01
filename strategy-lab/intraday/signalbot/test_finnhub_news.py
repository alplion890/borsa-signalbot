import datetime as dt
import json

from . import finnhub_news

NOW = dt.datetime(2026, 9, 29, 15, 30, tzinfo=dt.timezone.utc)


def _item(title, *, minutes=0):
    return {'published': NOW - dt.timedelta(minutes=minutes), 'headline': title,
            'url': 'https://example.com/market', 'source': 'Example',
            'category': 'Piyasa genelinde işlem kesintisi / sert olay',
            'scope': 'US100/NQ'}


def test_strict_exception_filter():
    assert finnhub_news.classify('Stock market crash triggers circuit breaker')
    assert finnhub_news.classify('Emergency Fed rate decision announced')
    assert finnhub_news.classify('US job openings fall in August') is None
    assert finnhub_news.classify('Fed rate outlook could lift stocks') is None
    assert finnhub_news.classify('What to do if stock market crash triggers circuit breaker') is None


def test_separate_label_and_dedupe(monkeypatch, tmp_path):
    monkeypatch.setenv('FINNHUB_API_KEY', 'test-key')
    sent = []
    state = tmp_path / 'finnhub.json'
    fetch = lambda **kwargs: ([_item('Stock market crash triggers circuit breaker')], 200)
    first = finnhub_news.run(now=NOW, state_path=state, fetch=fetch, send=sent.append)
    second = finnhub_news.run(now=NOW, state_path=state, fetch=fetch, send=sent.append)
    assert len(first) == 1 and second == [] and len(sent) == 1
    assert sent[0].startswith('BULUT HABERİ • FINNHUB')
    assert 'Kaynağın özgün başlığı' in sent[0]
    assert 'yeni setup veya LIVE işlem sinyali değildir' in sent[0]
    assert len(json.loads(state.read_text())['sent']) == 1


def test_dry_run_and_outside_window_do_not_send(monkeypatch, tmp_path):
    monkeypatch.setenv('FINNHUB_API_KEY', 'test-key')
    state = tmp_path / 'finnhub.json'
    fail = lambda _: (_ for _ in ()).throw(AssertionError('Telegram should not send'))
    fetch = lambda **kwargs: ([_item('Stock market crash triggers circuit breaker')], 200)
    assert len(finnhub_news.run(now=NOW, state_path=state, fetch=fetch,
                                send=fail, dry_run=True)) == 1
    assert not state.exists()
    assert finnhub_news.run(now=NOW + dt.timedelta(hours=6), state_path=state,
                            fetch=lambda **kwargs: (_ for _ in ()).throw(AssertionError()),
                            send=fail) == []


def test_http_denial_does_not_send(monkeypatch, tmp_path):
    monkeypatch.setenv('FINNHUB_API_KEY', 'test-key')
    assert finnhub_news.run(now=NOW, state_path=tmp_path / 'state.json',
                            fetch=lambda **kwargs: ([], 403),
                            send=lambda _: (_ for _ in ()).throw(AssertionError())) == []


def test_manual_dry_run_checks_api_outside_window(monkeypatch, tmp_path):
    monkeypatch.setenv('FINNHUB_API_KEY', 'test-key')
    seen = []
    def fetch(**kwargs):
        seen.append(kwargs)
        return [], 200
    finnhub_news.run(now=NOW + dt.timedelta(hours=6),
                     state_path=tmp_path / 'state.json', fetch=fetch,
                     send=lambda _: (_ for _ in ()).throw(AssertionError()), dry_run=True)
    assert len(seen) == 1
