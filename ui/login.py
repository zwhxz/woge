from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout)


class LoginDialog(QDialog):
    KEY = 'WOGE'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('窝哥报价系统 - 登录')
        self.setFixedSize(340, 160)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('请输入密钥：'))
        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.Password)
        self.edit.setPlaceholderText('密钥')
        self.edit.returnPressed.connect(self.check)
        lay.addWidget(self.edit)
        btn = QPushButton('登录')
        btn.setDefault(True)
        btn.clicked.connect(self.check)
        lay.addWidget(btn)

    def check(self):
        if self.edit.text().strip().upper() == self.KEY:
            self.accept()
        else:
            QMessageBox.warning(self, '登录失败', '密钥错误，请重新输入')
            self.edit.clear()
            self.edit.setFocus()
