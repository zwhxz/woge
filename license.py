import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import uuid

from db import data_dir

_KEY = b'WOGE-SN-2026-XRM'
LICENSE_FILE = os.path.join(data_dir(), 'license.key')


def _machine_guid():
    if sys.platform == 'win32':
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SOFTWARE\Microsoft\Cryptography')
            return winreg.QueryValueEx(k, 'MachineGuid')[0]
        except Exception:
            return ''
    if sys.platform == 'darwin':
        try:
            out = subprocess.check_output(
                ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                stderr=subprocess.DEVNULL).decode()
            m = re.search(r'"IOPlatformUUID" = "([^"]+)"', out)
            if m:
                return m.group(1)
        except Exception:
            return ''
    try:
        with open('/etc/machine-id') as f:
            return f.read().strip()
    except Exception:
        return ''


def _group(s):
    return '-'.join(s[i:i + 4] for i in range(0, len(s), 4))


def _norm(s):
    return (s or '').replace('-', '').replace(' ', '').upper()


def machine_code():
    raw = _machine_guid() + '|' + str(uuid.getnode())
    h = hashlib.sha256(raw.encode()).hexdigest().upper()
    return _group(h[:16])


def make_serial(code):
    digest = hmac.new(_KEY, _norm(code).encode(), hashlib.sha256).hexdigest().upper()
    return _group(digest[:16])


def verify_serial(code, serial):
    return _norm(serial) == _norm(make_serial(code))


def is_activated():
    try:
        with open(LICENSE_FILE, 'r', encoding='utf-8') as f:
            info = json.load(f)
    except (OSError, ValueError):
        return False
    if info.get('machine_code') != machine_code():
        return False
    return verify_serial(info.get('machine_code', ''), info.get('serial', ''))


def save_license(serial):
    with open(LICENSE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'machine_code': machine_code(), 'serial': serial}, f)
