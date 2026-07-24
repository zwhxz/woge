import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QComboBox, QDialog, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QVBoxLayout)

from db import get_conn

APP_NAME = '雪人大客户服务部客户管理系统'


def logo_path():
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        return os.path.join(base, 'logo.png')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logo.png')


class LoginDialog(QDialog):
    KEY = 'WOGE'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME + ' - 登录')
        self.setFixedSize(460, 330)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.username = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 25, 40, 25)
        lay.setSpacing(12)

        lbl_logo = QLabel()
        pm = QPixmap(logo_path())
        if not pm.isNull():
            lbl_logo.setPixmap(pm.scaledToWidth(220, Qt.SmoothTransformation))
        lbl_logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_logo)

        lbl_title = QLabel(APP_NAME)
        lbl_title.setAlignment(Qt.AlignCenter)
        f = lbl_title.font()
        f.setPointSize(16)
        f.setBold(True)
        lbl_title.setFont(f)
        lay.addWidget(lbl_title)

        conn = get_conn()
        names = [r['name'] for r in conn.execute(
            'SELECT name FROM users ORDER BY is_admin DESC, id').fetchall()]
        conn.close()
        self.cb_user = QComboBox()
        self.cb_user.setEditable(True)
        self.cb_user.addItems(names)
        self.cb_user.setMinimumHeight(34)
        lay.addWidget(self.cb_user)

        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.Password)
        self.edit.setPlaceholderText('请输入密钥')
        self.edit.setMinimumHeight(34)
        self.edit.returnPressed.connect(self.check)
        lay.addWidget(self.edit)

        btn = QPushButton('登  录')
        btn.setDefault(True)
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.check)
        lay.addWidget(btn)

    def check(self):
        name = self.cb_user.currentText().strip()
        if not name:
            QMessageBox.warning(self, '登录失败', '请输入用户名')
            return
        conn = get_conn()
        user = conn.execute('SELECT * FROM users WHERE name=?', (name,)).fetchone()
        conn.close()
        if not user:
            QMessageBox.warning(self, '登录失败', '用户不存在')
            return
        if user['disabled']:
            QMessageBox.warning(self, '登录失败', '该用户已被禁用，请联系管理员')
            return
        if self.edit.text().strip().upper() != self.KEY:
            QMessageBox.warning(self, '登录失败', '密钥错误，请重新输入')
            self.edit.clear()
            self.edit.setFocus()
            return
        self.username = name
        self.accept()
