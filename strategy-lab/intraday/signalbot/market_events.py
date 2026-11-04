"""Source-stamped macro alerts, without a directional thesis or orders."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from . import market_context, telegram_notify

TR = ZoneInfo('Europe/Istanbul')
STATE_PATH = Path(os.environ.get('MARKET_EVENTS_STATE_PATH', '.signalbot/market_events.json'))
NEWS_FEEDS = {
    'Investing.com Forex RSS': 'https://www.investing.com/rss/news_1.rss',
    'Investing.com Ekonomik Veriler RSS': 'https://www.investing.com/rss/news_95.rss',
    'Investing.com Borsa RSS': 'https://www.investing.com/rss/news_25.rss',
    'ECB resmî duyurular': 'https://www.ecb.europa.eu/rss/press.html',
    'BoE resmî duyurular': 'https://www.bankofengland.co.uk/rss/news',
}


def _news_category(title: str) -> str | None:
    """Only direct market-wide events; a bare 'war' or 'rate' is too broad."""
    if re.search(r'\b(?:forecast|outlook|preview|could|might|may|bets|expects?|'
                 r'prediction|analysts?|strategists?|due|upcoming|scheduled|'
                 r'tomorrow|next week|ahead of|to watch|set for)\b', title, re.I):
        return None
    rules = (
        (r'\b(?:fomc|federal reserve|fed chair|jerome powell)\b', 'ABD merkez bankası açıklaması'),
        (r'\b(?:consumer price index|\bcpi\b|personal consumption expenditures|\bpce\b|inflation data)\b',
         'ABD enflasyon verisi'),
        (r'\b(?:nonfarm payrolls?|employment situation|unemployment rate|\bjolts\b)\b',
         'ABD istihdam verisi'),
        (r'\b(?:us|u\.?s\.?)\s+(?:job openings|payrolls|unemployment)\b',
         'ABD istihdam verisi'),
        (r'\b(?:ecb|european central bank)\b', 'Avrupa Merkez Bankası açıklaması'),
        (r'\b(?:boe|bank of england)\b', 'İngiltere Merkez Bankası açıklaması'),
        (r'\b(?:uk|british|britain)\b.*\b(?:inflation|consumer prices?|\bcpi\b|'
         r'payrolls?|unemployment|\bgdp\b)\b', 'İngiltere ekonomik verisi'),
        (r'\b(?:eurozone|euro area|european union)\b.*\b(?:inflation|consumer prices?|'
         r'\bcpi\b|unemployment|\bgdp\b)\b', 'Avro Bölgesi ekonomik verisi'),
        (r'\b(?:gross domestic product|\bgdp\b)\b', 'Büyüme verisi'),
        (r'\b(?:stock market crash|market-wide trading halt|circuit breaker)\b',
         'Piyasa genelinde sert hareket'),
    )
    return next((label for pattern, label in rules if re.search(pattern, title, re.I)), None)


def _category(title: str, source: str) -> str | None:
    if source == 'ECB resmî duyurular':
        if re.search(r'\b(?:monetary policy decisions|interest rates on the deposit facility)\b',
                     title, re.I):
            return 'ECB para politikası kararı'
        return None
    if source == 'BoE resmî duyurular':
        if re.search(r'\b(?:monetary policy summary|bank rate (?:maintained|increased|'
                     r'reduced|raised|cut))\b', title, re.I):
            return 'BoE faiz kararı'
        return None
    return _news_category(title)


def _calendar_label(title: str) -> str:
    rules = (
        (r'job openings and labor turnover|\bjolts\b', 'ABD açık iş pozisyonları (JOLTS)'),
        (r'employment situation|nonfarm payroll', 'ABD istihdam raporu'),
        (r'consumer price|\bcpi\b', 'ABD tüketici enflasyonu'),
        (r'personal consumption expenditures|\bpce\b', 'ABD PCE enflasyonu'),
        (r'producer price|\bppi\b', 'ABD üretici fiyatları'),
        (r'\bfomc\b|federal funds|monetary policy', 'Fed para politikası'),
        (r'gross domestic product|\bgdp\b', 'Büyüme verisi'),
        (r'retail sales', 'Perakende satışlar'),
        (r'unemployment', 'İşsizlik verisi'),
    )
    return next((label for pattern, label in rules if re.search(pattern, title, re.I)),
                'Ekonomik takvim olayı (ayrıntı kaynakta)')


def _scope(category: str) -> str:
    if category.startswith(('ECB', 'Avro')):
        return 'EURUSD (PAPER)'
    if category.startswith(('BoE', 'İngiltere')):
        return 'GBPUSD (PAPER)'
    if category.startswith('Piyasa genelinde'):
        return 'US100/NQ izlemesi'
    return 'US100, EURUSD ve GBPUSD bağlamı'


def collect_context(now: dt.datetime) -> dict:
    context = market_context.collect(now)
    # Official category feeds; labels/links only, never turn commentary into a signal.
    for source, url in NEWS_FEEDS.items():
        try:
            response = requests.get(url, timeout=8,
                                    headers={'User-Agent': 'Mozilla/5.0 (personal RSS reader)'})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for item in root.findall('.//item'):
                title = (item.findtext('title') or '').strip()
                stamp = market_context._parse_datetime(item.findtext('pubDate'))
                link = (item.findtext('link') or '').strip()
                if stamp is not None and title and link.startswith('https://') and _category(title, source):
                    context['recent_news'].append({
                        'published_utc': stamp.isoformat(), 'headline': title,
                        'source': source, 'url': link,
                    })
        except (requests.RequestException, ET.ParseError) as exc:
            print(f'Makro izleme: {source} okunamadi ({type(exc).__name__}).')
    return context


def events(context: dict, now: dt.datetime) -> list[tuple[str, str]]:
    result = []
    for item in context.get('economic_calendar', []):
        try:
            stamp = dt.datetime.fromisoformat(item['time_utc'].replace('Z', '+00:00'))
            minutes = (stamp - now).total_seconds() / 60
        except (ValueError, KeyError, TypeError):
            continue
        if not -15 <= minutes <= 60:
            continue
        title = str(item.get('event', ''))[:140]
        key = f"calendar:{stamp.isoformat()}:{title}"
        figures = ', '.join(f'{label}: {item[field]}' for field, label in
                            [('estimate', 'beklenti'), ('actual', 'gerceklesen'),
                             ('previous', 'onceki')]
                            if item.get(field) is not None)
        category = _calendar_label(title)
        text = (f"PC TAKVİMİ • RESMÎ KAYNAK\n"
                f"Saat: {stamp.astimezone(TR):%d.%m %H:%M} TR\n"
                f"Olay: {category}\n"
                f"İlgili izleme: {_scope(category)}\n"
                f"Kaynak: {', '.join(context.get('sources', [])) or 'belirtilmedi'}\n"
                f"{figures or 'Beklenti/gerceklesen bu kaynakta yok.'}\n"
                'Bu takvim bildirimi yeni setup veya LIVE sinyal değildir. '
                'Fiyat tepkisini ve mevcut kuralları ayrıca kontrol et.')
        result.append((key, text))
    for item in context.get('recent_news', []):
        try:
            stamp = dt.datetime.fromisoformat(item['published_utc'].replace('Z', '+00:00'))
            age = (now - stamp).total_seconds() / 60
        except (ValueError, KeyError, TypeError):
            continue
        if not 0 <= age <= 20:
            continue
        title = str(item.get('headline', ''))[:240]
        category = _category(title, str(item.get('source', '')))
        if category is None:
            continue
        link = str(item.get('url', ''))
        if not link.startswith('https://'):
            continue
        bucket = stamp.replace(minute=(stamp.minute // 20) * 20, second=0, microsecond=0)
        result.append((f'news:{bucket.isoformat()}:{category}',
                       f"PC HABERİ • RSS\n"
                       f"Yayın: {stamp.astimezone(TR):%d.%m %H:%M} TR\n"
                       f"Olay: {category}\n"
                       f"İlgili izleme: {_scope(category)}\n"
                       f"Kaynak: {item.get('source', 'belirtilmedi')}\n"
                       f"Ayrıntı: {link}\n"
                       'Kaynak ayrıntısını doğrula; bu yeni setup veya LIVE sinyal değildir. '
                       'PC ve Finnhub aynı olayı bildirirse tek olay say.'))
    return result


def run(*, now=None, state_path=STATE_PATH, collect=None, send=None, dry_run=False):
    now = now or dt.datetime.now(dt.timezone.utc)
    from .scan_schedule import is_open
    if not is_open(now):
        return []
    context = (collect or collect_context)(now)
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
        notified = state.get('notified', {})
        if not isinstance(notified, dict):
            notified = {}
    except (OSError, ValueError, AttributeError):
        notified = {}
    # Bounded retention, including yesterday's releases around midnight.
    cutoff = (now - dt.timedelta(days=2)).isoformat()
    notified = {key: stamp for key, stamp in notified.items()
                if isinstance(stamp, str) and stamp >= cutoff}
    messages = []
    for key, text in events(context, now):
        if key in notified:
            continue
        if dry_run:
            print(text)
        else:
            (send or telegram_notify.send)(text)
            notified[key] = now.isoformat()
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({'notified': notified}), encoding='utf-8')
        messages.append(text)
    print(f'Makro izleme: yeni olay {len(messages)}; kaynaklar {context.get("sources", [])}.')
    return messages


def main():
    parser = argparse.ArgumentParser(description='Olay varsa makro bildirimi')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
