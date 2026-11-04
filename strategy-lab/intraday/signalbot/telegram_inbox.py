"""Private Telegram commands -> existing discretionary journal; no order API."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from .. import elenenler
from ..forward_ea import diskresyoner
from . import mt5_context, telegram_notify

UTC = dt.timezone.utc
TR = ZoneInfo('Europe/Istanbul')
STATE = Path(os.environ.get('TELEGRAM_INBOX_STATE_PATH', '.signalbot/telegram_inbox.json'))
NOTES = Path(os.environ.get('TELEGRAM_DECISION_NOTES_PATH', '.signalbot/telegram_decision_notes.json'))


def _fields(text: str) -> tuple[str, dict[str, str]]:
    parts = [part.strip() for part in text.split('|')]
    command = parts[0].lstrip('/').lower().split('@')[0]
    values = {}
    for part in parts[1:]:
        key, sep, value = part.partition('=')
        if not sep or not key.strip() or not value.strip():
            raise ValueError('Alanlar ad=deger biciminde olmali')
        key = key.strip().lower()
        if key in values:
            raise ValueError('Ayni alan iki kez yazilamaz: ' + key)
        values[key] = value.strip()
    return command, values


def _required(values: dict, names: tuple[str, ...]):
    missing = [name for name in names if not values.get(name)]
    if missing:
        raise ValueError('Eksik alan: ' + ', '.join(missing))


def _float(values, key):
    try:
        value = float(values[key])
    except (KeyError, ValueError):
        raise ValueError(key + ' sayi olmali') from None
    if not 0 < value < float('inf'):
        raise ValueError(key + ' pozitif sonlu olmali')
    return value


def _balance():
    snapshot = mt5_context.load()
    if snapshot is None:
        try:
            snapshot = mt5_context.collect()
        except Exception:
            raise ValueError('MT5 bakiyesi guncel degil; aday deftere kaydedilmedi') from None
    return float(snapshot['balance'])


def _method(name: str, symbol: str) -> str:
    if name.lower().replace(' ', '_') in {'nq_orb', 'gold_orb', 'gold_ny_orb'} or name in {'NQ_ORB_STRONG_TREND', 'GOLD_NY_ORB_TREND'}:
        raise ValueError('Emekli mekanik yontem giris gerekcesi olamaz')
    if name in {'EUR_LONDON_FADE_EMA', 'GBP_LONDON_STRONG_TREND'}:
        raise ValueError('Bu mekanik yontem PAPER; canli yetkisi yok')
    if name == 'SWEEP_CORE_AVOID_MID_VWAP':
        if symbol not in {'US100', 'NASDAQ100'}:
            raise ValueError('LIVE Sweep yalniz US100/NASDAQ100 kapsami')
        return 'mevcut LIVE Sweep'
    match = next((item for item in elenenler.KATALOG if item.id == name), None)
    if match is None:
        return 'olculmemis; calistigi varsayilmaz'
    if match.statu in {'rejected', 'retired', 'standalone_rejected'}:
        raise ValueError(f'Yontem {name}: {match.statu}; tek basina giris kaydi kabul edilmedi')
    return match.statu


def process(text: str, *, update_id: int, sent_at: dt.datetime) -> str | None:
    command = text.split('|', 1)[0].strip().lstrip('/').lower().split('@')[0]
    values = {} if command == 'aday' else _fields(text)[1]
    marker = f'telegram:{update_id}'
    if command in {'yardim', 'help', 'start'}:
        return ('Bu bot ne yapıyor?\n'
                '• Yalnız yeni tarama adayı veya seçilmiş piyasa olayı varsa haber verir. '
                'Mesaj gelmemesi, piyasada fırsat olmadığı anlamına gelmez.\n'
                '• Senin işlem kararını deftere kaydeder; MT5’te emir açmaz.\n\n'
                'Mesaj başlıkları: PC HABERİ/PC TAKVİMİ = yerel RSS ve resmî takvim; '
                'BULUT HABERİ • FINNHUB = GitHub’daki ayrı olağan dışı olay kontrolü. '
                'Aynı olay iki kaynakta görünürse tek olay say.\n\n'
                'Telefonda sıra: 1) Adayı ve MT5 fiyatını kontrol et. '
                '2) Giriş, stop, hedef, en az 2 katman, tez ve tezi neyin bozacağını belirle. '
                '3) Emirden ÖNCE ADAY kaydı yap. 4) Kararı sen ver; emri MT5’te sen aç.\n\n'
                'DURUM = defter özeti. ORNEK = kayıt için kopyalanacak biçim. '
                'PAS/BEKLE/ACILDI = kayıtlı adayın sonucunu bildir. '
                'LIVE yalnız Sweep; EUR/GBP PAPER; NQ/Gold ORB emekli.')
    if command == 'ornek':
        return ('Aşağıdaki metni düzenleyip 18:15–20:00 TR arasında gönder:\n'
                'ADAY|US100|long|tetik=GIRIS_FIYATI|stop=STOP_FIYATI|hedef=HEDEF_FIYATI|'
                'katmanlar=trend,destek|yontem=SWEEP_CORE_AVOID_MID_VWAP|'
                'tez=Buraya en az 20 karakterlik kendi tezini yaz|'
                'curuten=Buraya en az 15 karakterlik çürüteni yaz\n\n'
                'Büyük harfli fiyat alanlarını gerçek MT5 seviyelerinle değiştir. '
                'long/short yönünü, seviyeleri ve tezi sen belirle. '
                'Bot ADAY #numara derse kayıt oluşur. Sonra PAS|id=1|sebep=... '
                'veya BEKLE|id=1|not=... yazabilirsin. '
                'MT5’te elle açtıysan ACILDI|id=1|giris=...|acilis=YYYY-MM-DD HH:MM yaz.')
    if command == 'durum':
        summary = diskresyoner.ozet()
        return (f"Defter: aday {summary['aday_acik']}, pas {summary['pas']}, "
                f"kapanmis {summary['n']}, ortalama R {summary['exp_R']}. "
                'Bu mesaj bir islem onerisi degildir.')
    if command == 'aday':
        local = sent_at.astimezone(TR)
        if not dt.time(18, 15) <= local.time() < dt.time(20) or local.weekday() >= 5:
            raise ValueError('Diskresyoner aday zamani 18:15-20:00 TR hafta ici')
        parts = [part.strip() for part in text.split('|')]
        if len(parts) < 3:
            raise ValueError('ADAY|sembol|yon ile basla')
        symbol, direction = parts[1].upper(), parts[2].lower()
        # The first two positional fields are intentionally parsed separately.
        fields = {}
        for part in parts[3:]:
            key, sep, value = part.partition('=')
            if not sep or not key.strip() or not value.strip():
                raise ValueError('ADAY alanlari ad=deger biciminde olmali')
            key = key.strip().lower()
            if key in fields:
                raise ValueError('Ayni alan iki kez yazilamaz')
            fields[key] = value.strip()
        _required(fields, ('tetik', 'stop', 'hedef', 'katmanlar', 'yontem', 'tez', 'curuten'))
        method_status = _method(fields['yontem'], symbol)
        existing = next((item for item in diskresyoner.yukle()
                         if marker in item.narrative), None)
        if existing:
            return f'ADAY zaten defterde: id={existing.id}. MT5 emri acilmadi.'
        record = diskresyoner.aday(symbol, direction, _float(fields, 'tetik'),
                                   _float(fields, 'stop'), fields['tez'], fields['curuten'],
                                   fields['katmanlar'],
                                   narrative=f"{marker}; yontem={fields['yontem']}; "
                                             f"telegram_saati={sent_at.isoformat()}",
                                   timeframe=fields.get('timeframe', ''),
                                   hedef=_float(fields, 'hedef'), bakiye=_balance())
        return (f"ADAY #{record.id} deftere yazildi. Yontem: {method_status}. "
                'Bu MT5 emri degildir; giris ve riski telefonda tekrar kontrol et.')
    if command in {'pas', 'bekle', 'acildi'}:
        _required(values, ('id',))
        try:
            record_id = int(values['id'])
        except ValueError:
            raise ValueError('id tam sayi olmali') from None
        if command == 'pas':
            _required(values, ('sebep',))
            if len(values['sebep'].strip()) < 5:
                raise ValueError('pas sebebi en az 5 karakter olmali')
            previous = next((item for item in diskresyoner.yukle()
                             if item.id == record_id and marker in item.pas_sebebi), None)
            if previous:
                return f'PAS #{record_id} zaten defterde.'
            record = diskresyoner.pas(record_id, values['sebep'] + ' ' + marker)
            return f'PAS #{record.id} deftere yazildi. MT5 emri degismedi.'
        if command == 'bekle':
            _required(values, ('not',))
            record = next((item for item in diskresyoner.yukle() if item.id == record_id), None)
            if record is None or record.durum != 'aday':
                raise ValueError('BEKLE icin acik aday id gerekli')
            try:
                notes = json.loads(NOTES.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                notes = {}
            notes.setdefault(str(update_id), {'id': record_id, 'not': values['not'],
                                               'telegram_utc': sent_at.isoformat()})
            _save(NOTES, notes)
            return (f'BEKLE #{record_id} notu kaydedildi; aday defterde acik kalir. '
                    'Islem acilmadi. Sonuc icin PAS veya ACILDI bildir.')
        _required(values, ('giris', 'acilis'))
        try:
            opened = dt.datetime.strptime(values['acilis'], '%Y-%m-%d %H:%M')
        except ValueError:
            raise ValueError('acilis TR saati YYYY-MM-DD HH:MM olmali') from None
        opened_utc = opened.replace(tzinfo=TR).astimezone(UTC)
        if not dt.timedelta(0) <= sent_at - opened_utc <= dt.timedelta(days=3):
            raise ValueError('acilis saati mesajdan sonra veya 3 gunden eski olamaz')
        previous = next((item for item in diskresyoner.yukle()
                         if item.id == record_id and item.durum == 'acik'), None)
        if previous and abs(previous.giris - _float(values, 'giris')) < 1e-8:
            return f'ACILDI #{record_id} zaten defterde; bot emir acmadi.'
        record = diskresyoner.tetikle(record_id, _float(values, 'giris'),
                                      acilis=opened_utc.strftime('%Y-%m-%d %H:%M:%S'))
        return (f'ACILDI #{record.id} kullanici beyanina gore deftere yazildi. '
                'Bot brokerda emir acmadi/degistirmedi.')
    return None


def _api(method: str, token: str, **kwargs):
    try:
        response = requests.post(f'https://api.telegram.org/bot{token}/{method}',
                                 json=kwargs, timeout=15)
        response.raise_for_status()
        result = response.json()
        if result.get('ok') is not True:
            raise RuntimeError('Telegram API reddetti')
        return result['result']
    except requests.RequestException:
        raise RuntimeError('Telegram HTTP hatasi; token URL gizlendi') from None


def _save(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state), encoding='utf-8')
    temporary.replace(path)


def poll(*, state_path=STATE, fetch=None, send=None, now=None):
    now = now or dt.datetime.now(UTC)
    token, owner = os.environ['TELEGRAM_BOT_TOKEN'], os.environ['TELEGRAM_CHAT_ID']
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        state = {'offset': 0, 'pending': {}}
    getter = fetch or (lambda offset: _api('getUpdates', token, offset=offset,
                                           limit=100, timeout=0,
                                           allowed_updates=['message']))
    reply = send or telegram_notify.send
    for update_id, message in list(state.get('pending', {}).items()):
        reply(message)
        del state['pending'][update_id]
        _save(state_path, state)
    updates = getter(state['offset'])
    accepted = 0
    for update in updates:
        uid = int(update['update_id'])
        if uid < state['offset']:
            continue
        msg = update.get('message') or {}
        chat = msg.get('chat') or {}
        sender = msg.get('from') or {}
        body = str(msg.get('text') or '').strip()
        output = None
        if (chat.get('type') == 'private' and str(chat.get('id')) == owner
                and str(sender.get('id')) == owner and not sender.get('is_bot')):
            sent_at = dt.datetime.fromtimestamp(int(msg.get('date', 0)), UTC)
            if 0 <= (now - sent_at).total_seconds() <= 600 and body:
                try:
                    output = process(body, update_id=uid, sent_at=sent_at)
                except (ValueError, KeyError) as exc:
                    output = 'Kayit yapilmadi: ' + str(exc)[:280]
        state['offset'] = uid + 1
        if output:
            state.setdefault('pending', {})[str(uid)] = output
            accepted += 1
        _save(state_path, state)
        if output:
            reply(output)
            del state['pending'][str(uid)]
            _save(state_path, state)
    print(f'Telegram defter koprusu: {accepted} komuta cevap, emir yok.')
    return accepted


def main():
    parser = argparse.ArgumentParser(description='Private Telegram journal inbox')
    parser.parse_args()
    poll()


if __name__ == '__main__':
    main()
