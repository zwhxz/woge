from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QTabWidget, QWidget)

from db import get_conn
from ui.login import APP_NAME
from ui.material import MaterialWidget
from ui.quote_list import QuoteListWidget
from ui.users import UserManagerWidget


class ChangePasswordDialog(QDialog):
    def __init__(self, parent, username):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle('修改密码')
        self.setFixedSize(340, 190)
        form = QFormLayout(self)
        self.ed_old = QLineEdit()
        self.ed_old.setEchoMode(QLineEdit.Password)
        self.ed_new = QLineEdit()
        self.ed_new.setEchoMode(QLineEdit.Password)
        self.ed_new2 = QLineEdit()
        self.ed_new2.setEchoMode(QLineEdit.Password)
        form.addRow('原密码', self.ed_old)
        form.addRow('新密码', self.ed_new)
        form.addRow('确认新密码', self.ed_new2)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.do_change)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def do_change(self):
        conn = get_conn()
        user = conn.execute('SELECT * FROM users WHERE name=?', (self.username,)).fetchone()
        conn.close()
        if not user or self.ed_old.text() != (user['password'] or ''):
            QMessageBox.warning(self, '失败', '原密码错误')
            return
        new = self.ed_new.text()
        if not new:
            QMessageBox.warning(self, '失败', '新密码不能为空')
            return
        if new != self.ed_new2.text():
            QMessageBox.warning(self, '失败', '两次输入的新密码不一致')
            return
        conn = get_conn()
        conn.execute('UPDATE users SET password=? WHERE name=?', (new, self.username))
        conn.commit()
        conn.close()
        QMessageBox.information(self, '完成', '密码修改成功')
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, username=''):
        super().__init__()
        self.username = username
        self.logout_requested = False
        self.setWindowTitle(APP_NAME + (' - ' + username if username else ''))
        self.resize(1280, 800)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        self.material_page = MaterialWidget()
        self.quote_page = QuoteListWidget()
        tabs.addTab(self.quote_page, '报价单管理')
        tabs.addTab(self.material_page, '物料库管理')
        if username == 'woge':
            self.users_page = UserManagerWidget()
            tabs.addTab(self.users_page, '用户管理')

        corner = QWidget()
        corner_lay = QHBoxLayout(corner)
        corner_lay.setContentsMargins(4, 0, 4, 0)
        corner_lay.setSpacing(6)
        btn_pwd = QPushButton('修改密码')
        btn_pwd.clicked.connect(self.change_password)
        btn_logout = QPushButton('退出登录')
        btn_logout.clicked.connect(self.logout)
        corner_lay.addWidget(btn_pwd)
        corner_lay.addWidget(btn_logout)
        tabs.setCornerWidget(corner, Qt.TopRightCorner)
        lay.addWidget(tabs)
        self.setCentralWidget(central)

    def change_password(self):
        dlg = ChangePasswordDialog(self, self.username)
        dlg.exec_()

    def logout(self):
        self.logout_requested = True
        self.close()
