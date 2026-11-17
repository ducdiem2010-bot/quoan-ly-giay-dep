"""One display policy for existing naive timestamps and new timezone-aware audit entries.

SQLite database defaults (CURRENT_TIMESTAMP) are UTC; SQL Server SYSDATETIME is
local to the server. The deployment must set SQLSERVER_TIMEZONE based on its clock.
Never change or automatically rewrite legacy stored timestamps.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
from flask import current_app

VN = timezone(timedelta(hours=7), 'ICT')  # No DST; works on Windows without tzdata

def _source_zone():
    if current_app.config.get('DB_BACKEND') == 'sqlite':
        return timezone.utc
    name = current_app.config.get('SQLSERVER_TIMEZONE', 'Asia/Ho_Chi_Minh')
    if name in ('Asia/Ho_Chi_Minh', 'Asia/Saigon', 'UTC+07:00', '+07:00'):
        return VN
    if name in ('UTC', 'Etc/UTC', 'Z', '+00:00'):
        return timezone.utc
    return ZoneInfo(name)

def format_vn(value):
    if value is None or value == '':
        return '—'
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip().replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            return str(value)  # Unknown historical format: do not fabricate an hour
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_source_zone())
    return dt.astimezone(VN).strftime('%d/%m/%Y %H:%M')

_LOG = re.compile(r'^\[([^\]]+)\](.*)$')
def format_audit_log(value):
    lines = []
    for line in (value or '').splitlines():
        match = _LOG.match(line)
        if not match:
            lines.append(line)
            continue
        raw, message = match.groups()
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            lines.append(line)
            continue
        if dt.tzinfo is None:
            # Older Python datetime.now() logs have NO reliable origin timezone.
            lines.append(f'[{raw} — giờ cũ chưa xác định múi giờ]{message}')
        else:
            lines.append(f'[{dt.astimezone(VN).strftime("%d/%m/%Y %H:%M")}]' + message)
    return '\n'.join(lines)
