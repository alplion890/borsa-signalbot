"""Cloud-only Finnhub exceptional-news watch; never a trading signal."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from . import telegram_notify

UTC = dt.timezone.utc
TR = ZoneInfo('Europe/Istanbul')
URL = 'https://finnhub.io/api/v1/news'
STATE = Path(os.environ.get('FINNHUB_NEWS_STATE_PATH', '.signalbot/finnhub_news.json'))


def classify(headline: str) -> tuple[str, str] | None:
    title = headline.lower()
    if re.search(r'\b(?:stock market crash|market-wide trading halt|circuit breaker|'
                 r'nasdaq trading halt|s&p 500 trading halt)\b', title):
        return 'Piyasa genelinde işlem kesintisi / sert olay', 'US100/NQ'
    if re.search(r'\b(?:emergency|unscheduled)\b', title) and re.search(
            r'\b(?:fed|fomc|federal reserve|ecb|european central bank|'
            r'boe|bank of england)\b', title) and re.search(
            r'\b(?:rate|monetary policy|meeting|decision)\b', title):
        return 'Plan dışı merkez bankası duyurusu', 'US100, EURUSD veya GBPUSD'
    return None


def collect(*, token: str, now: dt.datetime) -> tuple[list[dict], int | None]:
    try:
        response = requests.get(URL, params={'category': 'general', 'token': token},
                                timeout=12)
        if response.status_code != 200:
            return [], response.status_code
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        print(f'Finnhub haber erişimi başarısız: {type(exc).__name__}; URL/token gizlendi.')
        return [], None
    if not isinstance(payload, list):
        print('Finnhub haber API: beklenen haber listesi gelmedi; içerik gizlendi.')
        return [], 502
    print(f'Finnhub haber API: {len(payload)} ham başlık alındı.')
    result = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            stamp = dt.datetime.fromtimestamp(int(item['datetime']), UTC)
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        age = (now - stamp).total_seconds() / 60
        title = str(item.get('headline') or '').strip()
        link = str(item.get('url') or '').strip()
        category = classify(title)
        if not 0 <= age <= 20 or not title or not link.startswith('https://') or category is None:
            continue
        result.append({'published': stamp, 'headline': title[:220], 'url': link,
                       'source': str(item.get('source') or 'Finnhub')[:60],
                       'category': category[0], 'scope': category[1]})
    return sorted(result, key=lambda x: x['published']), 200


def format_message(item: dict) -> str:
    stamp = item['published'].astimezone(TR)
    return (f"BULUT HABERİ • FINNHUB\n"
            f"Yayın: {stamp:%d.%m %H:%M} TR\n"
            f"Olay: {item['category']}\n"
            f"İlgili izleme: {item['scope']}\n"
            f"Kaynağın özgün başlığı: {item['headline']}\n"
            f"Kaynak: {item['source']} | {item['url']}\n"
            "Bu haber yeni setup veya LIVE işlem sinyali değildir. "
            "MT5 fiyatını ve mevcut kuralları ayrıca kontrol et. "
            "PC'den gelen aynı olay ayrı fırsat sayılmaz.")


def run(*, now: dt.datetime | None = None, state_path: Path = STATE,
        fetch=None, send=None, dry_run: bool = False) -> list[str]:
    now = now or dt.datetime.now(UTC)
    local = now.astimezone(TR)
    in_window = local.weekday() < 5 and (
            dt.time(10) <= local.time() < dt.time(14)
            or dt.time(16) <= local.time() < dt.time(20))
    if not in_window and not dry_run:
        print('Finnhub bulut haberi: seans penceresi dışında.')
        return []
    token = os.environ.get('FINNHUB_API_KEY', '')
    if not token:
        print('Finnhub bulut haberi: anahtar yok; haber gönderilmedi.')
        return []
    items, status = (fetch or collect)(token=token, now=now)
    if status != 200:
        print(f'Finnhub bulut haberi: HTTP {status}; haber gönderilmedi.')
        return []
    try:
        sent = json.loads(state_path.read_text(encoding='utf-8')).get('sent', {})
        if not isinstance(sent, dict):
            sent = {}
    except (OSError, ValueError, AttributeError):
        sent = {}
    cutoff = (now - dt.timedelta(days=2)).isoformat()
    sent = {key: value for key, value in sent.items()
            if isinstance(value, str) and value >= cutoff}
    messages = []
    for item in items:
        bucket = item['published'].replace(minute=(item['published'].minute // 20) * 20,
                                           second=0, microsecond=0)
        key = f"{bucket.isoformat()}:{item['category']}"
        if key in sent:
            continue
        message = format_message(item)
        if dry_run:
            print(message)
        else:
            (send or telegram_notify.send)(message)
            sent[key] = now.isoformat()
            state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = state_path.with_suffix('.tmp')
            temporary.write_text(json.dumps({'sent': sent}, ensure_ascii=False), encoding='utf-8')
            temporary.replace(state_path)
        messages.append(message)
    print(f'Finnhub bulut haberi: uygun yeni olay {len(messages)}, ham aday {len(items)}.')
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
