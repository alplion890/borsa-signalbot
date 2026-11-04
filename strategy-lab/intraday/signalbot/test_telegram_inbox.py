import datetime as dt
import json

import pytest

from ..forward_ea import diskresyoner
from . import telegram_inbox

SENT = dt.datetime(2026, 9, 29, 16, 45, tzinfo=dt.timezone.utc)
ADAY = ('ADAY|US100|long|tetik=100|stop=90|hedef=120|'
        'katmanlar=trend,destek|yontem=SWEEP_CORE_AVOID_MID_VWAP|'
        'tez=Onceki seviyede yeni bir fiyat tepkisi var|'
        'curuten=Kapanmis mum seviyeyi kaybeder')


def test_help_explains_bot_before_showing_template():
    help_text = telegram_inbox.process('YARDIM', update_id=1, sent_at=SENT)
    example = telegram_inbox.process('ORNEK', update_id=2, sent_at=SENT)
    assert 'Bu bot ne yapıyor?' in help_text
    assert 'MT5’te emir açmaz' in help_text
    assert 'ADAY|US100' not in help_text
    assert 'ADAY|US100' in example
    assert 'GIRIS_FIYATI' in example


def test_candidate_records_once_and_retired_is_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(diskresyoner, 'DEFTER', tmp_path / 'trades.csv')
    monkeypatch.setattr(telegram_inbox, '_balance', lambda: 5000.0)
    first = telegram_inbox.process(ADAY, update_id=17, sent_at=SENT)
    second = telegram_inbox.process(ADAY, update_id=17, sent_at=SENT)
    assert 'ADAY #1' in first
    assert 'zaten defterde' in second
    assert len(diskresyoner.yukle()) == 1
    with pytest.raises(ValueError, match='Emekli'):
        telegram_inbox.process(ADAY.replace('SWEEP_CORE_AVOID_MID_VWAP', 'NQ_ORB_STRONG_TREND'),
                               update_id=18, sent_at=SENT)
    with pytest.raises(ValueError, match='Emekli'):
        telegram_inbox.process(ADAY.replace('SWEEP_CORE_AVOID_MID_VWAP', 'nq orb'),
                               update_id=19, sent_at=SENT)
    with pytest.raises(ValueError, match='PAPER'):
        telegram_inbox.process(ADAY.replace('SWEEP_CORE_AVOID_MID_VWAP', 'EUR_LONDON_FADE_EMA'),
                               update_id=20, sent_at=SENT)


def test_no_candidate_outside_window(monkeypatch, tmp_path):
    monkeypatch.setattr(diskresyoner, 'DEFTER', tmp_path / 'trades.csv')
    with pytest.raises(ValueError, match='18:15-20:00'):
        telegram_inbox.process(ADAY, update_id=1,
                               sent_at=SENT + dt.timedelta(hours=1))
    assert diskresyoner.yukle() == []


def test_only_private_owner_message_is_processed(monkeypatch, tmp_path):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '7')
    monkeypatch.setattr(diskresyoner, 'DEFTER', tmp_path / 'trades.csv')
    monkeypatch.setattr(telegram_inbox, '_balance', lambda: 5000.0)
    event = {'update_id': 50, 'message': {'date': int(SENT.timestamp()),
             'text': ADAY, 'chat': {'type': 'private', 'id': 7},
             'from': {'id': 8, 'is_bot': False}}}
    sent = []
    assert telegram_inbox.poll(state_path=tmp_path / 'offset.json',
                               fetch=lambda offset: [event], send=sent.append,
                               now=SENT) == 0
    assert diskresyoner.yukle() == []
    event['update_id'] = 51
    event['message']['from']['id'] = 7
    assert telegram_inbox.poll(state_path=tmp_path / 'offset.json',
                               fetch=lambda offset: [event], send=sent.append,
                               now=SENT) == 1
    assert len(diskresyoner.yukle()) == 1
    assert json.loads((tmp_path / 'offset.json').read_text())['offset'] == 52


def test_reply_failure_does_not_duplicate_trade(monkeypatch, tmp_path):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '7')
    monkeypatch.setattr(diskresyoner, 'DEFTER', tmp_path / 'trades.csv')
    monkeypatch.setattr(telegram_inbox, '_balance', lambda: 5000.0)
    event = {'update_id': 55, 'message': {'date': int(SENT.timestamp()),
             'text': ADAY, 'chat': {'type': 'private', 'id': 7},
             'from': {'id': 7, 'is_bot': False}}}
    state = tmp_path / 'offset.json'
    def fail(_):
        raise RuntimeError('delivery error')
    with pytest.raises(RuntimeError):
        telegram_inbox.poll(state_path=state, fetch=lambda _: [event],
                            send=fail, now=SENT)
    replies = []
    telegram_inbox.poll(state_path=state, fetch=lambda _: [event],
                        send=replies.append, now=SENT)
    assert len(diskresyoner.yukle()) == 1
    assert len(replies) == 1
