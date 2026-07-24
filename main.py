import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox

from db import data_dir, init_db
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
