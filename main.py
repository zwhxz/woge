import os
import sys
import traceback

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from backup import backup_if_needed
from db import data_dir, init_db
from license import is_activated
from ui.activate import ActivateDialog
from ui.login import LoginDialog
from ui.main_window import MainWindow

LOG_PATH = os.path.join(data_dir(), 'error.log')


def log_error(msg):
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(msg + '\n' + '-' * 60 + '\n')
    except OSError:
        pass


def show_error(msg):
    log_error(msg)
    QMessageBox.critical(None, '程序错误',
                         '操作出错，详情请查看 error.log\n\n' + msg.strip().split('\n')[-1])


class SafeApplication(QApplication):
    def notify(self, obj, event):
        try:
            return super().notify(obj, event)
        except Exception:
            show_error(traceback.format_exc())
            return False


def excepthook(exc_type, exc_value, exc_tb):
    show_error(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))


def main():
    sys.excepthook = excepthook
    init_db()
    app = SafeApplication(sys.argv)
    if not is_activated():
        dlg = ActivateDialog()
        if dlg.exec_() != ActivateDialog.Accepted:
            return 0
    backup_if_needed()
    timer = QTimer()
    timer.setInterval(30 * 60 * 1000)
    timer.timeout.connect(backup_if_needed)
    timer.start()
    while True:
        login = LoginDialog()
        if login.exec_() != LoginDialog.Accepted:
            return 0
        win = MainWindow(login.username)
        win.show()
        app.exec_()
        if not win.logout_requested:
            return 0


if __name__ == '__main__':
    sys.exit(main())
