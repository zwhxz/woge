from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QVBoxLayout)

from license import machine_code, save_license, verify_serial
from ui.login import APP_NAME, logo_path
from PyQt5.QtGui import QPixmap


class ActivateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME + ' - 软件激活')
        self.setFixedSize(480, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 25, 40, 25)
        lay.setSpacing(12)

        lbl_logo = QLabel()
        pm = QPixmap(logo_path())
        if not pm.isNull():
            lbl_logo.setPixmap(pm.scaledToWidth(200, Qt.SmoothTransformation))
        lbl_logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_logo)

        lay.addWidget(QLabel('首次使用需要激活。请将以下机器码发送给管理员获取序列号：'))

        self.ed_code = QLineEdit(machine_code())
        self.ed_code.setReadOnly(True)
        self.ed_code.setAlignment(Qt.AlignCenter)
        self.ed_code.setMinimumHeight(34)
        self.ed_code.setStyleSheet('font-size:16px;font-weight:bold;')
        lay.addWidget(self.ed_code)

        self.ed_serial = QLineEdit()
        self.ed_serial.setPlaceholderText('请输入序列号（XXXX-XXXX-XXXX-XXXX）')
        self.ed_serial.setAlignment(Qt.AlignCenter)
        self.ed_serial.setMinimumHeight(34)
        self.ed_serial.returnPressed.connect(self.activate)
        lay.addWidget(self.ed_serial)

        row = QHBoxLayout()
        btn = QPushButton('激  活')
        btn.setDefault(True)
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.activate)
        btn_quit = QPushButton('退  出')
        btn_quit.setMinimumHeight(38)
        btn_quit.clicked.connect(self.reject)
        row.addWidget(btn)
        row.addWidget(btn_quit)
        lay.addLayout(row)

    def activate(self):
        serial = self.ed_serial.text().strip().upper()
        if verify_serial(machine_code(), serial):
            save_license(serial)
            QMessageBox.information(self, '完成', '激活成功，欢迎使用！')
            self.accept()
        else:
            QMessageBox.warning(self, '失败', '序列号不正确，请核对后重试')
            self.ed_serial.clear()
            self.ed_serial.setFocus()
