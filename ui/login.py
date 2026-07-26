import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QVBoxLayout)

from db import get_conn
from license import is_activated, machine_code, save_license, verify_serial

APP_NAME = '雪人大客户服务部客户管理系统'


def logo_path():
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        return os.path.join(base, 'logo.png')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logo.png')


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME + ' - 登录')
        self.setFixedSize(460, 460)
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

        self.need_serial = not is_activated()
        self.lbl_code = QLabel('本机机器码（请发送给管理员获取激活码）：')
        self.ed_code = QLineEdit(machine_code())
        self.ed_code.setReadOnly(True)
        self.ed_code.setAlignment(Qt.AlignCenter)
        self.ed_code.setMinimumHeight(32)
        self.ed_serial = QLineEdit()
        self.ed_serial.setPlaceholderText('请输入激活码（XXXX-XXXX-XXXX-XXXX）')
        self.ed_serial.setAlignment(Qt.AlignCenter)
        self.ed_serial.setMinimumHeight(34)
        self.lbl_serial_tip = QLabel('')
        for w in [self.lbl_code, self.ed_code, self.ed_serial]:
            lay.addWidget(w)
        if not self.need_serial:
            for w in [self.lbl_code, self.ed_code, self.ed_serial]:
                w.hide()

        conn = get_conn()
        names = [r['name'] for r in conn.execute(
            'SELECT name FROM users ORDER BY is_admin DESC, id').fetchall()]
        conn.close()
        self.cb_user = QComboBox()
        self.cb_user.setEditable(True)
        self.cb_user.addItems(names)
        self.cb_user.setCurrentIndex(-1)
        self.cb_user.lineEdit().setPlaceholderText('请输入用户名')
        self.cb_user.setMinimumHeight(34)
        lay.addWidget(self.cb_user)

        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.Password)
        self.edit.setPlaceholderText('请输入密码')
        self.edit.setMinimumHeight(34)
        self.edit.returnPressed.connect(self.check)
        lay.addWidget(self.edit)

        self.cb_admin = QCheckBox('超管登录（免激活码）')
        self.cb_admin.toggled.connect(self._toggle_admin)
        lay.addWidget(self.cb_admin)

        btn = QPushButton('登  录')
        btn.setDefault(True)
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.check)
        lay.addWidget(btn)

    def _toggle_admin(self, checked):
        if self.need_serial:
            for w in [self.lbl_code, self.ed_code, self.ed_serial]:
                w.setVisible(not checked)

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
        if self.cb_admin.isChecked():
            if not user['is_admin']:
                QMessageBox.warning(self, '登录失败', '该用户不是超管账号')
                return
        elif self.need_serial:
            serial = self.ed_serial.text().strip().upper()
            if not verify_serial(machine_code(), serial):
                QMessageBox.warning(self, '登录失败', '激活码不正确，请核对后重试')
                self.ed_serial.clear()
                self.ed_serial.setFocus()
                return
            save_license(serial)
            self.need_serial = False
        if self.edit.text() != (user['password'] or ''):
            QMessageBox.warning(self, '登录失败', '密码错误，请重新输入')
            self.edit.clear()
            self.edit.setFocus()
            return
        self.username = name
        self.accept()
