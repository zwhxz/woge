import datetime
import os
import sqlite3

from db import get_db_path

BACKUP_KEEP = 30


def backup_dir(db_path):
    return os.path.join(os.path.dirname(db_path), 'backups')


def backup_if_needed(force=False):
    src = get_db_path()
    if not os.path.exists(src):
        return None
    bdir = backup_dir(src)
    today = datetime.date.today().strftime('%Y%m%d')
    try:
        os.makedirs(bdir, exist_ok=True)
        existing = [f for f in os.listdir(bdir)
                    if f.startswith('woge_' + today) and f.endswith('.db')]
    except OSError:
        return None
    if existing and not force:
        return None
    dst = os.path.join(
        bdir, 'woge_{}.db'.format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
    try:
        s = sqlite3.connect(src)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()
        files = sorted(f for f in os.listdir(bdir)
                       if f.startswith('woge_') and f.endswith('.db'))
        for f in files[:-BACKUP_KEEP]:
            os.remove(os.path.join(bdir, f))
    except (OSError, sqlite3.Error):
        return None
    return dst
